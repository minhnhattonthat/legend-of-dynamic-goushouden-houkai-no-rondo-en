"""gfxsweep.py: static graphics-text sweep (docs/re/graphics.md). Renders every decoded block into labelled pages.

Sources: the packed blocks in work/packed_blocks.json (tools/scanpacked.py; decoded with tools/packed.py; labels
"t1_"/"t3_" for types 1/3, bare offsets for lh5) plus any *.bin files in --dumps
(blocks the emulator unpacked, named <hexsrc>.bin, for codecs not written in Python yet), plus raw ROM ranges given
with --raw START-END.

Each block is classified; text, palette-sized and tiny blocks are skipped and listed (never dropped silently).
The rest are drawn as gba4 (and gba8 when the nibble statistics suggest 8bpp) in grey, 32 tiles per row, packed
onto pages of --width px with the block offset written above each one. An index (pages.tsv) maps page -> blocks.

  python -X utf8 tools/gfxsweep.py --out work/sweep [--dumps work/qa/tour1/blocks] [--raw 0x1F0D00-0x2056AA]
"""
import argparse
import glob
import hashlib
import json
import os
import sys
from collections import Counter

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import packed  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM = os.path.join(ROOT, "rom", "Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba")
COLS = 32
LABEL = 10


def sjis_ratio(b):
    sj = i = 0
    while i < len(b) - 1:
        c = b[i]
        if (0x81 <= c <= 0x9F or 0xE0 <= c <= 0xEF) and 0x40 <= b[i + 1] <= 0xFC:
            sj += 2
            i += 2
        else:
            i += 1
    return sj / max(1, len(b))


def nib_skew(b):
    """Distance between the high- and low-nibble histograms: ~0 for 4bpp pixels, large for 8bpp."""
    hi = [0] * 16
    lo = [0] * 16
    for x in b:
        hi[x >> 4] += 1
        lo[x & 15] += 1
    n = max(1, len(b))
    return sum(abs(hi[k] - lo[k]) for k in range(16)) / (2 * n)


def classify(b):
    if len(b) < 128:
        return "skip:tiny"
    if sjis_ratio(b) > 0.3:
        return "skip:text"
    if len(b) <= 512 and len(b) % 32 == 0 and all(b[k + 1] < 0x80 for k in range(0, len(b), 2)):
        return "skip:palette?"
    if maplike(b):
        return "skip:tilemap?"
    return "gfx"


def maplike(b):
    """BG tilemap: u16 entries whose high byte (palette, flips, tile bits 8-9) takes few values (98% in <= 12)
    while the low byte (tile number) takes many. 2-colour glyph tiles have few values in both bytes."""
    if len(b) < 64 or len(b) & 1:
        return False
    hi = Counter(b[1::2])
    lo = set(b[0::2])
    top = sum(v for _, v in hi.most_common(12))
    return top >= 0.98 * (len(b) // 2) and len(lo) > 24


def draw_block(b, fmt):
    size = 32 if fmt == "gba4" else 64
    n = len(b) // size
    rows = -(-n // COLS)
    img = Image.new("L", (COLS * 8, rows * 8), 0)
    px = img.load()
    # stretch to the block's own range so 2-3-colour art and low 8bpp indices stay visible
    top = max(max(x >> 4 for x in b), max(x & 15 for x in b)) if fmt == "gba4" else max(b)
    scale = 255 / max(1, top)
    for t in range(n):
        d = b[t * size:(t + 1) * size]
        ox, oy = t % COLS * 8, t // COLS * 8
        for i in range(64):
            if fmt == "gba4":
                v = d[i >> 1] >> (4 * (i & 1)) & 15
            else:
                v = d[i]
            px[ox + (i & 7), oy + (i >> 3)] = int(v * scale)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--dumps", action="append", default=[])
    ap.add_argument("--raw", action="append", default=[])
    ap.add_argument("--width", type=int, default=1056)
    ap.add_argument("--height", type=int, default=1056)
    ap.add_argument("--no-lh5", action="store_true", help="skip work/packed_blocks.json")
    ap.add_argument("--skew8", type=float, default=0.45, help="also draw gba8 above this nibble skew")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rom = open(ROM, "rb").read()
    blocks = []  # (name, bytes)
    if not a.no_lh5:
        for row in sorted(json.load(open(os.path.join(ROOT, "work", "packed_blocks.json")))):
            o, typ = row[0], row[1]
            _, data, _ = packed.unpack(rom, o)
            blocks.append(("lh5_%06X" % o if typ == 2 else "t%d_%06X" % (typ, o), data))
    for d in a.dumps:
        for p in sorted(glob.glob(os.path.join(d, "*.bin"))):
            blocks.append(("dump_" + os.path.splitext(os.path.basename(p))[0], open(p, "rb").read()))
    for r in a.raw:
        s, e = (int(x, 0) for x in r.split("-"))
        blocks.append(("raw_%06X" % s, rom[s:e]))
    seen = {}
    todo = []
    skipped = open(os.path.join(a.out, "skipped.tsv"), "w", encoding="utf-8")
    for name, b in blocks:
        h = hashlib.sha1(b).hexdigest()
        if h in seen:
            skipped.write("%s\tdup of %s\n" % (name, seen[h]))
            continue
        seen[h] = name
        k = classify(b)
        if k != "gfx":
            skipped.write("%s\t%s\t%d bytes\n" % (name, k, len(b)))
            continue
        todo.append((name, b, "gba4"))
        if nib_skew(b) > a.skew8:
            todo.append((name, b, "gba8"))
    skipped.close()
    # pack: masonry columns (COLS*8 px wide); a block goes to the shortest column; tall blocks are sliced
    index = open(os.path.join(a.out, "pages.tsv"), "w", encoding="utf-8")
    colw = COLS * 8 + 8
    ncol = max(1, a.width // colw)
    maxh = a.height - LABEL
    slices = []
    for name, b, fmt in todo:
        img = draw_block(b, fmt)
        step = COLS * (32 if fmt == "gba4" else 64)
        for sy in range(0, img.height, maxh):
            sl = img.crop((0, sy, img.width, min(img.height, sy + maxh)))
            short = name[5:] if name.startswith("dump_") else name.replace("lh5_", "")
            slices.append((sl, "%s %s%s" % (short, fmt[3:], "+%X" % (sy // 8 * step) if sy else ""), name, fmt, sy // 8 * step))
    pno = 0
    page = Image.new("RGB", (a.width, a.height), (40, 0, 40))
    tops = [0] * ncol
    for sl, lab, name, fmt, off in slices:
        c = min(range(ncol), key=lambda k: tops[k])
        if tops[c] + sl.height + LABEL > a.height:
            page.save(os.path.join(a.out, "page%03d.png" % pno))
            pno += 1
            page = Image.new("RGB", (a.width, a.height), (40, 0, 40))
            tops = [0] * ncol
            c = 0
        x, y = c * colw, tops[c]
        page.paste(sl.convert("RGB"), (x, y + LABEL))
        ImageDraw.Draw(page).text((x + 1, y - 1), lab, fill=(255, 255, 0))
        index.write("page%03d\t%s\t%s\t+%X\n" % (pno, name, fmt, off))
        tops[c] = y + LABEL + sl.height + 3
    page.save(os.path.join(a.out, "page%03d.png" % pno))
    index.close()
    print("%d blocks, %d unique, %d rendered (%d renders), %d pages" % (
        len(blocks), len(seen), len({n for n, _, _ in todo}), len(todo), pno + 1))


if __name__ == "__main__":
    main()
