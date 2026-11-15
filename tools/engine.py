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
"""
import struct

ROM_SIZE = 0x1000000
NEW_ARCHIVE = 0x800000
FREE = (0x104DC0, 0x132E74)   # the archive's old slot

CHARSET = 0x1EFF98            # u16 count, u16 pad, count x SJIS pair (shared by the 8, 12 and 16 px fonts)
FONT12 = 0x1F0D18             # 1bpp, 12 rows of big-endian u16 (bit 15 = column 0), 24 bytes per glyph
ASCII_MAP = 0x0FA6A0          # 16 pointers (per high nibble) to 16 SJIS pairs each

# (offset of `adds r0, r7, #0`, ADV) in the printer: every glyph advance (docs/re/font.md)
ADV_SITES = (
    (0x0F126, 0x0C), (0x0F144, 0x10), (0x0F290, 0x0A), (0x0F2AE, 0x0E),
    (0x0F438, 0x0C), (0x0F43E, 0x10), (0x0F45C, 0x12),
    (0x0F486, 0x0C), (0x0F49E, 0x0C), (0x0F4BE, 0x0C),
    (0x0F59C, 0x10), (0x0F5A6, 0x14), (0x0F5C4, 0x16),
    (0x0F618, 0x10), (0x0F630, 0x10), (0x0F826, 0x10),
)
SPACE_ADV = 4
GAP = 1                       # blank columns after the ink


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


COMMON = """
    push {r1, r2, r3}
    add r1, sp, #0x28
    ldrb r2, [r1]
    ldrb r3, [r1, #1]
    subs r2, #0x81
    cmp r2, #1
    bhi done
    lsls r2, r2, #8
    adds r3, r2, r3
    mov r1, r6
    adds r1, #0xE0
    ldr r1, [r1]
    lsls r1, r1, #4
    adds r1, r1, r6
    ldr r1, [r1, #4]
    cmp r1, #12
    bne done
    ldr r1, table
    ldrb r1, [r1, r3]
    subs r0, r0, r1
done:
    adds r0, r0, r7
    pop {r1, r2, r3}
    bx lr
    .align 2
table:
"""


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
    cur = FREE[0]
    stubs = {}
    imms = sorted({imm for _, imm in ADV_SITES})
    stub_len = 4 * len(imms)
    common_at = cur + stub_len
    code = bytearray()
    for k, imm in enumerate(imms):
        at = cur + 4 * k
        stubs[imm] = at
        code += thumb("movs r0, #%d\nb 0x%X" % (imm, 0x08000000 + common_at), at)
    code += thumb(COMMON, common_at)
    while (cur + len(code)) % 4:
        code += b"\0"
    table_at = cur + len(code) + 4  # the literal word `table` follows the code
    code += struct.pack("<I", 0x08000000 + table_at)
    delta = bytearray(512)
    for pair, (_, _, adv) in glyphs.items():
        if pair[0] in (0x81, 0x82):
            delta[(pair[0] - 0x81) << 8 | pair[1]] = 12 - adv
    code += delta
    put(cur, bytes(code), "vwf hook")
    for site, imm in ADV_SITES:
        want = struct.pack("<HH", 0x1C38, 0x3000 | imm)
        assert bytes(orig[site:site + 4]) == want, "advance site %X: %s" % (site, orig[site:site + 4].hex())
        put(site, bl(site, stubs[imm]), "vwf site +%d" % imm)
    return cur + len(code)
