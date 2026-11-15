"""Redraw small framed graphics labels (menus, battle UI) in English, screen by screen (docs/re/graphics.md).

    python -X utf8 tools/gfxlabel.py dump [SCREEN..]      warp the original ROM there and dump VRAM (tools/ppuscene.py)
    python -X utf8 tools/gfxlabel.py info SCREEN          palette-index histogram per label rect (to pick clear/ink)
    python -X utf8 tools/gfxlabel.py draw [SCREEN..]      redraw -> gfx/<screen>_<BLOCK>.diff + work/gfx/<screen>/
                                                          (a TILES name draws tiles straight into its block)

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
VERBOSE = "-v" in sys.argv

# Label classes: one font and size per class (graphics.md §Lettering). fill/outline are RGB, matched to the nearest
# colour of each pixel's own palette bank.
CLASSES = {
    "small": dict(font="pixfont", size=6),  # tools/pixfont.py: 6-px bold caps, 1-px outline -> 8 rows
    "btn": dict(font="pixfont", size=6, shadow=True),  # tabs and buttons: drop shadow like the game's kana
    "head": dict(font="PressStart2P-Regular.ttf", size=8),  # screen-title pills: 7-px caps, outline -> 9 rows
    "tiny": dict(font="pixfont-tiny", size=5, shadow=True),  # 3x5 caps + drop shadow: under ~6 px per letter
}


def head(text, **opt):
    """The green screen-title pill (top left of every menu screen): lavender gradient, navy outline."""
    return ("head", (25, 2, 75, 13), text, "head", {3, 12, 13, 14, 15}, ([12, 13, 14, 15], 3), opt)

# screen -> scene (tools/debug/scenes.txt) and labels: (name, rect x,y,w,h, English, class, clear indices,
# (fill RGB, outline RGB)). Rects must cover the whole original glyph (dakuten, outline).
SCREENS = {
    "item": dict(scene="m1_item", labels=[
        head("ITEMS", dx=-2),  # x 80-95 above the glyphs is one tile used twice: stay left of x 80
        ("use", (2, 19, 28, 9), "USE", "btn", {3, 4, 11, 12, 13}, ([11, 12, 13], 4)),
        ("drop", (34, 19, 28, 9), "DROP", "btn", {3, 4, 11, 12, 13}, ([11, 12, 13], 4)),
        ("sort", (66, 19, 28, 9), "SORT", "btn", {3, 4, 11, 12, 13}, ([11, 12, 13], 4)),
        ("col1", (38, 47, 36, 9), "ITEM", "small", {1, 7, 8, 9, 10}, ([7, 8, 9, 10], 1)),
        ("col2", (148, 47, 40, 9), "ITEM", "small", {1, 7, 8, 9, 10}, ([7, 8, 9, 10], 1)),
    ]),
    "menu": dict(scene="k_jump", labels=[head("MENU")] + [
        (f"btn{i}", (147, 27 + 16 * i, 59, 10), t, "btn", {3, 4, 11, 12, 13, 15}, ([11, 12, 13], 4))
        for i, t in enumerate(["ITEMS", "PARTY", "STATUS", "SAVE"])]),
    "book": dict(scene="k_jump2", labels=[
        head("PROFILES"),
        ("skill", (5, 82, 37, 10), "SKILLS", "small", {1, 4, 7, 8, 9, 10}, ([7, 8, 9, 10], 1)),
        ("view", (159, 131, 23, 10), "VIEW", "small", {2, 3}, (2, None)),
        ("select", (186, 137, 52, 6), "SELECT:SEARCH", "tiny", {1, 2}, (2, None), dict(dy=-1)),
    ]),
    "party": dict(scene="m1_party", labels=[head("PARTY")]),
    # party edit: 1スキル / 1サポート are OBJ pills after the slot digit (text x 128-157 inside the border; x 120-127
    # is the cap tile, which differs in each pill's twin block 2FDCE0 / 2FDE1C: left alone so the copy reaches them);
    # バトラーストック (bg2, own tiles x 88-143; also on m2_bsel)
    "sparty": dict(scene="m2_sparty", labels=[
        ("skill", (128, 5, 30, 6), "SKILLS", "tiny", {1, 7, 8, 9, 10}, ([7, 8, 9, 10], 1), dict(kind="obj")),
        # サポート's glyphs start on the pill's top border row (y 48): that row clears to the border's index 1
        ("support", (128, 48, 30, 7), "SUPPORT", "tiny", {1, 7, 8, 9, 10}, ([7, 8, 9, 10], 1),
         dict(kind="obj", dy=1, clear_left=1)),
        ("stock", (88, 64, 56, 8), "BATTLER STOCK", "tiny", {1, 7, 8, 9, 10}, ([7, 8, 9, 10], 1),
         dict(kind="bg2")),
    ]),
    # partner stock (party edit -> a partner slot): パートナーストック's last 4 tiles (x 120-151) are バトラーストック's
    # ストック tiles (x 112-143 there): "R STOCK" ends both, so the text sits 8 px further right than on sparty
    # (PARTNE is 1 px wider than BATTLE: dx=3 puts the R 8 px right of sparty's) and those tiles come out identical. はずす / 全部はずす are 64x11 OBJ
    # buttons (blocks 2F990C / 2F99C0; highlighted twins 2F9C08 / 2F9CBC via VARIANTS)
    "sptn": dict(scene="m2_sptn", labels=[
        ("stock", (88, 64, 64, 8), "PARTNER STOCK", "tiny", {1, 7, 8, 9, 10}, ([7, 8, 9, 10], 1),
         dict(kind="bg2", dx=3)),
        ("rm", (170, 129, 59, 8), "REMOVE", "btn", {1, 15}, (15, 1), dict(kind="obj")),
        ("rmall", (170, 140, 59, 9), "REMOVE ALL", "btn", {1, 15}, (15, 1), dict(kind="obj")),
    ]),
    # shop, sell mode: アイテム / アクセサリー tabs (アクセサリー's tab is 34 px: GEAR, D9) and 売る数 (own tiles)
    "sell": dict(scene="m2_shop_sell", labels=[
        ("items", (38, 19, 34, 8), "ITEMS", "btn", {1, 15}, (15, 1)),
        ("gear", (87, 19, 35, 8), "GEAR", "btn", {1, 15}, (15, 1)),
        ("qty", (154, 76, 45, 12), "QTY", "head", {1, 2}, (2, 1)),
    ]),
    # the same tabs with アクセサリー selected: the other two states (blocks 2FA8D4 and the pink アクセサリー)
    "gear": dict(scene="m2_shop_gear", labels=[
        ("items", (38, 19, 34, 8), "ITEMS", "btn", {1, 15}, (15, 1)),
        ("gear", (87, 19, 35, 8), "GEAR", "btn", {1, 15}, (15, 1)),
    ]),
    "spoils": dict(scene="m1_crop", labels=[head("SPOILS")]),
    # stat labels (bg2 over the bg3 texture), one kana per tile of block 2F6658. こうげき's こ tile (x 8-15) is also
    # the last tile of the gender value おとこ (x 200, y 40): it goes blank, so ATTACK starts at x 16; all three
    # sit right-aligned against the [AT]/[DF]/[DX] tags, which are already English. Values: TILES["gender"].
    "status": dict(scene="m1_status", repeats=[(200, 40, 8, 8)], labels=[head("STATUS")] + [
        (n, (8, y, 32, 8), t, "tiny", {1, 7, 8, 9, 10}, ([7, 8, 9, 10], 1), dict(kind="bg2", right=1))
        for n, y, t in (("atk", 88, "ATTACK"), ("def", 112, "DEFENSE"), ("spd", 136, "SPEED"))] + [
        ("gender", (144, 40, 32, 8), "GENDER", "tiny", {1, 7, 8, 9, 10}, ([7, 8, 9, 10], 1), dict(kind="bg2")),
        # the セレクト tiles (block 2F6828) are the book's SELECT:SEARCH pill too: same rect and text row there
        ("select", (186, 81, 52, 6), "SELECT:SWITCH", "tiny", {1, 2}, (2, None), dict(kind="bg2", dy=-1)),
    ]),
    # セーブ画面 / ロード画面 share the 画面 tiles (x>=64 on the glyph rows): the word sits in x 33-63
    # file 2's panel (y >= 88) repeats file 1's label tiles
    "save": dict(scene="m1_save", repeats=[(0, 88, 240, 72)], labels=[
        head("SAVE", dx=-14, ring_xmax=63, clear_right=1),
        ("file", (12, 20, 43, 11), "FILE", "small", set(range(8, 16)) | {1, 2}, ([10, 12, 14, 15], 1),
         dict(right=1, bgfill=7, dx=-2)),
        ("file2", (12, 92, 43, 11), "FILE", "small", set(range(8, 16)) | {1, 2}, ([10, 12, 14, 15], 1),
         dict(right=1, bgfill=7, dx=-2)),  # x 48-63 (ル + digit) are each panel's own tiles
        ("area", (79, 22, 36, 10), "AREA", "small", {2}, (2, None), dict(left=1)),
        # own tiles only in x 96-127 / 168-207, y 72-79
        ("btl", (96, 72, 32, 8), "BATTLER", "tiny", {1, 7, 8, 9, 10, 11}, ([7, 8, 9, 10, 11], 1),
         dict(kind="bg2")),
        ("ptn", (168, 72, 40, 8), "PARTNER", "tiny", {1, 7, 8, 9, 10, 11}, ([7, 8, 9, 10, 11], 1),
         dict(kind="bg2")),
        ("book", (152, 1, 48, 12), "PROFILES", "small", {1, 7, 8, 9, 10}, ([7, 8, 9, 10], 1),
         dict(kind="bg2")),  # bg2 has its own tiles only in x 152-199 (x 200-215 is a shared blank tile)
    ]),
    "load": dict(scene="m1_load", labels=[head("LOAD", dx=-14, clear_right=1)]),
    # shop: tabs like the item screen's; the アイテム column head is the item screen's tiles (propagated)
    "shop": dict(scene="m2_shop", labels=[
        # each tab's top-left tile is shared with the name-entry buttons (block 2F8AD0): text starts at x0+8
        ("buy", (2, 19, 28, 9), "BUY", "btn", {3, 4, 11, 12, 13}, ([11, 12, 13], 4), dict(left=1, dx=6)),
        ("sell", (34, 19, 28, 9), "SELL", "btn", {3, 4, 11, 12, 13}, ([11, 12, 13], 4), dict(left=1, dx=6)),
        ("exit", (66, 19, 28, 9), "EXIT", "btn", {3, 4, 11, 12, 13}, ([11, 12, 13], 4), dict(left=1, dx=6)),
        ("price", (105, 32, 33, 8), "PRICE", "small", {1, 7, 8, 9, 10}, ([7, 8, 9, 10], 1)),
    ] + [(n, (154, y, w, h), t, "head", {1, 2}, (2, 1)) for n, y, w, h, t in (
        ("money", 19, 45, 12, "MONEY"), ("owned", 44, 45, 12, "OWNED"), ("qty", 76, 45, 12, "QTY"),
        ("total", 107, 58, 13, "TOTAL"))]),
    # name entry: alphabet tabs and the side buttons (same button style as the item tabs)
    "name": dict(scene="m1_name", labels=[
        # top-left tile of every tab/button is shared with the shop tabs (block 2F8AD0): text starts at x0+8
        ("hira", (82, 26, 36, 10), "HIRA", "btn", {3, 4, 11, 12, 13}, ([11, 12, 13], 4), dict(left=1, dx=8)),
        ("kata", (122, 26, 36, 10), "KATA", "btn", {3, 4, 11, 12, 13}, ([11, 12, 13], 4), dict(left=1, dx=8)),
        ("eng", (162, 26, 36, 10), "ABC", "btn", {3, 4, 11, 12, 13}, ([11, 12, 13], 4), dict(left=1, dx=10)),
    ] + [(f"side{i}", (3, 66 + 16 * i, 31, 10), t, "btn", {3, 4, 11, 12, 13}, ([11, 12, 13], 4),
          dict(left=1, dx=7 if len(t) > 2 else 11))
         for i, t in enumerate(["FWD", "BACK", "DEL", "OK"])]),
    # battle item list header pill (bg2; the skill list's スキル pill is the status label copy in 362BD0)
    "bitem": dict(scene="k_ode_item", labels=[
        ("items", (2, 25, 44, 11), "ITEMS", "small", {1, 4, 7, 8, 9, 10}, ([7, 8, 9, 10], 1),
         dict(kind="bg2", left=1, dx=2)),
    ]),
    # battle command list (S4, block 0x361AE4): 4 rows of 8 px, kana drawn with a right/bottom shadow
    "battle": dict(scene="k_ode", labels=[
        ("fight", (48, 123, 37, 8), "FIGHT", "small", {1, 13, 14}, ([13, 14, 14], 1), dict(left=1)),
        ("item", (48, 131, 37, 8), "ITEM", "small", {1, 13, 14}, ([13, 14, 14], 1), dict(left=1)),
        ("swap", (48, 139, 37, 8), "SWAP", "small", {1, 13, 14}, ([13, 14, 14], 1), dict(left=1)),
        ("run", (48, 147, 37, 8), "RUN", "small", {1, 13, 14}, ([13, 14, 14], 1), dict(left=1)),
    ]),
}


# Tiles drawn straight into a block (values the warp scene doesn't show): name -> block, fill indices top to
# bottom, shadow index, [(tile numbers left to right, text)]. Each run of tiles is cleared to 0 and the text centred
# in it, rows 1-6 like the kana (pixfont.SYM symbols, else the tiny caps), with a right/bottom drop shadow.
# gender (status screen, block 2F6658): the game composes each value from 3 tile numbers (EWRAM list at 0x0200C914
# after load): おとこ = 14 15 00, おんな = 14 16 17, ロボ = 18 19 1A, 両性 = 1A 1B 1C. 14 and 1A are each shared by two
# values and 00 is こうげき's こ, so only 15 / 16 17 / 18 19 / 1B 1C are a value's own: ♂, ♀, MECH, BOTH
# (docs/decisions.md D11).
# A run may carry options (tiles, text, {font: "small" (pixfont.G 6 rows) | "tiny", ay: top row, fill: ink rows}).
# Battle popups (OBJ, ink 7 7 7 8 9 a a top to bottom + shadow 1 right/below, like the kana): 2F5C04 is the damage
# sheet (digits 0-9, /, クリティカル!! at tiles 11-17, ミス at 28-29, %UP at 30-32); 362154 (クリティカル!!) and
# 3621F4 (ミス%UP) hold the same tiles for the other battle loader (0x08011BEF).
_POP = dict(fill=[7, 7, 8, 9, 10, 10], font="small")
_MISS = dict(fill=[7, 8, 9, 10, 10], font="tiny", ay=2)
TILES = {
    "gender": dict(block=0x2F6658, fill=[7, 8, 9, 10], shadow=1, runs=[
        ([0x14], ""), ([0x15], "♂"), ([0x16], "♀"), ([0x17], ""), ([0x18, 0x19], "MECH"), ([0x1A], ""),
        ([0x1B, 0x1C], "BOTH")]),
    "popup": dict(block=0x2F5C04, fill=[7, 8, 9, 10], shadow=1, runs=[
        (list(range(11, 18)), "CRITICAL!!", _POP), ([28, 29], "MISS", _MISS)]),
    "crit": dict(block=0x362154, fill=[7, 8, 9, 10], shadow=1, runs=[(list(range(7)), "CRITICAL!!", _POP)]),
    "miss": dict(block=0x3621F4, fill=[7, 8, 9, 10], shadow=1, runs=[([0, 1], "MISS", _MISS)]),
}


# Label strips drawn straight into a block's tiles, keeping their background (a block no warp scene shows on its
# own): name -> block, [(tile numbers left to right, text, ink indices top to bottom, clear indices)], outline index.
# Each run's pixels whose index is in `clear` take the nearest kept pixel of the same row in the run (else of the
# nearest row), then the text is drawn left-aligned in `small` with a 1-px ring, like the screen labels.
# 361AE4 (battle, loaded at 0x06003120 by k_ode): たたかう / アイテム / こうたい / にげる twice, ink d/e and ink f;
# the commands on screen come from 3618EC (SCREENS["battle"]), these are the menu's other states.
_CMD = ["FIGHT", "ITEM", "SWAP", "RUN"]
_CMD_TILES = [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14]]
STRIPS = {
    "battle2": dict(block=0x361AE4, outline=1, runs=[
        ([t + 16 * k for t in ts], text, ink, clear)
        for k, ink, clear in ((0, [13, 14, 14], {1, 13, 14}), (1, [15], {1, 15}))
        for ts, text in zip(_CMD_TILES, _CMD) if all(t + 16 * k < 31 for t in ts)]),
}


def draw_strip(name):
    cfg = STRIPS[name]
    rom = next((ROOT / "rom").glob("*.gba")).read_bytes()
    raw = packed.unpack(rom, cfg["block"])[1]
    new = bytearray(raw)

    def get(t, x, y):
        b = raw[32 * t + 4 * y + x // 2]
        return b >> 4 if x % 2 else b & 15

    for tiles, text, ink, clear in cfg["runs"]:
        w = 8 * len(tiles)
        px = {(x, y): get(tiles[x // 8], x % 8, y) for x in range(w) for y in range(8)}
        val = dict(px)
        for (x, y), v in px.items():
            if v not in clear:
                continue
            for d in range(1, w + 8):
                hit = [px[(xx, y)] for xx in (x - d, x + d) if 0 <= xx < w and px[(xx, y)] not in clear]
                if not hit:  # a row with no kept pixel: nearest row
                    hit = [px[(x, yy)] for yy in (y - d, y + d) if 0 <= yy < 8 and px[(x, yy)] not in clear]
                if hit:
                    val[(x, y)] = hit[0]
                    break
        pts, tw, th = render_mask(text, "pixfont", 6)
        pts = {(x + 1, y + 1) for x, y in pts}
        for x, y in ring(pts):
            val[(x, y)] = cfg["outline"]
        for x, y in pts:
            val[(x, y)] = ink[min(len(ink) - 1, (y - 1) * len(ink) // th)]
        for (x, y), v in val.items():
            if not (0 <= x < w and 0 <= y < 8):
                raise SystemExit(f"{name}: '{text}' pixel ({x},{y}) outside its tiles")
            b = 32 * tiles[x // 8] + 4 * y + (x % 8) // 2
            new[b] = (new[b] & 0x0F) | (v << 4) if x % 2 else (new[b] & 0xF0) | v
    gfx.DIR.mkdir(exist_ok=True)
    out = gfx.DIR / f"{name}_{cfg['block']:06X}.diff"
    out.write_text(gfx.make_diff(raw, bytes(new)), newline="\n")
    from PIL import Image
    n = len(new) // 32
    im = Image.new("L", (16 * 8, (n + 15) // 16 * 8 * 2 + 4), 40)
    for half, data in ((0, raw), (1, new)):
        for t in range(n):
            for y in range(8):
                for x in range(8):
                    b = data[t * 32 + y * 4 + x // 2]
                    im.putpixel(((t % 16) * 8 + x, half * ((n + 15) // 16 * 8 + 4) + (t // 16) * 8 + y),
                                ((b >> 4) if x % 2 else (b & 15)) * 16)
    pv = ROOT / "work" / "gfx" / name
    pv.mkdir(parents=True, exist_ok=True)
    im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(pv / "tiles.png")
    print(f"{name}: {out.name}")


# Twin blocks drawn in another palette (a highlighted button): screen -> [(drawn block, twin block, {index: index})].
# The twin's diff is the drawn block's edit with the indices remapped; refused unless the remap turns the original
# drawn block into the original twin exactly.
HI = {3: 2, 6: 4, 7: 5, 15: 13}
VARIANTS = {"sptn": [(0x2F990C, 0x2F9C08, HI), (0x2F99C0, 0x2F9CBC, HI)]}


def remap(data, m):
    return bytes(m.get(b & 15, b & 15) | m.get(b >> 4, b >> 4) << 4 for b in data)


def draw_tiles(name):
    import pixfont
    cfg = TILES[name]
    rom = next((ROOT / "rom").glob("*.gba")).read_bytes()
    raw = packed.unpack(rom, cfg["block"])[1]
    new = bytearray(raw)
    for tiles, text, *opt in cfg["runs"]:
        opt = opt[0] if opt else {}
        px = {}
        if text:
            font = pixfont.SYM if all(c in pixfont.SYM for c in text) else pixfont.T
            if opt.get("font") == "small":
                font = pixfont.G
            pts, tw, th = pixfont.mask(text, font=font)
            ax, ay = (8 * len(tiles) - tw - 1) // 2, opt.get("ay", 1)
            pts = {(ax + x, ay + y) for x, y in pts}
            for x, y in pts:
                for dx, dy in ((1, 0), (0, 1), (1, 1)):
                    if (x + dx, y + dy) not in pts:
                        px[(x + dx, y + dy)] = cfg["shadow"]
            ink = opt.get("fill", cfg["fill"])
            for x, y in pts:
                px[(x, y)] = ink[min(len(ink) - 1, (y - ay) * len(ink) // th)]
        for k, t in enumerate(tiles):
            o = 32 * t
            new[o:o + 32] = bytes(32)
            for (x, y), v in px.items():
                if not (0 <= x < 8 * len(tiles) and 0 <= y < 8):
                    raise SystemExit(f"{name}: '{text}' pixel ({x},{y}) outside its tiles")
                if x // 8 == k:
                    b = o + y * 4 + (x % 8) // 2
                    new[b] = (new[b] & 0x0F) | (v << 4) if x % 2 else (new[b] & 0xF0) | v
    gfx.DIR.mkdir(exist_ok=True)
    out = gfx.DIR / f"{name}_{cfg['block']:06X}.diff"
    out.write_text(gfx.make_diff(raw, bytes(new)), newline="\n")
    # preview: the block's tiles, 4x
    from PIL import Image
    n = len(new) // 32
    im = Image.new("L", (n * 9, 8), 40)
    for t in range(n):
        for y in range(8):
            for x in range(8):
                b = new[t * 32 + y * 4 + x // 2]
                im.putpixel((t * 9 + x, y), ((b >> 4) if x % 2 else (b & 15)) * 16)
    pv = ROOT / "work" / "gfx" / name
    pv.mkdir(parents=True, exist_ok=True)
    im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(pv / "tiles.png")
    print(f"{name}: {out.name}")


def prefix(screen):
    return ROOT / "work" / "qa" / "ppu" / f"jp_{SCREENS[screen]['scene']}" / f"ppu_{FRAMES - 1:06d}"


def runs(pre):
    """[(vram lo, vram hi, block offset, block-relative lo)] from vramfind.py against work/blocks."""
    cache = pre.with_suffix(".find.txt")
    if not cache.exists():
        # only the blocks this scene loaded (its unpack log), so a duplicate copy elsewhere is never taken
        log = pre.parent / "log.txt"
        if not log.exists():
            raise SystemExit(f"{log}: no unpack log; re-dump the scene (gfxlabel.py dump SCREEN)")
        src = pre.parent / "blocks"
        src.mkdir(exist_ok=True)
        for m in re.finditer(r"unpack src=08([0-9A-F]{6})", log.read_text(errors="replace")):
            f = BLOCKS / f"{m.group(1)}.bin"
            if f.exists() and not (src / f.name).exists():
                (src / f.name).write_bytes(f.read_bytes())
        cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "vramfind.py"),
               str(pre.with_suffix(".vram.bin")), str(src), "--fmt", "gba4"]
        cache.write_text(subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8").stdout)
    # exact: unpack() straight into VRAM (dst 0x06xxxxxx), later loads over earlier ones; kept only where the
    # dumped VRAM still holds that block's bytes. vramfind (first matching copy) only fills what the log misses.
    vram = pre.with_suffix(".vram.bin").read_bytes()
    owner = {}  # VRAM tile -> (block, offset)
    for m in re.finditer(r"unpack src=08([0-9A-F]{6}) dst=06([0-9A-F]{6})",
                         (pre.parent / "log.txt").read_text(errors="replace")):
        b, dst = int(m.group(1), 16), int(m.group(2), 16)
        f = BLOCKS / f"{b:06X}.bin"
        if not f.exists():
            continue
        data = f.read_bytes()
        for k in range(0, len(data) - 31, 32):
            owner[(dst + k) & ~31] = (b, k) if (dst + k) % 32 == 0 else None
    out = []
    for t, v in owner.items():
        if v and 0 <= t < len(vram) - 31 and vram[t:t + 32] == (BLOCKS / f"{v[0]:06X}.bin").read_bytes()[v[1]:v[1] + 32]:
            out.append((t, t + 31, v[0], v[1]))
    have = {lo for lo, *_ in out}
    for m in re.finditer(r"VRAM ([0-9A-F]+)-([0-9A-F]+) .*?([0-9A-F]{6})\.bin ([0-9A-F]+)-", cache.read_text()):
        lo, hi, b, blo = (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16), int(m.group(4), 16))
        for t in range(lo, hi + 1, 32):
            if t not in have:
                out.append((t, t + 31, b, blo + t - lo))
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
    if font in ("pixfont", "pixfont-tiny"):
        import pixfont
        return pixfont.mask(text, font=pixfont.T if font.endswith("tiny") else None)
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


def screens(pre, labels):
    """{kind: Screen} for every label kind: bg (all BGs), obj, bgN (BG N alone, transparent pixels editable)."""
    out = {"bg": gfxscreen.compose(pre, objs=False), "obj": gfxscreen.compose(pre, bgs=False)}
    for lab in labels:
        k = (lab[6] if len(lab) > 6 else {}).get("kind", "bg")
        if k.startswith("bg") and len(k) == 3 and k not in out:
            out[k] = gfxscreen.compose(pre, only=int(k[2]))
    return out


def info(screen):
    pre = prefix(screen)
    full = gfxscreen.compose(pre)
    scrs = screens(pre, SCREENS[screen]["labels"])
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
    scrs = screens(pre, cfg["labels"])
    vram = bytearray(full.vram)
    newnib = {}  # (addr, hi) -> value
    want = {}  # (vram addr, hi, x, y) -> value: the pixels we meant to set
    label_tiles = {}  # label -> VRAM tiles it changes
    rects = []
    for name, (x0, y0, w, h), text, cls, clear, (fill_rgb, ol_rgb), *opt in cfg["labels"]:
        opt = opt[0] if opt else {}
        scr = scrs[opt.get("kind", "bg")]
        rects.append((x0, y0, w, h))
        val = {}
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                s = scr.src[y][x]
                if s and s[4] in clear and "bgfill" in opt:
                    val[(x, y)] = opt["bgfill"]
                elif s and s[4] in clear:
                    # nearest kept pixel; clear_right=1 looks right first (identical result in a tile two
                    # screens share when only the left part differs)
                    # clear_left=1 looks left first (a pill whose right edge is a dark shading column)
                    side = 1 if opt.get("clear_right") else -1 if opt.get("clear_left") else 0
                    order = [(d,) for d in range(1, 64)] if not side else \
                        [(side * d,) for d in range(1, w)] + [(-side * d,) for d in range(1, w)]
                    for (d,) in order:
                        cand = (x - d, x + d) if not side else (x + d,)
                        hit = [xx for xx in cand if x0 <= xx < x0 + w and scr.src[y][xx]
                               and scr.src[y][xx][4] not in clear and (scr.src[y][xx][0] == s[0] or
                                   scr.src[y][xx][0][:3] == s[0][:3] == "obj")]  # a pill of several sprites
                        if hit:
                            val[(x, y)] = scr.src[y][hit[0]][4]
                            break
                    else:  # a row with no kept pixel (a dark stripe): its left-edge index
                        val[(x, y)] = scr.src[y][x0][4]
        c = CLASSES[cls]
        pts, tw, th = render_mask(text, c["font"], opt.get("size", c["size"]), c.get("weight"))
        sh = 1 if c.get("shadow") and ol_rgb is not None else 0  # a drop shadow: 1 px right/below
        ax = (x0 + 1 - sh if opt.get("left") else x0 + w - 1 - tw if opt.get("right")
              else x0 + (w - tw - sh) // 2) + opt.get("dx", 0)
        ay = y0 + (h - th + 1 - 2 * sh) // 2 + opt.get("dy", 0)
        pts = {(ax + x, ay + y) for x, y in pts}
        if c.get("shadow"):  # drop shadow right and below, like the kana on the game's own buttons
            rg = {(x + dx, y + dy) for x, y in pts for dx, dy in ((1, 0), (0, 1), (1, 1))} - pts
        else:
            rg = ring(pts)
        rg = {(x, y) for x, y in rg if x <= opt.get("ring_xmax", 999)} if ol_rgb is not None else set()
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
            want[(addr, hi, x, y)] = v
            if v != old:
                label_tiles.setdefault(name, set()).add(addr & ~31)
        print(f"{name}: '{text}' {tw}x{th} px at {ax},{ay}")
    for (addr, hi), v in newnib.items():
        vram[addr] = (vram[addr] & 0x0F) | (v << 4) if hi else (vram[addr] & 0xF0) | v
    # every pixel that changes must be one we meant to change (a tile repeated elsewhere, in or out of a label)
    for kind, scr in scrs.items():
        for y in range(160):
            for x in range(240):
                s = scr.src[y][x]
                if s and (s[1], s[2]) in newnib and newnib[(s[1], s[2])] != s[4] \
                        and want.get((s[1], s[2], x, y)) != newnib[(s[1], s[2])] \
                        and not any(a <= x < a + w and b <= y < b + h for a, b, w, h in cfg.get("repeats", [])):
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

    def put_tile(off, old, new):
        """A label copy in another block: only where the tile occurs exactly once there."""
        data = alls[off]
        i = data.find(old)
        if i >= 0 and data.find(old, i + 1) < 0:
            block(off)[i:i + 32] = new

    # 1. every changed tile into the block this screen loaded it from, at the offset VRAM came from (a block
    #    can hold the same tile bytes several times: only this copy is the one on screen)
    srcs = {}
    for t0, (old, new) in sorted(tiles.items()):
        at = {(boff, blo + t0 - lo) for lo, hi, boff, blo in rs if lo <= t0 and t0 + 32 <= hi + 1}
        srcs[t0] = {b for b, _ in at}
        if not at:
            raise SystemExit(f"{screen}: VRAM tile {t0:#x} not found in any packed block")
        for off, i in at:
            if alls[off][i:i + 32] != old:
                raise SystemExit(f"{screen}: tile {t0:#x} is not at {off:06X}+{i:X}")
            block(off)[i:i + 32] = new
    # 2. a whole label duplicated in another block (another screen's copy): only when that block holds every
    #    distinctive tile of the label (a shared glyph such as る in すてる / うる must not carry one label's
    #    letters into the other); near-blank tiles never travel
    for name, ts in label_tiles.items():
        dist = [t for t in ts if t in tiles and len(set(tiles[t][0])) >= 5
                and sum(1 for b in tiles[t][0] for v in (b & 15, b >> 4) if v) >= 12]
        if len(dist) < 2:  # one glyph tile is no evidence of the whole label (ア starts アイテム and アソート)
            continue
        cand = None
        for t in dist:
            has = {off for off, data in alls.items() if off not in inner and tiles[t][0] in data}
            cand = has if cand is None else cand & has
        for off in sorted(cand - set().union(*srcs.values())):  # never a block this screen loads itself
            if VERBOSE:
                print(f"  label {name}: copy in block {off:06X}")
            for t in dist:
                put_tile(off, *tiles[t])
    for src, dst, m in VARIANTS.get(screen, []):
        if src not in edits:
            raise SystemExit(f"{screen}: variant source {src:06X} not edited")
        twin = packed.unpack(rom, dst)[1]
        if remap(raws[src], m) != twin:
            raise SystemExit(f"{screen}: {dst:06X} is not {src:06X} remapped")
        raws[dst], edits[dst] = twin, bytearray(remap(edits[src], m))
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
    scr = gfxscreen.compose(pre, objs=kind == "obj", bgs=kind != "obj",
                            only=int(kind[2]) if len(kind) == 3 and kind.startswith("bg") else None)
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
    cmd, names = sys.argv[1], [a for a in sys.argv[2:] if not a.startswith("-")] or sorted(SCREENS) + (
        sorted(TILES) + sorted(STRIPS) if sys.argv[1] == "draw" else [])
    for n in names:
        if n in TILES:
            draw_tiles(n)
        elif n in STRIPS:
            draw_strip(n)
        elif cmd == "dump":
            import ppuscene
            print(ppuscene.dump(SCREENS[n]["scene"], "jp", FRAMES))
        elif cmd == "info":
            info(n)
        else:
            draw(n)


if __name__ == "__main__":
    main()
