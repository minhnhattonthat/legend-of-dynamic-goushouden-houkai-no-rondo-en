"""Battle SFX cut-ins (ドワッ, ガキーン...): English letters for the onomatopoeia sprite font (graphics group S5).

    python -X utf8 tools/gfx_sfx.py draw     -> gfx/sfx_<BLOCK>.diff + work/gfx/sfx/preview.png
    python -X utf8 tools/gfx_sfx.py names    -> script/rom/sfx.json "en" from script/sfx_en.tsv (jp<TAB>en)
    python -X utf8 tools/gfx_sfx.py check    -> every English SFX name uses only drawn letters, <= MAXLEN

How the game draws them (docs/re/graphics.md S5): an onomatopoeia record's name (0x0D9CF8 + 0x20 i, +0x0C) is read
two bytes per char by 0x080C6258; each char is looked up in a 40-entry kana list (table 0x08104D1C -> entries
0x0D9CF4 - 4 i: index 0 = う ... 39 = ピ) and index i draws the 32x32 OBJ glyph in packed block BLOCKS[i] (the
blocks sit in that order, each behind its 32-byte record). A char not in the list is skipped. The object keeps 6
glyph slots (+0x30..+0x35) and loads a glyph per char, but the cut-in draws only 4 sprites (32 px apart, scrolling
left from x 233), so English names are at most 4 letters.

English: index i gets the letter SLOTS[i] (fullwidth SJIS in both the lookup and the names); the other kana
indices keep their glyphs and codes. Letters: Bangers (OFL, fonts/Bangers-Regular.ttf), drawn in
the original's style: body gradient b (top) .. 3 (bottom), outline 2 above / right, c-f below / left, shadow 1.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402
import packed  # noqa: E402
import sjis  # noqa: E402

ROM = ROOT / "rom" / "Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba"
FONT = ROOT / "fonts" / "Bangers-Regular.ttf"
OUT = ROOT / "work" / "gfx" / "sfx"
NAMES = ROOT / "script" / "sfx_en.tsv"

# packed glyph blocks, lookup index order (う ふ ん ア イ ウ オ カ キ シ ス タ チ ヒ ホ リ ル ワ ン ァ ィ ゥ ォ ッ ャ ュ ー
# ガ ギ グ ゴ ジ ズ ド バ ビ ブ ベ ボ ピ)
BLOCKS = [0x3873C8, 0x3874C4, 0x3875D0, 0x3876E8, 0x3877D4, 0x3878B8, 0x3879B4, 0x387AB8, 0x387BB8, 0x387CBC,
          0x387DD4, 0x387ED8, 0x387FE8, 0x3880E4, 0x3881CC, 0x3882F4, 0x3883D4, 0x3884E0, 0x3885C8, 0x3886BC,
          0x388780, 0x38883C, 0x388914, 0x3889E8, 0x388AD0, 0x388BA8, 0x388C68, 0x388CE8, 0x388E08, 0x388F10,
          0x389034, 0x389124, 0x389254, 0x389370, 0x38944C, 0x38956C, 0x38966C, 0x389768, 0x389858, 0x389998]
LOOKUP = 0x0D9C58          # 40 entries of {u16 sjis (big-endian bytes), u16 0}; index i at LOOKUP_LAST - 4 i
LOOKUP_LAST = 0x0D9CF4
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ!"
# index -> letter ("." = kana kept). A letter must repack (lh5) into its block's packed slot: letters sorted by
# packed size went to the blocks sorted by slot size (largest to largest; every one fits with 9+ bytes to spare,
# the small-kana blocks ィ ォ ュ ー stay). Changing the font or the drawing: re-run that matching.
MAP = "THRI.FZPYKCSE.G.D.!........NXMLQU.OVBJWA"
SLOTS = {i: c for i, c in enumerate(MAP) if c != "."}
assert sorted(SLOTS.values()) == sorted(LETTERS)
MAXLEN = 4  # the cut-in draws 4 glyph sprites (OAM log, tools/lua/oamlog.lua); the 5th+ load but never show

GRAD = [0xB, 0xB, 0xB, 0xA, 0x9, 0x8, 0x7, 0x6, 0x5, 0x4, 0x4, 0x4, 0x3]
OUTLINE, LOW, SHADOW = 0x2, 0xD, 0x1
CAP = 22                   # letter height in px (the kana bodies are 21-24)
WIDEN = 1.4
BOX = (3, 5, 26, 27)       # x0, y0, x1, y1 the letter is centred in (shadow falls right / below)


def code(ch):
    return sjis.encode(sjis.fullwidth(ch))


def lookup_bytes(orig):
    """The new 0x0D9C58..0x0D9CF8 span: SLOTS letters in their indices, the rest as in the original."""
    out = bytearray(orig[LOOKUP:LOOKUP_LAST + 4])
    for i, ch in SLOTS.items():
        c = code(ch)
        assert len(c) == 2, ch
        at = LOOKUP_LAST - 4 * i - LOOKUP
        out[at:at + 4] = c + b"\0\0"
    return bytes(out)


def apply(orig, put):
    """Build step: write the lookup span (the glyph blocks go in through gfx/sfx_*.diff, gfx.insert)."""
    new = lookup_bytes(orig)
    if new != orig[LOOKUP:LOOKUP_LAST + 4]:
        put(LOOKUP, new, "sfx glyph lookup")


def ranges():
    return [(LOOKUP, LOOKUP_LAST + 4)]


def mask(ch):
    """Letter pixels in the 32x32 cell: drawn at 8x, scaled to CAP px cap height and WIDEN wider (Bangers is
    condensed; the kana are ~22 px wide), thresholded (16-colour tiles, no antialiasing)."""
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(str(FONT), 8 * 32)
    hb = f.getbbox("H")
    k = CAP / (hb[3] - hb[1])
    im = Image.new("L", (512, 512), 0)
    ImageDraw.Draw(im).text((64, 64), ch, font=f, fill=255)
    box = im.getbbox()
    w = max(1, round((box[2] - box[0]) * k * WIDEN))
    h = max(1, round((box[3] - box[1]) * k))
    sm = im.crop(box).resize((w, h), Image.LANCZOS)
    top = round((box[1] - 64 - hb[1]) * k)  # every letter on the cap line, "!" included
    x0 = BOX[0] + (BOX[2] - BOX[0] - w) // 2
    return {(x + x0, y + top + BOX[1]) for y in range(h) for x in range(w) if sm.getpixel((x, y)) > 110}


def glyph(ch):
    """32x32 index grid for one letter."""
    m = mask(ch)
    ys = [y for _, y in m]
    top, bot = min(ys), max(ys)
    g = [[0] * 32 for _ in range(32)]
    ring = {(x + dx, y + dy) for (x, y) in m for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - m
    for (x, y) in ring | m:  # shadow first: everything shifted 1-2 px right / down
        for d in (1, 2):
            if 0 <= x + d < 32 and 0 <= y + d < 32:
                g[y + d][x + d] = SHADOW
    mid = (top + bot) / 2
    for (x, y) in ring:
        if not (0 <= x < 32 and 0 <= y < 32):
            continue
        below = (x, y - 1) in m and (x, y + 1) not in m
        left = (x + 1, y) in m and (x - 1, y) not in m and y > mid
        g[y][x] = LOW if below or left else OUTLINE
    for (x, y) in m:
        t = (y - top) / max(1, bot - top)
        g[y][x] = GRAD[int(t * (len(GRAD) - 1) + 0.5)]
    return g


def to_tiles(g):
    """32x32 grid -> 16 4bpp tiles, 1D OBJ order (4 tiles per row)."""
    out = bytearray(512)
    for y in range(32):
        for x in range(32):
            t = (y // 8) * 4 + x // 8
            i = t * 32 + (y % 8) * 4 + (x % 8) // 2
            out[i] |= g[y][x] << (4 * (x & 1))
    return bytes(out)


def from_tiles(b):
    g = [[0] * 32 for _ in range(32)]
    for y in range(32):
        for x in range(32):
            t = (y // 8) * 4 + x // 8
            v = b[t * 32 + (y % 8) * 4 + (x % 8) // 2]
            g[y][x] = (v >> 4) if x & 1 else v & 15
    return g


def draw():
    from PIL import Image
    orig = ROM.read_bytes()
    OUT.mkdir(parents=True, exist_ok=True)
    for p in gfx.DIR.glob("sfx_*.diff"):
        p.unlink()
    pal = [(0, 0, 0), (40, 0, 20)] + [(255, 255, 255)] + [(60 + 18 * i, 20 + 12 * i, 30 + 12 * i) for i in range(1, 10)] \
        + [(150, 60, 70), (120, 40, 60), (90, 30, 50), (70, 20, 40)]
    sheet = Image.new("RGB", (len(BLOCKS) * 34, 70), (60, 60, 90))
    total = 0
    for i, off in enumerate(BLOCKS):
        _, raw, size = packed.unpack(orig, off)
        assert len(raw) == 512, hex(off)
        new = to_tiles(glyph(SLOTS[i])) if i in SLOTS else raw
        if new != raw:
            (gfx.DIR / ("sfx_%06X.diff" % off)).write_text(gfx.make_diff(raw, new), encoding="utf-8", newline="\n")
            total += 1
        for row, data in ((0, raw), (1, new)):
            g = from_tiles(data)
            for y in range(32):
                for x in range(32):
                    sheet.putpixel((i * 34 + x, row * 35 + y), pal[g[y][x]])
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    sheet.save(OUT / "preview.png")
    print("%d glyph blocks redrawn; preview %s" % (total, OUT / "preview.png"))


def table():
    rows = {}
    for line in NAMES.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            jp, en = line.split("\t")
            rows[jp] = en
    return rows


def check():
    import extract
    rows, bad = table(), []
    for e in extract.load("rom/sfx.json"):
        en = rows.get(e["jp"])
        if en is None:
            bad.append("%s %s: no line in %s" % (e["id"], e["jp"], NAMES.name))
        elif len(en) > MAXLEN or any(c not in LETTERS for c in en):
            bad.append("%s %s -> %r: over %d letters or a letter not in SLOTS" % (e["id"], e["jp"], en, MAXLEN))
        elif e.get("en") != en:
            bad.append("%s %s: sfx.json en %r != %r (run gfx_sfx.py names)" % (e["id"], e["jp"], e.get("en"), en))
    return bad


def names():
    import extract
    rows = table()
    ents = extract.load("rom/sfx.json")
    for e in ents:
        if e["jp"] in rows:
            e["en"] = rows[e["jp"]]
            e["notes"] = "drawn as sprites: lookup 0x0D9C58 + glyphs, tools/gfx_sfx.py (English from script/sfx_en.tsv)"
    extract.save("rom/sfx.json", ents)
    print("sfx.json: %d of %d names set" % (sum(1 for e in ents if e["jp"] in rows), len(ents)))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "draw":
        draw()
    elif cmd == "names":
        names()
    elif cmd == "check":
        bad = check()
        print("\n".join(bad) or "sfx ok")
        sys.exit(1 if bad else 0)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
