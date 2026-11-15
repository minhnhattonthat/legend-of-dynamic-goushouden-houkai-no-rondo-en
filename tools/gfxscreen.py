"""Compose a GBA screen from a ppudump (tools/ppuscene.py) with each pixel's source, for graphics-text redraws.

    python -X utf8 tools/gfxscreen.py PREFIX [--out PNG] [--layers]    render (and per-layer renders) to check

compose(prefix) -> Screen: .rgb[y][x], .src[y][x] = (layer, vram byte addr, high nibble?, palette bank, index) of
the visible pixel (None = backdrop). Text-mode BGs (mode 0/1 BG0-2 text, regular OBJs) only; no affine, windows or
blending. The io dump's scroll registers are write-only on hardware: they read as 0, so scrolled BGs come out
unscrolled (menus don't scroll).
"""
import argparse
import struct
from pathlib import Path

OBJ_SIZES = {0: [(8, 8), (16, 16), (32, 32), (64, 64)], 1: [(16, 8), (32, 8), (32, 16), (64, 32)],
             2: [(8, 16), (8, 32), (16, 32), (32, 64)]}


class Screen:
    def __init__(self, prefix, bgs=True, objs=True):
        p = Path(prefix)
        self.bgs, self.objs = bgs, objs
        self.vram = p.with_suffix(".vram.bin").read_bytes()
        self.pal = p.with_suffix(".pal.bin").read_bytes()
        self.oam = p.with_suffix(".oam.bin").read_bytes()
        self.io = p.with_suffix(".io.bin").read_bytes()
        self.rgb = [[self.color(0, 0)] * 240 for _ in range(160)]
        self.src = [[None] * 240 for _ in range(160)]
        self.prio = [[(9, 9)] * 240 for _ in range(160)]
        self.compose()

    def recompose(self, vram):
        self.vram = bytes(vram)
        self.rgb = [[self.color(0, 0)] * 240 for _ in range(160)]
        self.src = [[None] * 240 for _ in range(160)]
        self.prio = [[(9, 9)] * 240 for _ in range(160)]
        self.compose()

    def color(self, bank, i, obj=False):
        c = struct.unpack_from("<H", self.pal, (0x200 if obj else 0) + 2 * (bank * 16 + i))[0]
        return ((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31)

    def u16(self, off):
        return struct.unpack_from("<H", self.io, off)[0]

    def put(self, x, y, key, layer, addr, hi, bank, i, obj=False):
        if 0 <= x < 240 and 0 <= y < 160 and key < self.prio[y][x]:
            self.prio[y][x] = key
            self.rgb[y][x] = self.color(bank, i, obj)
            self.src[y][x] = (layer, addr, hi, bank, i)

    def pixel4(self, base, tile, px, py):
        addr = base + tile * 32 + py * 4 + px // 2
        b = self.vram[addr] if addr < len(self.vram) else 0
        return addr, bool(px & 1), (b >> 4) if px & 1 else (b & 15)

    def compose(self):
        dispcnt = self.u16(0)
        mode = dispcnt & 7
        for n in range(4):
            if not self.bgs or not dispcnt >> (8 + n) & 1 or mode > 1 or (mode == 1 and n > 2):
                continue
            cnt = self.u16(8 + 2 * n)
            pr, cbase, sbase, size = cnt & 3, (cnt >> 2 & 3) * 0x4000, (cnt >> 8 & 31) * 0x800, cnt >> 14
            if cnt >> 7 & 1:
                continue  # 8bpp BG: not handled
            hx, vy = 0, 0  # scroll registers are write-only: the dump reads open bus there
            wt, ht = (32, 32) if size == 0 else (64, 32) if size == 1 else (32, 64) if size == 2 else (64, 64)
            for y in range(160):
                for x in range(240):
                    mx, my = (x + hx) % (wt * 8), (y + vy) % (ht * 8)
                    tx, ty = mx // 8, my // 8
                    blk = (tx // 32) + (ty // 32) * (2 if wt == 64 else 1)
                    e = struct.unpack_from("<H", self.vram, sbase + blk * 0x800 + 2 * ((ty % 32) * 32 + tx % 32))[0]
                    t, hf, vf, bank = e & 0x3FF, e >> 10 & 1, e >> 11 & 1, e >> 12
                    px, py = mx % 8, my % 8
                    px, py = (7 - px if hf else px), (7 - py if vf else py)
                    addr, hi, i = self.pixel4(cbase, t, px, py)
                    if i:
                        self.put(x, y, (pr, 1, n), f"bg{n}", addr, hi, bank, i)
        if not self.objs or not dispcnt >> 12 & 1:
            return
        one_d = dispcnt >> 6 & 1
        for k in range(128):  # the priority key (prio, 0, k) makes the lower OAM index win
            a0, a1, a2 = struct.unpack_from("<HHH", self.oam, 8 * k)
            if a0 >> 8 & 1 or a0 >> 9 & 1 or (a0 >> 10 & 3) == 2:  # affine / hidden / window obj: skip
                continue
            if a0 >> 13 & 1:
                continue  # 8bpp obj: not handled
            shape, sz = a0 >> 14, a1 >> 14
            if shape == 3:
                continue
            w, h = OBJ_SIZES[shape][sz]
            y0, x0 = a0 & 255, a1 & 511
            y0 = y0 - 256 if y0 >= 160 else y0
            x0 = x0 - 512 if x0 >= 240 else x0
            hf, vf = a1 >> 12 & 1, a1 >> 13 & 1
            tile0, pr, bank = a2 & 0x3FF, a2 >> 10 & 3, a2 >> 12
            for yy in range(h):
                for xx in range(w):
                    sx, sy = (w - 1 - xx if hf else xx), (h - 1 - yy if vf else yy)
                    tx, ty = sx // 8, sy // 8
                    t = tile0 + (ty * (w // 8) + tx if one_d else ty * 32 + tx)
                    addr, hi, i = self.pixel4(0x10000, t & 0x3FF, sx % 8, sy % 8)
                    if i:
                        self.put(x0 + xx, y0 + yy, (pr, 0, k), f"obj{k}", addr, hi, bank, i, obj=True)

    def image(self, scale=1):
        from PIL import Image
        im = Image.new("RGB", (240, 160))
        im.putdata([c for row in self.rgb for c in row])
        return im.resize((240 * scale, 160 * scale), Image.NEAREST) if scale > 1 else im


def compose(prefix, bgs=True, objs=True):
    return Screen(prefix, bgs, objs)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prefix")
    ap.add_argument("--out")
    a = ap.parse_args()
    s = compose(a.prefix)
    out = a.out or str(Path(a.prefix).with_suffix(".compose.png"))
    s.image().save(out)
    print(out)


if __name__ == "__main__":
    main()
