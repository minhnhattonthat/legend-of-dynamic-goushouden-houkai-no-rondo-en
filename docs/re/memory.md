# Memory map and free space

## RAM (verified by watches unless marked)
| address | use |
|---|---|
| 0x0201CD20.. | glyph tile buffer (DMA source for text tiles) |
| 0x0201D000..0x0201FFFF | unpacked script file (opening file at 0x0201D66C; message copy by memcpy 0x080CD64C) |
| 0x0201FD50 / 0x0201FE60 | lh5 Huffman tables / stream buffer |
| 0x0300039C, 0x030003A0, 0x03000288 | lh5 source base, position, bytes left |
| 0x03004024 | lh5 bit buffer |
| 0x03004858 | pointer to the active font's charset list |

## Built ROM layout (phase 5, `tools/engine.py`)
- 16 MiB (0x1000000), 0xFF fill past the original 8 MiB. SRAM save: unaffected (boots, saves in phase 8 QA).
- 0x800000..: the script archive (5 root pointers repointed); its old slot 0x104DC0-0x132E74 is free space in BL
  range of the code (+-4 MiB): the VWF hook sits at 0x104DC0 (~0x250 bytes), the rest is free for later hooks.
- Thumb BL reaches only +-4 MiB: code above 0x400000 can't be called with a plain BL from the text code.

## ROM free space
- The ROM is exactly 8 MiB with no 0xFF/0x00 tail. GBA allows growing to 16 MiB (or 32 MiB): new text and code go
  past 0x800000, which needs no trap test. SRAM save, so a larger ROM keeps saves working (check in phase 5).
- Runs of 0xCC padding precede packed blocks (e.g. before 0x312070); small, not worth using.
