# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5. Engine spike done (VWF in game); marker build boots and shows ids in dialogue; marker tour review,
  non-text strings and the width gate are next. Builds: `build/goushouden_en.gba` (JP text through the new engine:
  16 MiB, archive relocated, VWF), `build/goushouden_marker.gba` (`build.py --marker`).
- **Done:**
  - Step 0, phases 1-4 (see git history and `docs/re/`): ROM pinned, MesenCE 2.2.1, codecs, debug warp tool
    (`tools/debug/`, 340 scenes), identity build (`build.py --verify`), extraction to `script/` (`tools/sjis.py`).
  - Phase 5 so far (`docs/re/font.md` Printer + VWF, `docs/re/memory.md` layout, `tools/engine.py`):
    - English is plain ASCII, 1 byte/char: the printer maps every single byte to a fullwidth glyph (0x0800FE5C).
    - VWF: the 94 Latin glyphs of the 12-px font moved to column 0, the 16 pen-advance sites in the printer call a
      hook at 0x104DC0 that subtracts `12 - width`. Verified in game (`Abc Hello ijl`, map_290).
    - ROM: 16 MiB, archive at 0x800000 (5 pointers), every write logged (`build/*.writes.txt`), `tests/test_engine.py`
      (archive reads back, every changed byte logged and in an allowed range, widths sane).
    - `build.py --marker [archive|rom|rom:LO-HI]`, `--qa FF.SS=TEXT`; `tools/marker.py`; `tools/lua/drawlog.lua`.
    - Non-text found so far: ASCII map rows 0x0CE010-0x0CE154 (now `data`, `romstr.DATA_SPANS`); default names
      r0D18BC/r0D18C4 need fullwidth (`extract.FULLWIDTH`). `{p}` = hero's name (verified), `{s}` = heroine (guess).
    - Fixed: `.gitignore` `rom/` hid `script/rom/` (1,849 ROM strings were never committed); now `/rom/`.
    - Dialogue box: 1 line held ~32 capitals (`ABCDEFGHIJ` x3 + `AB`) before clipping at the right edge.
- **Next (phase 5, `references/pipeline.md` §Marker + §Width gate):**
  - Review the marker tour `work/qa/marker_tour/shots/` (rerun: `python -X utf8 tools/debug/warp_all.py
    build/goushouden_marker.gba --out work/qa/marker_tour --jobs 2`; send the shots to a read-only pass in chunks).
    Look for: Japanese left (text not extracted), blank or garbled boxes (non-text strings -> `DATA_SPANS`), menus
    drawn by fonts or paths the VWF doesn't cover yet (8/16 px fonts: their cell width isn't 12, the hook skips them).
  - Torture line (all printable ASCII + double spaces) with `--qa`, zoomed shot; tune GAP / odd glyphs (`i`, `l`, `'`).
  - Width gate: measure in pixels per box variant (dialogue lines and lines per page, name tag, choices, menus,
    item/skill fields, shop, battle messages) and record budgets in a window-data file the lint will read.
  - `{s}` `{g}` `{!R}` `{!W}` meanings in game; `!R`/`!W` mean English must never contain `!R`/`!W` literally.
  - Archive buffer: English files grow; check the EWRAM file buffer (0x0201D000..) holds the largest file
    (marker files are bigger than JP; a crash or garbage in some scene would show it).
  - Carried: SFX names (`sfx.json`) probably sprites via the kana lookup 0x0D9C58; graphics survey groups to screens.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
