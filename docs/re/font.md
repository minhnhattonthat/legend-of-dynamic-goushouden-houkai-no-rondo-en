# Font and text drawing

- Glyphs are rendered at run time into an EWRAM tile buffer (0x0201CD20..) and DMA'd to VRAM 0x06000000+ by
  0x0807D0F4 (verified: VRAM write watch).
- Character lookup 0x0800AC34(b1, b2): linear search of the charset list at `[0x03004858]` (u16 count, u16 pad, then
  SJIS byte pairs) -> glyph index; 0x0800AC1C(window, index) returns `[window + mode*16] + index * [window + mode*16 + 0xC]`.
  (verified by disassembly)
- Charset list of the main font: ROM 0x081EFF98, 1,691 fullwidth glyphs (`　、。，．…０-９Ａ-Ｚａ-ｚ` hiragana, katakana,
  kanji), shared by the 8, 12 and 16 px fonts. A second, small charset 0x081F0CD4 (`？！～…いかくとも...`) goes with
  the 16 px font. Descriptor table 0x080FA690: [0..2] main charset, [3] small charset.
- The name-entry screen has hiragana / katakana / 英語 tabs: the font has fullwidth Latin letters only.

## Text window struct (verified: RAM dump of the dialogue window 0x0201B900 while drawing, phase 5)
| offset | meaning |
|---|---|
| +mode*16 + 0 / 4 / 8 / 0xC | font base, cell width, cell height, bytes per glyph for font mode 1..4 |
| mode 1 | 0x081FABA0, 8x8, 8 bytes (1bpp 8x8, same charset) |
| mode 2 | 0x081F0D18, 12x12, 24 bytes: 12 rows of big-endian u16, bit 15 = column 0 (**the dialogue font**) |
| mode 3 | 0x081FE078, 12x12, 24 bytes (286 glyphs) |
| mode 4 | 0x081FFB48, 16x16, 32 bytes |
| +0xAC / +0xB0 | cursor column (tiles, = pen x / 8) / row |
| +0xD8 / +0xDC | pen x / y in pixels (loaded into r7 by the printer) |
| +0xE0 | current font mode (2 in dialogue) |

## Printer 0x0800E898 (one call per character; verified by disassembly + Lua exec logs)
- Reads b1 at `[sp+0x1C]`. `!W` / `!R` set [win+0xC8] = 2 / 4 (text colour/style **guess**), CR/LF new line,
  `\x1b[` starts an ANSI-like escape (`ESC[x;yH` positions the pen in 8-px units, numbers parsed at 0x0800EF3E).
- Double-byte lead (0x81-0x9F, 0xE0-0xFC) reads b2; **any other byte goes through 0x0800FE5C**, which maps it to
  a fullwidth pair with the table at 0x080FA6A0 (16 row pointers to the rows at ROM 0x0CE010-0x0CE154): `A` -> `Ａ`,
  `'` -> `’`, `"` -> `”`, space and `` ` `` -> `　`, half-width kana -> fullwidth katakana. So **English is plain
  ASCII, one byte per char**, and draws with the existing fullwidth Latin glyphs.
- Per font mode and style it calls one of ~15 glyph writers (0x0800CCAC in dialogue), then advances the pen:
  `adds r0, r7, #0; adds r0, #ADV` (ADV 12 for the 12-px font; 0x10/0x12/... for outlined styles and other fonts).
  The glyph writer ORs a 1bpp glyph in at any pixel x (spike: ADV 7 overlapped glyphs cleanly), so a VWF only needs
  the advance changed.

## VWF (phase 5, `tools/engine.py`; verified in game: `Abc Hello ijl` in the map_290 box)
- The 94 glyphs ASCII maps to are moved to column 0 in the 12-px font; advance = ink width + 1 (space 4).
- The 16 advance sites in the printer (`engine.ADV_SITES`) become `bl stub_ADV` (stubs + common code + 512-byte
  delta table at 0x104DC0, the archive's old slot). The common code subtracts `12 - width` for those glyphs when
  the window's cell width ([win + mode*16 + 4]) is 12; other fonts and Japanese glyphs keep their advance.
- Fullwidth Latin input (player names typed on the 英語 tab, fields encoded with `sjis.fullwidth`) gets the same
  widths, because the delta table is keyed by the SJIS pair.
- **Plain ASCII does not draw with the 12-px font.** In dialogue it switches the window to font mode 3, the
  half-width font 0x081FE078 (286 glyphs, same charset index, ink <= 5 px, advance 6), so the 12-px VWF above only
  covers fullwidth input (names typed on the 英語 tab, `extract.FULLWIDTH` fields). Verified with
  `tools/lua/advprobe.lua` at map_290: mode 3, pair at [sp+0x1C..0x1D] at every half-width advance.
- **Half-width VWF** (`engine.HALF_SITES`, verified in game with a torture line): its 4 advance sites are
  `adds r0, r7, #6; ldr rX, [sp, #0x38]` at 0x0F288, 0x0F300, 0x0F316 (rX = r3), 0x0F352; each becomes `bl` to a
  stub that returns pen + 6 - HDELTA[pair] and reloads rX. The ASCII glyphs move to column 0, advance = ink + 1,
  space 3; digits keep 6 px (number columns). Kana in a mode-3 line (a `{p}` name) still advance 12.
- **Second printer 0x0800E3D0** (menus and lists; calls the same glyph writers, `engine.PRINTERS` "p2"): window r5,
  pen r6, the drawn pair at [sp+0..1], advance sites `adds r0, r6, #0; adds r0, #8/#0xC/#0x10` and half-width
  `adds r0, r6, #6; ldr rX, [sp, #0xC]`. The item menu (m1_item) and party list draw ASCII with the **8x8 font**
  (font mode 1, cell width 8) through it. Verified: no site of printer 0x0800E898 fires in the item menu.
- **8-px VWF** (verified in m1_item): the 8x8 font's ASCII glyphs move to column 0 (advance ink + 1, space 3), the
  common hook subtracts DELTA8 when the window's cell width is 8. Both printers' 8-px sites are hooked.
- Digits are tabular in the 8-px and half-width fonts: one advance (widest digit + 1: 7 and 6 px), each centred.
- Glyph torture line (map_290): every printable ASCII draws; `\` is the yen sign and `` ` `` a blank (SJIS), so
  the lint bans both. `"` and `'` draw as ” and ’.
- Text is not clipped by the box: a long line draws over the border up to x=232 (24 tiles from x=40), then stops.
- Not yet covered: the 8 and 16 px fonts (other window modes), and draw paths outside 0x0800E898 (the other
  callers of 0x0800AC34: 0x0800B6F2..0x0800DFD4 are inside the printer's glyph writers; menus still to check in
  the marker tour).
