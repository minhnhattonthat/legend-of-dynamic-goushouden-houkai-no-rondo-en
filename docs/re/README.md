# RE notes index

ROM: `Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba`, 8 MiB (0x800000), game code `AVDJ`, title `DYNAMIC`,
save type SRAM (`SRAM_V112` at 0x0DE78C), Banpresto / Will, 2003. No earlier fan translation exists (web search
2026-11-15: only ROM sites and the Japanese strategy guide). Each finding is marked **verified** (how) or **guess** (why).

| File | Subsystem |
|---|---|
| `compression.md` | packed-file header, codecs for types 1/2(lh5)/3/0x63 (all decoders verified), asset tables |
| `text.md` | script archive (5,400 messages), menu/item strings, control codes, pointers |
| `font.md` | runtime glyph renderer, charset lists, font descriptor table |
| `memory.md` | RAM buffers and free-space candidates |
| `graphics.md` | graphics-text survey (tile-drawn Japanese); per-block list in `graphics_sweep.tsv` |
| `debug.md` | leftover debug menus, warp hook points, event flags, party records (phase 2 debug tool) |

Tools written in recon: `tools/packed.py` (all packed formats; `tests/test_codecs.py`), `tools/lh5.py`,
`tools/gbalz.py` (BIOS LZ77; 5 blocks only), `tools/scanpacked.py` (find every block), `tools/findtables.py`
(self-relative asset tables from unpack logs), `tools/romcover.py` (uncovered ROM ranges), `tools/gfxsweep.py` +
`tools/sweep_quarters.py` + `tools/sweep_review.sh` + `tools/sweep_merge.py` (static graphics sweep),
`tools/lua/unpacklog.lua` (log/dump every unpack), `tools/lua/watchval.lua` (log nonzero writes with registers).
Phase 3: `tools/archive.py` (script archive read/rebuild, slot split/join), the lh5 encoder in `tools/lh5.py`,
`build.py` (`--verify` identity, `--reencode` encoder test build), `tests/test_identity.py`.

## Gotchas
- `watch.lua` logs the first write per PC, often a clear; use `tools/lua/watchval.lua` to see real values.
- The game copies a whole message file into EWRAM; a read watch on the message buffer during display logged nothing.
- Type-3 blocks copy from before the start of their output (zeros expected); decode with the 0x800-byte zero pad.
- Mashing A from the opening stops in the first free-roam field (~f15000): later screens need the debug tool.
- Mesen Lua can patch the loaded ROM (`emu.write(off, v, emu.memType.gbaPrgRom)`) and set CPU registers
  (`emu.setState({["cpu.r0"]=n})`) from an exec hook: that is how warp.lua drives the debug menus.
- The debug top menu ignores input for ~25 frames after it appears; route presses before that are lost.
- Script archive: an unused message slot has offset 0; file 53 has slots 0..62 only. lh5.decode's byte count is
  exact for these streams (next file offset = start + consumed), so archive.read() checks it per file.
