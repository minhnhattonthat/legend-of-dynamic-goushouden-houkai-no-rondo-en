"""engine.py: code and font patches for English (phase 5, docs/re/font.md "VWF").

  apply(rom, put)   expand the ROM, relocate the script archive's pointers, write the VWF hook and the font changes
  widths()          {sjis pair: advance in px} for the 12-px font (the lint's width table)

ROM layout after apply():
  0x000000-0x7FFFFF  original game; the archive's old slot 0x104DC0-0x132E74 becomes free space (FREE), in BL
                     range (+-4 MiB) of the text code, so the VWF hook lives there
  0x800000-          the script archive (NEW_ARCHIVE), then 0xFF up to ROM_SIZE

VWF (verified in game, phase 5): the text printer 0x0800E898 keeps the pen x in r7 (pixels) and after each glyph
does `adds r0, r7, #0; adds r0, #ADV` (ADV = 12 for the 12-px font, more for outlined styles). The glyph writer
ORs a 1bpp glyph in at any pixel x. Each such pair becomes `bl stub_ADV`; the stub loads ADV and the common code
subtracts DELTA[(b1 - 0x81) << 8 | b2] (12 - width) when the window's current font is 12 px wide, for the glyphs
the ASCII bytes map to (0x0800FE5C, table 0x080FA6A0: 'A' -> Ａ 8260 ...). The char pair is at the printer's
[sp + 0x1C], the window in r6, the font mode at [window + 0xE0], the cell width at [window + mode * 16 + 4].
The fullwidth Latin glyphs of the 12-px font are moved to column 0, so the narrow advance packs them.

Phase 5 later: plain ASCII actually draws with the half-width font (mode 3, advance 6: HALF hooks, HDELTA) in
dialogue and with the 8x8 font (mode 1, advance 8: DELTA8 in the common hook) in menus, through two printers
(PRINTERS: 0x0800E898 dialogue, 0x0800E3D0 menus/lists). All three fonts get their ASCII glyphs moved to column 0.
"""
import struct

ROM_SIZE = 0x1000000
NEW_ARCHIVE = 0x800000
FREE = (0x104DC0, 0x132E74)   # the archive's old slot

CHARSET = 0x1EFF98            # u16 count, u16 pad, count x SJIS pair (shared by the 8, 12 and 16 px fonts)
FONT12 = 0x1F0D18             # 1bpp, 12 rows of big-endian u16 (bit 15 = column 0), 24 bytes per glyph
ASCII_MAP = 0x0FA6A0          # 16 pointers (per high nibble) to 16 SJIS pairs each

# The two text printers (docs/re/font.md): window register, pen register, the drawn SJIS pair's stack offset,
# the stack offset the half-width sites reload, the advance sites `adds r0, PEN, #0; adds r0, #ADV` as
# (offset, ADV) and the half-width sites `adds r0, PEN, #6; ldr rX, [sp, #RET]` as (offset, X).
PRINTERS = (
    dict(name="p1", at=0x0E898, win=6, pen=7, pair=0x1C, ret=0x38,   # dialogue
         adv=((0x0F126, 0x0C), (0x0F144, 0x10), (0x0F290, 0x0A), (0x0F2AE, 0x0E),
              (0x0F438, 0x0C), (0x0F43E, 0x10), (0x0F45C, 0x12),
              (0x0F486, 0x0C), (0x0F49E, 0x0C), (0x0F4BE, 0x0C),
              (0x0F59C, 0x10), (0x0F5A6, 0x14), (0x0F5C4, 0x16),
              (0x0F618, 0x10), (0x0F630, 0x10), (0x0F826, 0x10),
              (0x0F120, 0x08), (0x0F16C, 0x08), (0x0F180, 0x08), (0x0F1A4, 0x08)),
         half=((0x0F288, 1), (0x0F300, 1), (0x0F316, 3), (0x0F352, 1))),
    dict(name="p2", at=0x0E3D0, win=5, pen=6, pair=0x00, ret=0x0C,   # menus, lists (item menu: 8-px font)
         adv=((0x0E5DA, 0x08), (0x0E5F2, 0x08), (0x0E612, 0x08),
              (0x0E72A, 0x0C), (0x0E73E, 0x0C), (0x0E762, 0x0C),
              (0x0E7CA, 0x10), (0x0E7E2, 0x10), (0x0E820, 0x10)),
         half=((0x0E676, 1), (0x0E68C, 2), (0x0E6C8, 2))),
)
ADV_SITES = tuple(s for p in PRINTERS for s in p["adv"])

# The 8x8 font (window font mode 1, cell width 8): menus, item and party lists. 8 bytes per glyph, bit 7 = column 0.
FONT8 = 0x1FABA0
EIGHT_ADV = 8
EIGHT_SPACE_ADV = 3
EIGHT_MONO = "0123456789"
SPACE_ADV = 4
GAP = 1                       # blank columns after the ink

# The half-width font (window font mode 3): 286 glyphs, same charset index and 24-byte layout as FONT12, at most
# 5 px of ink, advance 6. Plain ASCII in dialogue and menus draws with it (verified: tools/lua/advprobe.lua at
# map_290, mode 3, pair at [sp + 0x1C]). Its advance sites are `adds r0, r7, #6; ldr rX, [sp, #0x38]`.
FONT6 = 0x1FE078
FONT6_COUNT = 286
HALF_SITES = tuple(s for p in PRINTERS for s in p["half"])
HALF_ADV = 6
HALF_SPACE_ADV = 3
HALF_MONO = "0123456789"      # digits keep the fixed 6 px so number columns still line up


def ascii_pairs(rom):
    """{ascii byte: sjis pair} for 0x20..0x7E, from the game's own table."""
    out = {}
    for c in range(0x20, 0x7F):
        p = struct.unpack_from("<I", rom, ASCII_MAP + 4 * (c >> 4))[0] - 0x08000000
        out[c] = bytes(rom[p + 2 * (c & 15):p + 2 * (c & 15) + 2])
    return out


def glyph_index(rom):
    n = struct.unpack_from("<H", rom, CHARSET)[0]
    return {bytes(rom[CHARSET + 4 + 2 * i:CHARSET + 6 + 2 * i]): i for i in range(n)}


def glyph_rows(rom, i):
    return list(struct.unpack_from(">12H", rom, FONT12 + 24 * i))


def latin_glyphs(rom):
    """-> {pair: (index, rows shifted to column 0, advance)} for every pair an ASCII byte maps to."""
    idx = glyph_index(rom)
    out = {}
    for c, pair in ascii_pairs(rom).items():
        if pair in out:
            continue
        i = idx[pair]
        rows = glyph_rows(rom, i)
        ink = 0
        for r in rows:
            ink |= r
        if not ink:
            out[pair] = (i, rows, SPACE_ADV)
            continue
        lo = next(b for b in range(16) if ink >> (15 - b) & 1)
        hi = max(b for b in range(16) if ink >> (15 - b) & 1)
        out[pair] = (i, [(r << lo) & 0xFFFF for r in rows], min(12, hi - lo + 1 + GAP))
    return out


def widths(rom):
    """{sjis pair: advance px} for the glyphs English uses (12-px font); anything else advances 12."""
    return {p: adv for p, (_, _, adv) in latin_glyphs(rom).items()}


def pack_glyphs(rom, read, bits, adv0, space_adv, mono_chars):
    """-> {pair: (index, rows with the ink moved to column 0, advance)} for every ASCII pair of one font.
    read(i) -> the glyph's rows (bit `bits - 1` = column 0). Digits (mono_chars) are tabular: one advance, the
    widest digit's ink + GAP, each centred in it, so number columns still line up."""
    idx = glyph_index(rom)
    pairs = ascii_pairs(rom)
    mono = {pairs[ord(c)] for c in mono_chars}
    mask = (1 << bits) - 1

    def extent(rows):
        ink = 0
        for r in rows:
            ink |= r
        if not ink:
            return None
        cols = [b for b in range(bits) if ink >> (bits - 1 - b) & 1]
        return cols[0], cols[-1]

    tab = max(hi - lo + 1 for lo, hi in (extent(read(idx[p])) for p in mono)) + GAP
    out = {}
    for c, pair in pairs.items():
        if pair in out:
            continue
        i = idx[pair]
        rows = read(i)
        ext = extent(rows)
        if ext is None:
            out[pair] = (i, rows, space_adv)
            continue
        lo, hi = ext
        if pair in mono:
            to = (tab - GAP - (hi - lo + 1)) // 2
            out[pair] = (i, [((r << lo) & mask) >> to for r in rows], tab)
        else:
            out[pair] = (i, [(r << lo) & mask for r in rows], min(adv0, hi - lo + 1 + GAP))
    return out


def half_glyphs(rom):
    """-> {pair: (index, rows shifted to column 0, advance)} in the half-width font for every ASCII pair."""
    def read(i):
        assert i < FONT6_COUNT, "glyph %d past the half-width font" % i
        return list(struct.unpack_from(">12H", rom, FONT6 + 24 * i))
    return pack_glyphs(rom, read, 16, HALF_ADV, HALF_SPACE_ADV, HALF_MONO)


def eight_glyphs(rom):
    """-> {pair: (index, 8 row bytes shifted to column 0, advance)} in the 8x8 font for every ASCII pair."""
    return pack_glyphs(rom, lambda i: list(rom[FONT8 + 8 * i:FONT8 + 8 * i + 8]), 8, EIGHT_ADV, EIGHT_SPACE_ADV,
                       EIGHT_MONO)


def eight_widths(rom):
    """{sjis pair: advance px} in the 8x8 menu font; others advance 8."""
    return {p: adv for p, (_, _, adv) in eight_glyphs(rom).items()}


def half_widths(rom):
    """{sjis pair: advance px} in the half-width font (what plain ASCII text draws with); others advance 6."""
    return {p: adv for p, (_, _, adv) in half_glyphs(rom).items()}


def bl(src, dst):
    """Thumb BL at ROM offset src to ROM offset dst."""
    off = dst - (src + 4)
    if not -0x400000 <= off < 0x400000:
        raise ValueError("BL %X -> %X out of range" % (src, dst))
    return struct.pack("<HH", 0xF000 | (off >> 12) & 0x7FF, 0xF800 | (off >> 1) & 0x7FF)


def thumb(src, base):
    from keystone import KS_ARCH_ARM, KS_MODE_THUMB, Ks
    enc, _ = Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm(src, 0x08000000 + base)
    return bytes(enc)


# Common code of the `bl stub_ADV` sites (r0 = ADV on entry): subtract DELTA12 or DELTA8 [(b1 - 0x81) << 8 | b2]
# when the window's current font is 12 or 8 px wide, add the pen. Called by BL, so sp is the printer's: the pair is
# at [sp + PAIR] (+12 after the push).
COMMON = """
    push {r1, r2, r3}
    add r1, sp, #%(pair)d
    ldrb r2, [r1]
    ldrb r3, [r1, #1]
    subs r2, #0x81
    cmp r2, #1
    bhi done
    lsls r2, r2, #8
    adds r3, r2, r3
    mov r1, r%(win)d
    adds r1, #0xE0
    ldr r1, [r1]
    lsls r1, r1, #4
    adds r1, r1, r%(win)d
    ldr r1, [r1, #4]
    cmp r1, #12
    beq w12
    cmp r1, #8
    bne done
    ldr r1, t8
    b look
w12:
    ldr r1, t12
look:
    ldrb r1, [r1, r3]
    subs r0, r0, r1
done:
    adds r0, r0, r%(pen)d
    pop {r1, r2, r3}
    bx lr
    .align 2
t8:
    .byte %(t8)s
t12:
    .byte %(t12)s
"""


# Replaces `adds r0, PEN, #6; ldr rX, [sp, #RET]`: r0 = pen + 6 - HDELTA[pair], rX = [sp, #RET].
HALF = """
    push {r1, r2, r3}
    add r2, sp, #%(pair)d
    ldrb r3, [r2, #1]
    ldrb r2, [r2]
    movs r0, #0
    subs r2, #0x81
    cmp r2, #1
    bhi hdone
    lsls r2, r2, #8
    adds r3, r2, r3
    ldr r2, th
    ldrb r0, [r2, r3]
hdone:
    negs r0, r0
    adds r0, #6
    adds r0, r0, r%(pen)d
    pop {r1, r2, r3}
    ldr r%(reg)d, [sp, #%(ret)d]
    bx lr
    .align 2
th:
    .byte %(th)s
"""


# Cursor x clamp (phase 5, verified in game): set_cursor 0x0800FD08(window, x, y) stores x as the line start pen
# ([w+0xD8]) and its tile column / sub-pixel ([w+0xAC], [w+0xD0]); it clamps y at 0 but not x. Callers that centre a
# line pass (width - text) / 2, negative for a line wider than its window, and the glyph blitter then writes before
# the printer's 512-byte malloc'd glyph buffer, over the next heap header (game_over on the marker build: the battle
# message's long text corrupted the free list and the next malloc spun in the out-of-memory trap 0x08000C82).
# `mov sb, r1; mov r8, r2` at its entry becomes a BL to: clamp r1 at 0, then the same two moves.
CURSOR_SITE = 0x0FD14
CURSOR_ORIG = "mov r9, r1\nmov r8, r2"
CLAMP = """
    cmp r1, #0
    bge keep
    movs r1, #0
keep:
    mov r9, r1
    mov r8, r2
    bx lr
"""


# List field padding (phase 8, shop sell list showed "Remedy   e"): the wrapper 0x0800E87C(window, n, str) sets
# [w+0x10C] = n (8 for item names) and printer p2 then pads the string with 0x8140 spaces while a character count
# ([sp+0x14], n - 1 minus one per glyph) stays >= 0: n cells of 8 px for Japanese. Under the VWF a space advances 3 px
# and ASCII names are up to 13 glyphs, so a shorter name left the end of the longer one it replaced. The check
# `ldr r2, [sp, #0x14]; cmp r2, #0` before `blt done` at PAD_SITE becomes a BL that sets the flags from
# (line start [w+0xD8] + 8 * n) - pen - 1 instead: pad while the pen is left of the field's Japanese width. Each pad
# blits an 8-px cell, so the cleared span ends 5-7 px past 8 * n (69 px for items: windows.json item_list).
PAD_SITE = 0x0E844
PAD_ORIG = "ldr r2, [sp, #0x14]\ncmp r2, #0"
PAD = """
    push {r0, r1}
    movs r1, #0x86
    lsls r1, r1, #1
    ldr r1, [r5, r1]
    lsls r1, r1, #3
    movs r0, #0xD8
    ldr r0, [r5, r0]
    adds r1, r1, r0
    subs r2, r1, r6
    subs r2, #1
    pop {r0, r1}
    bx lr
"""


def word_bytes(off):
    return ", ".join(str(b) for b in struct.pack("<I", 0x08000000 + off))


def delta_table(glyphs, adv0):
    out = bytearray(512)
    for pair, (_, _, adv) in glyphs.items():
        if pair[0] in (0x81, 0x82):
            out[(pair[0] - 0x81) << 8 | pair[1]] = adv0 - adv
    return bytes(out)


def apply(rom, put, orig):
    """rom: bytearray of the full original; put(off, data, by) logs and writes. Returns the free-space cursor."""
    if len(rom) < ROM_SIZE:
        rom.extend(b"\xff" * (ROM_SIZE - len(rom)))
    # 1. archive root pointers (the archive bytes are written at NEW_ARCHIVE by build.py)
    import archive
    for site in archive.POINTER_SITES:
        assert struct.unpack_from("<I", orig, site)[0] == 0x08000000 + archive.BASE, hex(site)
        put(site, struct.pack("<I", 0x08000000 + NEW_ARCHIVE), "archive ptr")
    # 2. font: Latin glyphs to column 0
    glyphs = latin_glyphs(orig)
    for pair, (i, rows, adv) in sorted(glyphs.items(), key=lambda kv: kv[1][0]):
        data = struct.pack(">12H", *rows)
        if data != bytes(orig[FONT12 + 24 * i:FONT12 + 24 * i + 24]):
            put(FONT12 + 24 * i, data, "font12 %s" % pair.hex())
    # 3. VWF hook in the archive's old slot
    # (the 8-px and half-width fonts: ASCII glyphs to column 0 too)
    eights, halves = eight_glyphs(orig), half_glyphs(orig)
    for pair, (i, rows, adv) in sorted(eights.items(), key=lambda kv: kv[1][0]):
        if bytes(rows) != bytes(orig[FONT8 + 8 * i:FONT8 + 8 * i + 8]):
            put(FONT8 + 8 * i, bytes(rows), "font8 %s" % pair.hex())
    for pair, (i, rows, adv) in sorted(halves.items(), key=lambda kv: kv[1][0]):
        data = struct.pack(">12H", *rows)
        if data != bytes(orig[FONT6 + 24 * i:FONT6 + 24 * i + 24]):
            put(FONT6 + 24 * i, data, "font6 %s" % pair.hex())
    # 3. VWF hooks in the archive's old slot: the delta tables, then per printer its stubs, common code and
    #    half-width stubs; every advance site becomes a BL
    cur = FREE[0]
    tables = {}
    for name, data in (("t12", delta_table(glyphs, 12)), ("t8", delta_table(eights, EIGHT_ADV)),
                       ("th", delta_table(halves, HALF_ADV))):
        tables[name] = word_bytes(cur)
        put(cur, data, "vwf delta %s" % name)
        cur += len(data)
    for p in PRINTERS:
        imms = sorted({imm for _, imm in p["adv"]})
        common_at = cur + 4 * len(imms)
        code = bytearray()
        stubs = {}
        for k, imm in enumerate(imms):
            stubs[imm] = cur + 4 * k
            code += thumb("movs r0, #%d\nb 0x%X" % (imm, 0x08000000 + common_at), cur + 4 * k)
        code += thumb(COMMON % dict(p, pair=p["pair"] + 12, **tables), common_at)
        while len(code) % 4:
            code += b"\0"
        half = {}
        for reg in sorted({r for _, r in p["half"]}):
            half[reg] = cur + len(code)
            code += thumb(HALF % dict(p, pair=p["pair"] + 12, reg=reg, **tables), cur + len(code))
            while len(code) % 4:
                code += b"\0"
        put(cur, bytes(code), "vwf hook %s" % p["name"])
        cur += len(code)
        for site, imm in p["adv"]:
            want = struct.pack("<HH", 0x1C00 | p["pen"] << 3, 0x3000 | imm)
            assert bytes(orig[site:site + 4]) == want, "advance site %X: %s" % (site, orig[site:site + 4].hex())
            put(site, bl(site, stubs[imm]), "vwf %s site +%d" % (p["name"], imm))
        for site, reg in p["half"]:
            want = struct.pack("<HH", 0x1D80 | p["pen"] << 3, 0x9800 | reg << 8 | p["ret"] // 4)
            assert bytes(orig[site:site + 4]) == want, "half site %X: %s" % (site, orig[site:site + 4].hex())
            put(site, bl(site, half[reg]), "vwf %s half site r%d" % (p["name"], reg))
    # 4. cursor x clamp (CURSOR_SITE); the flags it sets are overwritten by the `movs r0, #8` that follows the site
    want = thumb(CURSOR_ORIG, CURSOR_SITE)
    assert bytes(orig[CURSOR_SITE:CURSOR_SITE + 4]) == want, "cursor site: %s" % orig[CURSOR_SITE:CURSOR_SITE + 4].hex()
    code = thumb(CLAMP, cur)
    put(cur, code, "cursor x clamp")
    put(CURSOR_SITE, bl(CURSOR_SITE, cur), "cursor x clamp site")
    cur += (len(code) + 3) & ~3
    # 5. list padding by width (PAD_SITE)
    want = thumb(PAD_ORIG, PAD_SITE)
    assert bytes(orig[PAD_SITE:PAD_SITE + 4]) == want, "pad site: %s" % orig[PAD_SITE:PAD_SITE + 4].hex()
    code = thumb(PAD, cur)
    put(cur, code, "list pad by width")
    put(PAD_SITE, bl(PAD_SITE, cur), "list pad by width site")
    cur += (len(code) + 3) & ~3
    return cur
