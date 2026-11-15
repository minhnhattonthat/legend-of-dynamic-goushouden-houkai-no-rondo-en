# RE notes index

ROM: `Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba`, 8 MiB (0x800000), game code `AVDJ`, title `DYNAMIC`,
save type SRAM (`SRAM_V112` at 0x0DE78C), Banpresto / Will, 2003. No earlier fan translation exists (web search
2026-11-15: only ROM sites and the Japanese strategy guide). Each finding is marked **verified** (how) or **guess** (why).

| File | Subsystem |
|---|---|
| `compression.md` | packed-file header, lh5 codec, types 1/3/0x63 |
| `text.md` | script archive (5,400 messages), menu/item strings, control codes, pointers |
| `font.md` | runtime glyph renderer, charset lists, font descriptor table |
| `memory.md` | RAM buffers and free-space candidates |
| `graphics.md` | graphics-text survey (tile-drawn Japanese) |

Tools written in recon: `tools/lh5.py` (lh5 codec, decode verified), `tools/gbalz.py` (BIOS LZ77; the game barely
uses it: 5 blocks), `tools/lua/watchval.lua` (log nonzero writes with registers).

## Gotchas
- `watch.lua` logs the first write per PC, often a clear; use `tools/lua/watchval.lua` to see real values.
- The game copies a whole message file into EWRAM; a read watch on the message buffer during display logged nothing.
