# Compression

## Packed-file header (verified: disassembly of 0x08000F58, decoded blocks match RAM)
`unpack(src, dst?)` at 0x08000F58 reads a u32 `type << 24 | unpacked_size` and dispatches:

| type | handler | format |
|---|---|---|
| 1 | 0x08002E64 | unknown codec with a bit-width parameter (r3 <= 4); **guess**: dictionary/LZW-style. Not yet decoded. |
| 2 | 0x08006538 | LHA **-lh5-** bit stream, no LHA header (see below) |
| 3 | 0x08001D70 | unknown bit-level LZ (5-bit short distance, 2/4-bit lengths); not yet decoded |
| 0x63 | 0x08000FCE | stored (raw copy) |

Header candidates in the ROM (4-aligned, size 16..0x40000): type1 23,609, type2 8,430, type3 9,587, raw 315 (most are
false positives). Of the type-2 candidates, 1,410 decode cleanly with `tools/lh5.py`; list in `work/lh5_blocks.json`
(regenerate with a scan). By 1 MiB bank: 0x0 2, 0x1 31, 0x2 429, 0x3 436, 0x4 300, 0x5 44, 0x6 74, 0x7 94.
**Next**: log every call to 0x08000F58 (src, header) during the screen tour to learn which types the game really uses.

## lh5 (verified: decoded blocks found byte-for-byte in an EWRAM dump)
- Decoder state at 0x030003xx: 0x0300039C source base, 0x030003A0 source position, 0x03000288 bytes left,
  0x03004024 bit buffer; 8 KiB ring at mask 0x1FFF; `len = sym - 253`; NC 510, NP 14, NT 19, CBIT 9, PBIT 4, TBIT 5.
  The read layer at 0x08006ECC / 0x08006F04 streams output and supports skipping (seek by decoding).
- `tools/lh5.py`: `decode(data, off, size)`, `unpack(data, off)`. The encoder is not written yet (phase 3); the
  identity test must re-encode the script archive (or keep original streams for unchanged files).
- BIOS LZ77 (type 0x10 via SWI): only 5 tiny blocks in the ROM.
