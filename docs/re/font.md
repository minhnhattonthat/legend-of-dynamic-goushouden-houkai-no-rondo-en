# Font and text drawing

- Glyphs are rendered at run time into an EWRAM tile buffer (0x0201CD20..) and DMA'd to VRAM 0x06000000+ by
  0x0807D0F4 (verified: VRAM write watch). Glyph writer around 0x0800CE5E (writes 4bpp pixel pairs, colours C/D),
  caller 0x0800CD9F; cell setup uses width 12 (or 11) and height 16/24 (0x0800CD8E-0x0800CDA8). **guess**: 12x12 glyphs
  in 16-px rows.
- Character lookup 0x0800AC34(b1, b2): linear search of the charset list at `[0x03004858]` (u16 count, u16 pad, then
  SJIS byte pairs) -> glyph index; 0x0800AC1C returns `font_base + index * glyph_size` from a per-font descriptor.
  (verified by disassembly)
- Charset list of the main font: ROM 0x081EFF98, 1,691 fullwidth glyphs (`　、。，．…０-９Ａ-Ｚａ-ｚ` hiragana, katakana,
  kanji). **No half-width ASCII**: English needs new glyphs (VWF or 8-px half-width cells) in phase 5.
- Font descriptor table near ROM 0x0FA690: entries pointing at charset 0x081EFF98 (three fonts share it), 0x081F0CD4
  (a second, small charset list starting `？！～…いかくともァォオギクグジッノャユロワ瓜王黒紗朱凄生物魔麗`), and 0x080CE130.
  Glyph bitmaps follow around 0x1F0Dxx-0x2056AA (4bpp-looking data). Exact layout: phase 5.
- The name-entry screen has hiragana / katakana / 英語 tabs: the font has fullwidth Latin letters only.
