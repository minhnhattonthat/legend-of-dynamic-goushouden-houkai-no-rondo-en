# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 3. Identity build next (phase 2 done: all 340 debug-tool scenes reached from a cold boot). Last build: none yet.
- **Done:**
  - Step 0 and phase 1 (see git history and `docs/re/`): ROM pinned, MesenCE 2.2.1, codecs verified, script archive
    and menu strings located, graphics-text survey (`docs/re/graphics.md`).
  - Phase 2 (`docs/re/debug.md`): the game's own debug menus survive. `tools/debug/warp.lua` redirects main()'s BL
    (ROM 0x7E48A) into デバックＭＥＮＵ in emulator memory and picks menu rows / field-test map ids by setting
    registers at hook points; `tools/debug/scenes.txt` (47 named scenes: retail title, new game -> name entry, field
    menu, items, assort, status, save/load, encyclopedia, shop, battle results, battles incl. robot battle and skill
    cut-ins, game over, ending + credits roll, BGM/SE tests) plus `map_NNN` for all 293 non-discarded field maps
    (`tools/debug/maps.tsv`). `tools/debug/warp_all.py` runs them, one shot each; `--states` regenerates
    `work/states/<scene>.mss`. `tools/lua/flagdump.lua` dumps the event-flag block for diffs.
  - Proof run, original ROM, `--frames 3000 --states`: 340/340 ok, 0 failed (`work/qa/warp_all/` for the named
    scenes + map_000..210, `work/qa/warp_all_rest/` for map_211..310; contact sheets in `<out>/sheets/`, each read
    by eye). Spawns that look odd but aren't warp bugs are listed in `docs/re/debug.md` §Proof run (map_168, 170,
    201, 267 = 黒ＢＧ, the 15 identical bathroom variants 218..232, map_290 opens a dialogue on entry).
- **Next (phase 3, `references/pipeline.md` §Identity):** write `build.py` (rom check first, then unpack + repack
  every edited structure with no edits: the lh5 script archive, menu string tables, packed graphics) and a test
  that the rebuilt `build/goushouden_en.gba` is byte-identical to the original; wire the test into `tools/check.py`.
  Later, not gating: route starts need the branch flags (add when event scripts are read, phase 4/5; the game has no
  chapter cards). Carried from phase 1: confirm control codes `\p \s \g !R !W`; glyph bitmap layout behind the font
  descriptor table ~0x0FA690 (phase 5); tie each survey group to its screen by VRAM dump.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
