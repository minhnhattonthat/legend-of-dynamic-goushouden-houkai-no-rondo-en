"""Redraw small framed graphics labels (menus, battle UI) in English, screen by screen (docs/re/graphics.md).

    python -X utf8 tools/gfxlabel.py dump [SCREEN..]      warp the original ROM there and dump VRAM (tools/ppuscene.py)
    python -X utf8 tools/gfxlabel.py info SCREEN          palette-index histogram per label rect (to pick clear/ink)
    python -X utf8 tools/gfxlabel.py draw [SCREEN..]      redraw -> gfx/<screen>_<BLOCK>.diff + work/gfx/<screen>/

How: the screen is composed from the original's VRAM dump with every pixel's source (tools/gfxscreen.py). In each
label rect the pixels whose palette index is in `clear` take the nearest kept pixel of the same row (the frame's
fill, gradients included), then the English is drawn with a 1-px outline (fonts/, docs/fonts.md). Each changed VRAM
byte goes back to the packed block it was loaded from (vramfind.py runs against work/blocks, tools/dumpblocks.py),
and the same tile edit goes to every other block holding that exact tile (duplicates other screens load). Refuses:
a tile shown somewhere outside the label rects that would change, a nibble written two ways, a pixel outside the rect.
gfx.insert merges every diff of one block and repacks it as lh5 in place.
"""
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402
import gfxscreen  # noqa: E402
import packed  # noqa: E402
from skill import SKILL  # noqa: E402

FONTS = ROOT / "fonts"
BLOCKS = ROOT / "work" / "blocks"
FRAMES = 900

# Label classes: one font and size per class (graphics.md §Lettering). fill/outline are RGB, matched to the nearest
# colour of each pixel's own palette bank.
CLASSES = {
    "small": dict(font="pixfont", size=6),  # tools/pixfont.py: 6-px bold caps, 1-px outline -> 8 rows
    "head": dict(font="PressStart2P-Regular.ttf", size=8),  # screen-title pills: 7-px caps, outline -> 9 rows
}


def head(text, **opt):
    """The green screen-title pill (top left of every menu screen): lavender gradient, navy outline."""
    return ("head", (25, 2, 75, 13), text, "head", {3, 12, 13, 14, 15}, ([12, 13, 14, 15], 3), opt)

# screen -> scene (tools/debug/scenes.txt) and labels: (name, rect x,y,w,h, English, class, clear indices,
# (fill RGB, outline RGB)). Rects must cover the whole original glyph (dakuten, outline).
SCREENS = {
    "item": dict(scene="m1_item", labels=[
        head("ITEMS", dx=-2),  # x 80-95 above the glyphs is one tile used twice: stay left of x 80
        ("use", (2, 19, 28, 9), "USE", "small", {3, 4, 11, 12, 13}, ([11, 12, 13], 4)),
        ("drop", (34, 19, 28, 9), "DROP", "small", {3, 4, 11, 12, 13}, ([11, 12, 13], 4)),
        ("sort", (66, 19, 28, 9), "SORT", "small", {3, 4, 11, 12, 13}, ([11, 12, 13], 4)),
        ("col1", (38, 47, 36, 9), "ITEM", "small", {1, 7, 8, 9, 10}, ([7, 8, 9, 10], 1)),
        ("col2", (148, 47, 40, 9), "ITEM", "small", {1, 7, 8, 9, 10}, ([7, 8, 9, 10], 1)),
    ]),
    "menu": dict(scene="k_jump", labels=[head("MENU")]),
    "book": dict(scene="k_jump2", labels=[head("PROFILES")]),
    "party": dict(scene="m1_party", labels=[head("PARTY")]),
    "spoils": dict(scene="m1_crop", labels=[head("SPOILS")]),
    "status": dict(scene="m1_status", labels=[head("STATUS")]),
    # セーブ画面 / ロード画面 share the 画面 tiles (x>=64 on the glyph rows): the word sits in x 33-63
    "save": dict(scene="m1_save", labels=[head("SAVE", dx=-14, ring_xmax=63, clear_right=1)]),
    "load": dict(scene="m1_load", labels=[head("LOAD", dx=-14, clear_right=1)]),
    # battle command list (S4, block 0x361AE4): 4 rows of 8 px, kana drawn with a right/bottom shadow
    "battle": dict(scene="k_ode", labels=[
        ("fight", (48, 123, 37, 8), "FIGHT", "small", {1, 13, 14}, ([13, 14, 14], 1), dict(left=1)),
        ("item", (48, 131, 37, 8), "ITEM", "small", {1, 13, 14}, ([13, 14, 14], 1), dict(left=1)),
        ("swap", (48, 139, 37, 8), "SWAP", "small", {1, 13, 14}, ([13, 14, 14], 1), dict(left=1)),
        ("run", (48, 147, 37, 8), "RUN", "small", {1, 13, 14}, ([13, 14, 14], 1), dict(left=1)),
    ]),
}


def prefix(screen):
    return ROOT / "work" / "qa" / "ppu" / f"jp_{SCREENS[screen]['scene']}" / f"ppu_{FRAMES - 1:06d}"


def runs(pre):
    """[(vram lo, vram hi, block offset, block-relative lo)] from vramfind.py against work/blocks."""
    cache = pre.with_suffix(".find.txt")
    if not cache.exists():
        cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "vramfind.py"),
               str(pre.with_suffix(".vram.bin")), str(BLOCKS), "--fmt", "gba4"]
        cache.write_text(subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8").stdout)
    out = []
    for m in re.finditer(r"VRAM ([0-9A-F]+)-([0-9A-F]+) .*?([0-9A-F]{6})\.bin ([0-9A-F]+)-", cache.read_text()):
        out.append((int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16), int(m.group(4), 16)))
    return out


_ALL = []


def all_blocks():
    """({offset: unpacked bytes} for every block in work/blocks, {offsets that start inside another block})."""
    if not _ALL:
        import json
        alls = {int(f.stem, 16): f.read_bytes() for f in BLOCKS.glob("*.bin")}
        spans = sorted((o, o + n) for o, _, _, n, *_ in json.loads((ROOT / "work" / "packed_blocks.json").read_text()))
        inner, end = set(), 0
        for o, e in spans:
            if o < end:
                inner.add(o)
            end = max(end, e)
        _ALL.extend([alls, inner])
    return _ALL[0], _ALL[1]


def render_mask(text, font, size, weight=None):
    if font == "pixfont":
        import pixfont
        return pixfont.mask(text)
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(str(FONTS / font), size)
    if weight:
        f.set_variation_by_name(weight)
    im = Image.new("L", (400, 40), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"  # no antialiasing: 16-colour tiles
    d.text((4, 4), text, font=f, fill=255)
    box = im.getbbox()
    im = im.crop(box)
    return {(x, y) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y)) > 127}, im.width, im.height


def ring(pts):
    return {(x + dx, y + dy) for (x, y) in pts for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - pts


def nearest(scr, src, rgb):
    layer, _, _, bank, _ = src
    obj = layer.startswith("obj")
    return min(range(1, 16), key=lambda i: sum((a - b) ** 2 for a, b in zip(scr.color(bank, i, obj), rgb)))


def info(screen):
    pre = prefix(screen)
    full = gfxscreen.compose(pre)
    scrs = {"bg": gfxscreen.compose(pre, objs=False), "obj": gfxscreen.compose(pre, bgs=False)}
    for name, (x0, y0, w, h), *rest in SCREENS[screen]["labels"]:
        opt = rest[4] if len(rest) > 4 else {}
        scr = scrs[opt.get("kind", "bg")]
        c = Counter()
        layers = Counter()
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                s = scr.src[y][x]
                if s:
                    c[(s[0][:3], s[3], s[4])] += 1
                    layers[s[0]] += 1
                f = full.src[y][x]
                if f and f[0] != (s and s[0]):
                    layers["covered by " + f[0]] += 1
        print(name, [(f"{lay}p{b}i{i}", n, scr.color(b, i, lay == "obj")) for (lay, b, i), n in c.most_common(10)])
        print("   layers", dict(layers))


def draw(screen):
    cfg = SCREENS[screen]
    pre = prefix(screen)
    full = gfxscreen.compose(pre)
    scrs = {"bg": gfxscreen.compose(pre, objs=False), "obj": gfxscreen.compose(pre, bgs=False)}
    vram = bytearray(full.vram)
    newnib = {}  # (addr, hi) -> value
    want = {}  # (kind, x, y) -> value: the pixels we meant to set
    rects = []
    for name, (x0, y0, w, h), text, cls, clear, (fill_rgb, ol_rgb), *opt in cfg["labels"]:
        opt = opt[0] if opt else {}
        scr = scrs[opt.get("kind", "bg")]
        rects.append((x0, y0, w, h))
        val = {}
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                s = scr.src[y][x]
                if s and s[4] in clear:
                    # nearest kept pixel; clear_right=1 looks right first (identical result in a tile two
                    # screens share when only the left part differs)
                    order = [(d,) for d in range(1, 64)] if not opt.get("clear_right") else \
                        [(d,) for d in range(1, w)] + [(-d,) for d in range(1, w)]
                    for (d,) in order:
                        cand = (x - d, x + d) if not opt.get("clear_right") else (x + d,)
                        hit = [xx for xx in cand if x0 <= xx < x0 + w and scr.src[y][xx]
                               and scr.src[y][xx][4] not in clear and scr.src[y][xx][0] == s[0]]
                        if hit:
                            val[(x, y)] = scr.src[y][hit[0]][4]
                            break
                    else:  # a row with no kept pixel (a dark stripe): its left-edge index
                        val[(x, y)] = scr.src[y][x0][4]
        c = CLASSES[cls]
        pts, tw, th = render_mask(text, c["font"], opt.get("size", c["size"]), c.get("weight"))
        ax = (x0 + 1 if opt.get("left") else x0 + (w - tw) // 2) + opt.get("dx", 0)
        ay = y0 + (h - th + 1) // 2 + opt.get("dy", 0)
        pts = {(ax + x, ay + y) for x, y in pts}
        rg = {(x, y) for x, y in ring(pts) if x <= opt.get("ring_xmax", 999)} if ol_rgb is not None else set()
        for layer, ink in ((rg, ol_rgb), (pts, fill_rgb)):
            for (x, y) in layer:
                if not (x0 <= x < x0 + w and y0 <= y < y0 + h) or not scr.src[y][x]:
                    raise SystemExit(f"{screen}/{name}: '{text}' pixel ({x},{y}) outside rect or on backdrop")
                if isinstance(ink, int):
                    val[(x, y)] = ink
                elif isinstance(ink, list):  # palette indices top to bottom over the glyph rows
                    val[(x, y)] = ink[min(len(ink) - 1, (y - ay) * len(ink) // th)]
                else:
                    val[(x, y)] = nearest(scr, scr.src[y][x], ink)
        for (x, y), v in val.items():
            _, addr, hi, _, old = scr.src[y][x]
            k = (addr, hi)
            if newnib.get(k, v) != v:
                raise SystemExit(f"{screen}/{name}: VRAM {addr:#x} written two ways (a tile repeats in the label)")
            newnib[k] = v
            want[(opt.get("kind", "bg"), x, y)] = v
        print(f"{name}: '{text}' {tw}x{th} px at {ax},{ay}")
    for (addr, hi), v in newnib.items():
        vram[addr] = (vram[addr] & 0x0F) | (v << 4) if hi else (vram[addr] & 0xF0) | v
    # every pixel that changes must be one we meant to change (a tile repeated elsewhere, in or out of a label)
    for kind, scr in scrs.items():
        for y in range(160):
            for x in range(240):
                s = scr.src[y][x]
                if s and (s[1], s[2]) in newnib and newnib[(s[1], s[2])] != s[4] \
                        and want.get((kind, x, y)) != newnib[(s[1], s[2])]:
                    raise SystemExit(f"{screen}: tile at VRAM {s[1]:#x} also shows at ({x},{y}) and would change there")
    # back to the blocks
    rom = next((ROOT / "rom").glob("*.gba")).read_bytes()
    rs = runs(pre)
    tiles = {}
    for (addr, _) in newnib:
        t0 = addr & ~31
        tiles[t0] = (bytes(full.vram[t0:t0 + 32]), bytes(vram[t0:t0 + 32]))
    edits = {}  # block offset -> bytearray
    raws = {}

    def block(off):
        if off not in edits:
            raws[off] = packed.unpack(rom, off)[1]
            edits[off] = bytearray(raws[off])
        return edits[off]

    alls, inner = all_blocks()
    skipped = set()
    for t0, (old, new) in sorted(tiles.items()):
        src = {boff for lo, hi, boff, blo in rs if lo <= t0 and t0 + 32 <= hi + 1}
        if not src:
            raise SystemExit(f"{screen}: VRAM tile {t0:#x} not found in any packed block")
        for off, data in alls.items():
            i = data.find(old)
            if i < 0:
                continue
            if off in inner and off not in src:
                skipped.add(off)  # a false-positive decode inside a real block: never write there
                continue
            while i >= 0:
                block(off)[i:i + 32] = new
                i = data.find(old, i + 1)
    if skipped:
        print(f"{screen}: skipped blocks inside other blocks: {', '.join('%06X' % o for o in sorted(skipped))}")
    gfx.DIR.mkdir(exist_ok=True)
    for old in gfx.DIR.glob(f"{screen}_*.diff"):
        old.unlink()
    for off, b in sorted(edits.items()):
        if bytes(b) != raws[off]:
            (gfx.DIR / f"{screen}_{off:06X}.diff").write_text(gfx.make_diff(raws[off], bytes(b)), newline="\n")
    print(f"{screen}: {len(tiles)} tiles changed, blocks {', '.join('%06X' % o for o in sorted(edits))}")
    # preview
    out = ROOT / "work" / "gfx" / screen
    out.mkdir(parents=True, exist_ok=True)
    full.image().save(out / "orig.png")
    full.recompose(vram)
    full.image().save(out / "en.png")


def grid(scene, rect, kind="bg"):
    """Print a rect of the original screen as palette indices (hex), '*' after a tile column shared elsewhere."""
    pre = ROOT / "work" / "qa" / "ppu" / f"jp_{scene}" / f"ppu_{FRAMES - 1:06d}"
    scr = gfxscreen.compose(pre, objs=kind == "obj", bgs=kind == "bg")
    x0, y0, w, h = rect
    uses = {}
    for y in range(160):
        for x in range(240):
            s = scr.src[y][x]
            if s:
                uses.setdefault(s[1] & ~31, set()).add((x // 8, y // 8))
    print("     " + "".join(str(x % 10) for x in range(x0, x0 + w)))
    for y in range(y0, y0 + h):
        row = ""
        for x in range(x0, x0 + w):
            s = scr.src[y][x]
            row += "%x" % s[4] if s else "."
        shared = "".join("*" if (s := scr.src[y][x]) and len(uses[s[1] & ~31]) > 1 else " "
                         for x in range(x0, x0 + w, 8))
        print(f"{y:4d} {row}  {shared}  {scr.src[y][x0][0] if scr.src[y][x0] else ''}")


def main():
    if len(sys.argv) >= 4 and sys.argv[1] == "grid":
        return grid(sys.argv[2], tuple(int(v) for v in sys.argv[3].split(",")), *(sys.argv[4:5] or ["bg"]))
    if len(sys.argv) < 2 or sys.argv[1] not in ("dump", "info", "draw"):
        raise SystemExit(__doc__)
    cmd, names = sys.argv[1], sys.argv[2:] or sorted(SCREENS)
    for n in names:
        if cmd == "dump":
            import ppuscene
            print(ppuscene.dump(SCREENS[n]["scene"], "jp", FRAMES))
        elif cmd == "info":
            info(n)
        else:
            draw(n)


if __name__ == "__main__":
    main()
