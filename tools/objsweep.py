"""Find OBJ blocks the linear-tile sweep (gfxsweep.py) can't show: packed blocks followed by sprite-frame records
(issue #1: the big クリティカル!! / ミス popup 4F65B0 reads as noise when its 32x16 OBJs are drawn tile by tile).

    python -X utf8 tools/objsweep.py [--out work/objsweep]   -> one PNG per block: every frame assembled

Frame record (part records after block 4F65B0, read by the OAM writer 0x08011556): u32 part count, then per part
u16 attr (shape << 8 | size << 10, flip bits 12-13), u16 tile, s16 x, s16 y. A run of >= 2 frames that parses with
sane values within 0x400 bytes after a packed block's end is taken as that block's frames.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import packed  # noqa: E402

DIMS = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64), (1, 0): (16, 8), (1, 1): (32, 8),
        (1, 2): (32, 16), (1, 3): (64, 32), (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}


def frame_at(rom, p, ntiles):
    if p + 4 > len(rom):
        return None
    n = struct.unpack_from("<I", rom, p)[0]
    if not 1 <= n <= 16 or p + 4 + 8 * n > len(rom):
        return None
    parts = []
    for k in range(n):
        attr, tile, x, y = struct.unpack_from("<HHhh", rom, p + 4 + 8 * k)
        shape, size = attr >> 8 & 3, attr >> 10 & 3
        if attr & 0xC0FF or shape == 3 or not (-128 <= x <= 128 and -128 <= y <= 128):
            return None
        w, h = DIMS[(shape, size)]
        if tile + w * h // 64 > ntiles:
            return None
        parts.append((w, h, tile, x, y, attr >> 12 & 3))
    return parts, p + 4 + 8 * n


def frames_after(rom, start, ntiles):
    for p in range(start, start + 0x400, 4):
        out, q = [], p
        while (f := frame_at(rom, q, ntiles)) is not None:
            out.append(f[0])
            q = f[1]
        if len(out) >= 2:
            return p, out
    return None, []


def render(raw, frames, path):
    from PIL import Image
    tiles = [raw[i:i + 32] for i in range(0, len(raw) - 31, 32)]
    cells = []
    for parts in frames:
        xs = [x for _, _, _, x, _, _ in parts] + [x + w for w, _, _, x, _, _ in parts]
        ys = [y for _, _, _, _, y, _ in parts] + [y + h for _, h, _, _, y, _ in parts]
        x0, y0 = min(xs), min(ys)
        im = Image.new("L", (max(xs) - x0, max(ys) - y0), 24)
        for w, h, t0, x, y, flip in parts:
            for ty in range(h // 8):
                for tx in range(w // 8):
                    t = tiles[t0 + ty * (w // 8) + tx]
                    for yy in range(8):
                        for xx in range(8):
                            v = t[yy * 4 + xx // 2] >> (xx & 1) * 4 & 15
                            if v:
                                px, py = tx * 8 + xx, ty * 8 + yy
                                if flip & 1:
                                    px = w - 1 - px
                                if flip & 2:
                                    py = h - 1 - py
                                im.putpixel((x - x0 + px, y - y0 + py), 60 + v * 12)
        cells.append(im)
    W = sum(c.width for c in cells) + 4 * len(cells)
    H = max(c.height for c in cells)
    sheet = Image.new("L", (min(W, 1200), H * (W // 1200 + 1) + 4), 0)
    x = y = 0
    for c in cells:
        if x + c.width > sheet.width:
            x, y = 0, y + H + 4
        if y + c.height <= sheet.height:
            sheet.paste(c, (x, y))
        x += c.width + 4
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "work" / "objsweep"))
    ap.add_argument("--rom", help="ROM to read (default: the original in rom/; a build to check redraws)")
    ap.add_argument("--only", help="comma-separated block offsets (hex)")
    a = ap.parse_args()
    rom = Path(a.rom).read_bytes() if a.rom else next((ROOT / "rom").glob("*.gba")).read_bytes()
    only = {int(x, 16) for x in a.only.split(",")} if a.only else None
    blocks = json.loads((ROOT / "work" / "packed_blocks.json").read_text())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    hits = 0
    for off, typ, rawlen, packlen, *_ in blocks:
        if rawlen < 64 or rawlen % 32 or (only and off not in only):
            continue
        p, frames = frames_after(rom, (off + packlen + 3) & ~3, rawlen // 32)
        if not frames:
            continue
        try:
            raw = packed.unpack(rom, off)[1]
        except Exception:
            continue
        hits += 1
        multi = max(len(f) for f in frames)
        print(f"{off:06X}\ttype {typ}\t{rawlen // 32} tiles\tframes {len(frames)} at {p:06X}\tmax parts {multi}")
        render(raw, frames, out / f"{off:06X}.png")
    print(f"{hits} blocks with frame records -> {out}")


if __name__ == "__main__":
    main()
