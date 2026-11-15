# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool built; full proof run (every scene, one shot each) still to finish. Last build: none yet.
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
  - Proven with shots so far: all 45 named scenes in test batches (work/qa/warp_all earlier runs; all reached
    WARP_DONE, shots read by eye), map_010, map_019, map_257, map_300. The full `warp_all.py --states` run
    (339 scenes) was stopped by Claude Code at 18/339 (all 18 ok) because the machine ran low on memory; it was not
    restarted.
- **Next (phase 2):**
  1. Re-run `python -X utf8 tools/debug/warp_all.py --jobs 2 --frames 3000 --states` (fewer jobs: 6 Mesen
     instances hit memory pressure) and read the contact sheets of `work/qa/warp_all/shots/` (in chunks). Fix or
     drop any scene that fails or shows nothing; then phase 2 is done.
  2. Game over is not reachable yet (`docs/re/debug.md` §Not reached yet): find the party-wiped-out path. Route
     starts need the branch flags: add when the event scripts are read (phase 4/5). The game has no chapter cards.
  Carried from phase 1 (not gating): confirm control codes `\p \s \g !R !W`; glyph bitmap layout behind the font
  descriptor table ~0x0FA690 (phase 5); tie each survey group to its screen by VRAM dump now that warps exist.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
