# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool built, game over reachable; proof run at 240/340 scenes (map_211..map_310 left). Last build: none yet.
- **Done:**
  - Step 0 and phase 1 (see git history and `docs/re/`): ROM pinned, MesenCE 2.2.1, codecs verified, script archive
    and menu strings located, graphics-text survey (`docs/re/graphics.md`).
  - Phase 2 (this session, `docs/re/debug.md`): the game's own debug menus survive. `tools/debug/warp.lua`
    redirects main()'s BL (ROM 0x7E48A) into デバックＭＥＮＵ in emulator memory and picks menu rows / field-test
    map ids by setting registers at hook points; `tools/debug/scenes.txt` (45 named scenes: retail title, new game
    -> name entry, field menu, items, assort, status, save/load, encyclopedia, shop, battle results, battles incl.
    robot battle and skill cut-ins, ending + credits roll, BGM/SE tests) plus `map_NNN` for all 293 non-discarded
    field maps (`tools/debug/maps.tsv`, from `tools/debug/mapnames.py`). `tools/debug/warp_all.py` runs them all in
    parallel, one shot each, `--states` regenerates `work/states/<scene>.mss`. `tools/lua/flagdump.lua` dumps the
    event-flag block for diffs.
  - Game over (session 2): scene `game_over` (warp.lua `wipe` step: party HP 1, random battle in map 257, enemy HP
    pinned, trio dies to enemy hits; `docs/re/debug.md` §Battle state). The GAME OVER screen is already an English
    graphic. Shot: `work/qa/warp_all_go/shots/game_over.png`, state `work/states/game_over.mss`.
  - Proof run `warp_all.py --jobs 2 --frames 3000 --states` (session 2): 239 scenes ok (all 45 named + map_000 ..
    map_210), 0 failed, shots + states regenerated; then Claude Code's low-memory guard killed it while other
    projects' Mesen instances were running. Contact sheets `work/qa/warp_all/sheets/sheet*.png` read by eye: every
    scene shows its screen. Field-test spawn quirks (map loaded, game alive, not a warp bug): map_170 (hotel 3F)
    renders fully black at the spawn point (Start opens the field menu over it), map_168 (hotel 1F) shows only a
    map edge, map_201 (魔王の城Ｄ) the hero on black.
- **Next (phase 2):**
  1. Finish the proof run for the 100 maps left: `python -X utf8 tools/debug/warp_all.py --only "^map_(2(1[1-9]|[2-9]\d)|3\d\d)$" --jobs 1 --frames 3000 --states --out work/qa/warp_all_rest`
     (a separate `--out` keeps the first run's summary.tsv), check memory first (other repos run Mesen too), then
     read its shots in chunks. Any black/empty map gets a note like map_170's. Then phase 2 is done.
  2. Route starts need the branch flags: add when the event scripts are read (phase 4/5). The game has no chapter
     cards.
  Carried from phase 1 (not gating): confirm control codes `\p \s \g !R !W`; glyph bitmap layout behind the font
  descriptor table ~0x0FA690 (phase 5); tie each survey group to its screen by VRAM dump now that warps exist.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
