# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5. VWF in all three fonts; dialogue, book and description budgets measured and linted; hidden
  archives extracted; the effect / place-name boxes and the menu/list field budgets (items, skills, shop, battle)
  are the last part of the width gate. Builds: `build/goushouden_en.gba`
  (JP text through the new engine), `build/goushouden_marker.gba` (`build.py --marker`).
- **Done:**
  - Step 0, phases 1-4 (see git history and `docs/re/`): ROM pinned, MesenCE 2.2.1, codecs, debug warp tool
    (`tools/debug/`, 340 scenes), identity build (`build.py --verify`), extraction to `script/` (`tools/sjis.py`).
  - Phase 5 (`docs/re/font.md`, `docs/re/memory.md`, `tools/engine.py`):
    - English is plain ASCII, 1 byte/char. It does **not** draw with the 12-px font: dialogue uses the half-width
      font (mode 3, 6 px), menus/lists the 8x8 font (mode 1, 8 px). Two printers (`engine.PRINTERS`: 0x0800E898
      dialogue, 0x0800E3D0 menus). Every advance site of both is hooked; ASCII glyphs of all three fonts moved to
      column 0; delta tables per font; digits tabular (7 px / 6 px). Verified in game: torture line at map_290,
      item menu and party list (m1_item, m1_party).
    - Torture line: every printable ASCII draws; `\` = yen sign, `` ` `` = blank (the lint bans both).
    - Width gate so far (`tools/windows.json`, read by `tools/lint.py`, run by `tools/check.py`):
      dialogue line 1 = 192 px, line 2 = 184 px (page arrow), 2 lines per page, blank line = new page (measured);
      name tag 36 bytes (measured); `{p}`/`{s}` = 84 px (7-char name entry x 12 px kana, measured).
      Item list name field 69 px before the count (`item_list`, measured; not yet mapped to ROM string ids).
    - Probes: `tools/lua/advprobe.lua` (advance sites: pen, pair, font mode, cell width), `tools/lua/srcprobe.lua`
      (source pointer of every string the two printers draw, and its callers), `p2probe.lua` (menu printer calls +
      window fields), `glyphdest.lua`, `arcprobe.lua` (which archive a scene reads), `malloclog.lua`, `oom.lua`
      (heap walk / out-of-memory trap), `watchw.lua` (who writes an address), `pcsample.lua`; `tools/funcof.py`
      (function holding a literal pool + its BL callers), `tools/bisect_marker.py SCENE` (ROM-marker bisection).
    - Hidden archives extracted (`archive.ARCHIVES`, `script/{book,desc,effect,place,test}/`, 843 messages, ids
      B/D/E/P/T + FF.SS): identity byte-exact; the build rebuilds book/desc/effect/place after the script archive
      and repoints their literal pools (full-ROM sweep: no other pointer forms). The test archive (1 line, no
      pointer) stays in place, status data. Marker build shows B.. ids in the book and D.. ids in its skill box.
    - The book window can't show plain ASCII (ink goes to tiles it never displays): the book is inserted fullwidth
      (`Spec.wide`, 12-px font, proportional through the VWF), and must fit its 512-byte stack buffer (build.py
      checks 511 bytes). Budgets measured: book 108 px/line, 7 lines incl. name + 2 blank (`windows.json` book,
      12-px widths); description box 224 px, 1 line (desc, half-width). Lint checks both (`lint.lint_box`).
    - game_over on the marker build fixed: a centred line wider than its window got x < 0 and the glyph blitter
      corrupted the heap (`docs/re/memory.md` §Heap). set_cursor 0x0800FD08 now clamps x at 0
      (`engine.CURSOR_SITE`). Marker game_over reaches GAME OVER; m1_*/m2_top/k_jump* still ok.
    - Marker tour 340 scenes (`work/qa/marker_tour/`): 337 ok; retail_newgame, game_over, ending_credits only need
      `--frames 4000`. Every box reached shows its id. `jp_left.py --gba-ptrs` on the marker build: 0 runs.
- **Next (phase 5, `references/pipeline.md` §Width gate):**
  - **Effects and place names: find their screens and measure.** Readers (`docs/re/text.md` §1b): effect
    0x0809CC54 (from 0x09E9BA), 0x080A3618 (from 0x0A5F44 / 0x0A6576 / 0x0A7C94); place 0x08096C48 (from
    0x09751C), 0x08097084 (from 0x0976A6), probably the save/load slots' 現在地 (needs a save: no scene has one;
    add a scene that saves from k_jump, or a .sav in work/states). For each: check ASCII shows (else `wide` like the
    book), measure px, add to `windows.json` + `lint.BOXES`. Desc readers 0x0808827C / 0x0809A45C (item menu,
    battle?) not yet seen: confirm the 224 px box there.
  - **Right-hand overflow is unguarded** (`docs/re/memory.md` §Heap): a line past its window's right end may corrupt
    the heap like the negative x did. Either test it (marker build: a long ROM string in a short centred window)
    and clamp the pen at the window width in the VWF hook, or make every box's px budget part of the lint (below).
  - Centred lines are centred by byte count, not VWF width (cosmetic, phase 8).
  - Review `work/qa/marker_sys/shots/` (46/47 ok; m1_*/m2_* reviewed: dialogue/menus show ids, menu labels and
    headers are graphics text = phase 8) (non-map scenes, new marker build, `--frames 4000`): for each list/menu
    field (item, skill, equipment effect, enemy names, shop, battle messages, map names, save/load, sfx) read the
    field x and the next element's x, record px budgets in `tools/windows.json` with the shot, and map the
    `script/rom` id ranges to them so the lint checks ROM strings in px (8-px font: `engine.eight_widths`).
  - Item names have ~69 px (about 11 chars): consider moving the count right (engine work, decision D4) if the
    glossary names don't fit.
  - `{g}` (item name variable?) and `{!R}`/`{!W}` meanings; the archive buffer size (EWRAM 0x0201D000..) vs the
    largest English file.
  - Carried: SFX names (`sfx.json`) probably sprites via the kana lookup 0x0D9C58; graphics survey groups.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
