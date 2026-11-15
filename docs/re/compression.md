# Compression

## Packed-file header (verified: disassembly of 0x08000F58; all three codecs reproduce game output byte for byte)
`unpack(src, dst, ...)` at 0x08000F58 reads a u32 `type << 24 | unpacked_size`, decodes into a temp buffer from
0x08000BE8 (malloc), then copies it to dst at 0x08000FDA (r4 = temp buffer, r5 = size there). Codec: `tools/packed.py`
(`unpack(rom, off)`), tested by `tests/test_codecs.py` against blocks the game decoded (dumps from
`tools/lua/unpacklog.lua` with `DUMP_DIR`; `tools/test_packed.py` checks every dump in `work/qa/*/dumps`).

| type | handler | format |
|---|---|---|
| 1 | 0x08002E64 | u32 `bits` (0..4), then LZSS over **u16 words**: ring N = 0x1000 >> bits words, write pos starts at N - F (F = (8 << bits) + 2), ring zero-filled. Control byte c: c < 0x80 = c literal words; c >= 0x80 = + byte d: absolute ring pos `(c & 0x7F) | (d >> (3+bits)) << 7`, length `(d & ((8<<bits)-1)) + 3` words. c = 0 is a no-op. |
| 2 | 0x08006538 | LHA **-lh5-** bit stream, no LHA header (below) |
| 3 | 0x08001D70 | MSB-first bit stream LZ77: `1`+8 bits literal; `00`+5 bits: copy 1 byte, dist+1; `01`+2 bits k: k<3 len k+2 dist 8 bits; k=3: 4 bits m<15 len m+5 dist 9 bits; m=15: 8 bits m<255 len m+20 dist 10 bits; else len 12 bits + 0x113, dist 11 bits. Copies may reach **before the start of the output** (the game reads whatever precedes its temp buffer; the shipped data expects zeros): `packed.py` pads 0x800 zero bytes. Our encoder must never do this. |
| 0x63 | 0x08000FCE | stored (raw copy) |

Which codec the game uses (unpack log of boot -> title -> name entry -> opening -> first field, 119 distinct
sources): type 1 for most graphics and maps (e.g. 67 of 109 in tour 1), lh5 for the script archive and many tile
sets, type 3 for small blocks (8 seen).

## Where blocks live
- No direct u32 pointer reaches any block. Loaders use self-relative tables: `src = B + u32[B + 8*i]` (e.g. caller
  0x0801BA6A: B = [r4 + 0x48]). Tables found by `tools/findtables.py` from the unpack logs: **0x588DA8** (35 logged
  blocks) and **0x56369C** (31). Others are reached through other structures (to map in phase 3/graphics work).
- `tools/scanpacked.py` finds every block by header scan + decode + overlap resolution -> `work/packed_blocks.json`
  (see the run summary in `docs/re/graphics.md`). `tools/romcover.py` lists ROM ranges no known block covers.

## lh5 (verified: decoded blocks found byte-for-byte in an EWRAM dump)
- Decoder state at 0x030003xx: 0x0300039C source base, 0x030003A0 source position, 0x03000288 bytes left,
  0x03004024 bit buffer; 8 KiB ring at mask 0x1FFF; `len = sym - 253`; NC 510, NP 14, NT 19, CBIT 9, PBIT 4, TBIT 5.
  The read layer at 0x08006ECC / 0x08006F04 streams output and supports skipping (seek by decoding).
- `tools/lh5.py`: `decode(data, off, size)`, `unpack(data, off)`, `encode(raw)` / `pack(raw)` (phase 3: greedy +
  one-step lazy LZ, max distance 8191, package-merge Huffman <= 16 bits, blocks of 0x4000 symbols). Not
  byte-identical to the original packer, but smaller (script archive 153,939 vs 154,060 bytes).
  **verified**: decode(encode(x)) == x for all 54 archive files and all 10,106 scanned packed blocks; a build with
  every archive file re-encoded (`build.py --reencode`) shows the same dialogue as the original at map_290.
- Identity build (`build.py --verify`, `tests/test_identity.py`): unchanged archive files keep their original
  stream, so the rebuilt ROM is byte-identical; edited files are re-encoded.
- **Edited graphics plan**: repack any edited block as type 2 (`lh5.pack`), whatever its original type, since
  unpack() dispatches on the header. **guess** until phase 8 boots one: no caller is known to call a codec
  handler directly. lh5 is smaller in total (4.55 MB vs 5.20 MB over the scanned blocks) but 676 small blocks
  grow, so an edited block may need relocation and its self-relative table entry rewritten.
- BIOS LZ77 (type 0x10 via SWI): only 5 tiny blocks in the ROM.
