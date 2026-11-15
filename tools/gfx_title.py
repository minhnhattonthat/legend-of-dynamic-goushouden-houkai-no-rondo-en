"""Title screen graphics text (docs/re/graphics.md G1): redraw the English lettering into the BG3 tile block.

    python -X utf8 tools/gfx_title.py info          index/palette histogram per rect (to pick ink indices)
    python -X utf8 tools/gfx_title.py draw          writes work/gfx/title/{orig,en}.png and gfx/title_2FAD2C.bin

The title picture is BG3 (BGCNT 0x1F03: map 0xF800, char base 0, 4bpp), tiles from packed block 0x2FAD2C (lh5,
17,600 bytes) loaded at VRAM 0x1D20. The screen is rebuilt from a VRAM dump of the original title
(work/qa/p8_title_jp, scene retail_title + ppudump.lua), edited per rect, and the changed pixels are written back
into the block's own tiles. A tile used at more than one map cell must not change: the script refuses that.
It writes gfx/title_2FAD2C.diff (changed bytes only; the repo holds no game art); build.py applies it to the ROM's
block and repacks it as lh5 in place (it must fit the original 10,284-byte slot). Fonts: fonts/ (docs/fonts.md).
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402
import packed  # noqa: E402

DUMP = ROOT / "work" / "qa" / "p8_title_jp" / "ppu_001499"
BLOCK, LOAD = 0x2FAD2C, 0x1D20
MAP = 0xF800
OUT = ROOT / "work" / "gfx" / "title"
BIN = ROOT / "gfx" / "title_2FAD2C.diff"
FONTS = ROOT / "fonts"

# (name, clear rect x, y, w, h (screen px), text, font file, px size, fill idx, outline idx, anchor x, baseline y)
ROWS = [
    ("kana", (5, 9, 108, 14), "LEGEND OF DYNAMIC", "Silkscreen-Regular.ttf", 8, None, None, 8, 10),
    ("ruby", (140, 41, 96, 11), "HOUKAI NO RONDO", "Silkscreen-Regular.ttf", 8, None, None, 143, 42),
    ("main", (131, 52, 108, 21), "Rondo of Ruin", "Cinzel[wght].ttf", 12, None, None, 135, 57),
]


def load():
    vram = (DUMP.with_suffix(".vram.bin")).read_bytes()
    pal = (DUMP.with_suffix(".pal.bin")).read_bytes()
    cells = {}
    idx = [[0] * 256 for _ in range(256)]
    bank = [[0] * 256 for _ in range(256)]
    for ty in range(32):
        for tx in range(32):
            e = struct.unpack_from("<H", vram, MAP + 2 * (ty * 32 + tx))[0]
            t, hf, vf, pb = e & 0x3FF, e >> 10 & 1, e >> 11 & 1, e >> 12
            cells[(tx, ty)] = (t, hf, vf, pb)
            for y in range(8):
                for x in range(8):
                    sx, sy = (7 - x if hf else x), (7 - y if vf else y)
                    b = vram[t * 32 + sy * 4 + sx // 2]
                    idx[ty * 8 + y][tx * 8 + x] = (b >> 4) if sx & 1 else (b & 15)
                    bank[ty * 8 + y][tx * 8 + x] = pb
    return vram, pal, cells, idx, bank


def rgb(pal, pb, i):
    c = struct.unpack_from("<H", pal, 2 * (pb * 16 + i))[0]
    return ((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31)


def info():
    _, pal, cells, idx, bank = load()
    from collections import Counter
    for name, (x0, y0, w, h), *_ in ROWS:
        c = Counter((bank[y][x], idx[y][x]) for y in range(y0, y0 + h) for x in range(x0, x0 + w))
        print(name, [(f"p{pb}i{i}", n, rgb(pal, pb, i)) for (pb, i), n in c.most_common(12)])
        use = Counter(cells.values())
        tiles = {cells[(x // 8, y // 8)] for y in range(y0, y0 + h) for x in range(x0, x0 + w)}
        shared = [t for t in tiles if sum(1 for v in cells.values() if v[0] == t[0]) > 1]
        print("  tiles", len(tiles), "shared", [hex(t[0]) for t in shared], use.most_common(1))


# Sky, ring and star indices per sub-palette (kept); every other index in a rect is lettering (cleared).
SKY = {6: {1, 2, 3, 4}, 8: {1, 2, 3, 4, 5, 7, 8, 9, 10}, 9: {1, 2, 3}, 10: {1, 2}, 11: {1, 2, 4}}
# Inks as RGB: each pixel takes the nearest colour of its own tile's sub-palette (fill, outline, outer outline).
INK = {"kana": ((255, 255, 255), (213, 0, 0), None),
       "ruby": ((222, 49, 49), (0, 0, 32), None),
       "main": ((255, 213, 123), (123, 57, 8), (8, 0, 57))}


def nearest(pal, pb, c):
    return min(range(1, 16), key=lambda i: sum((a - b) ** 2 for a, b in zip(rgb(pal, pb, i), c)))


def render_mask(text, font, size):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(str(FONTS / font), size)
    if "wght" in font:
        f.set_variation_by_name("Bold")
    im = Image.new("L", (300, 40), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"  # no antialiasing: 16-colour tiles
    d.text((0, 0), text, font=f, fill=255)
    box = im.getbbox()
    im = im.crop(box)
    return [[im.getpixel((x, y)) > 127 for x in range(im.width)] for y in range(im.height)]


def dilate(m, w, h):
    return {(x + dx, y + dy) for (x, y) in m for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - set(m)


def draw():
    vram, pal, cells, idx, bank = load()
    orig = [r[:] for r in idx]
    for name, (x0, y0, w, h), text, font, size, _, _, ax, ay in ROWS:
        inside = [(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w) if bank[y][x] in SKY]
        for y in range(y0, y0 + h):  # clear: lettering pixels -> nearest sky pixel on the row (same bank)
            for x in range(x0, x0 + w):
                pb = bank[y][x]
                if pb not in SKY or idx[y][x] in SKY[pb]:
                    continue
                for d in range(1, 64):
                    hit = [xx for xx in (x - d, x + d) if 0 <= xx < 240 and bank[y][xx] == pb
                           and orig[y][xx] in SKY[pb]]
                    if hit:
                        idx[y][x] = orig[y][hit[0]]
                        break
                else:
                    idx[y][x] = min(SKY[pb])
        m = render_mask(text, font, size)
        pts = {(ax + x, ay + y) for y, r in enumerate(m) for x, v in enumerate(r) if v}
        fill, ol, ol2 = INK[name]
        ring1 = dilate(pts, 0, 0)
        layers = [(ring1, ol), (pts, fill)]
        if ol2 is not None:
            layers.insert(0, (dilate(pts | ring1, 0, 0), ol2))
        ok = set(inside)
        for layer, ink in layers:
            for p in layer:
                if p not in ok:
                    raise SystemExit(f"{name}: '{text}' pixel {p} outside its rect {x0},{y0},{w},{h}")
                idx[p[1]][p[0]] = nearest(pal, bank[p[1]][p[0]], ink)
        print(f"{name}: '{text}' {max(x for x, _ in pts) - ax + 1}x{max(y for _, y in pts) - ay + 1} px at {ax},{ay}")
    rom = next((ROOT / "rom").glob("*.gba")).read_bytes()
    block = bytearray(packed.unpack(rom, BLOCK)[1])
    assert bytes(block) == vram[LOAD:LOAD + len(block)], "VRAM dump does not hold the block at LOAD"
    owner = {}
    for (tx, ty), (t, hf, vf, pb) in cells.items():
        if tx >= 30 or ty >= 20:
            continue
        for y in range(8):
            for x in range(8):
                sx, sy = tx * 8 + x, ty * 8 + y
                if idx[sy][sx] == orig[sy][sx]:
                    continue
                px, py = (7 - x if hf else x), (7 - y if vf else y)
                key = (t, px, py)
                if key in owner and owner[key] != idx[sy][sx]:
                    raise SystemExit(f"tile {t:#x} is shared and would change two ways")
                owner[key] = idx[sy][sx]
    users = {}
    for (tx, ty), (t, *_ ) in cells.items():
        users.setdefault(t, set()).add((tx, ty))
    for (t, px, py), v in owner.items():
        if len(users[t]) > 1:
            raise SystemExit(f"tile {t:#x} used at {sorted(users[t])}: would change other cells")
        o = t * 32 - LOAD + py * 4 + px // 2
        assert 0 <= o < len(block), f"tile {t:#x} is not in block {BLOCK:#x}"
        block[o] = (block[o] & 0x0F) | (v << 4) if px & 1 else (block[o] & 0xF0) | v
    BIN.parent.mkdir(parents=True, exist_ok=True)
    BIN.write_text(gfx.make_diff(packed.unpack(rom, BLOCK)[1], bytes(block)))
    OUT.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    for nm, src in (("orig", orig), ("en", idx)):
        im = Image.new("RGB", (240, 160))
        im.putdata([rgb(pal, bank[y][x], src[y][x]) for y in range(160) for x in range(240)])
        im.save(OUT / f"{nm}.png")
    print(f"{len({k[0] for k in owner})} tiles changed -> {BIN.relative_to(ROOT)}; screens in {OUT.relative_to(ROOT)}")


def main():
    if sys.argv[1:] == ["info"]:
        info()
    elif sys.argv[1:] == ["draw"]:
        draw()
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
