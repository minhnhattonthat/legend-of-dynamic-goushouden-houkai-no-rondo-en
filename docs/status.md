# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5. VWF in all three fonts, dialogue budgets measured and linted; the menu/list field budgets
  (items, skills, shop, battle, map names) are the last part of the width gate. Builds: `build/goushouden_en.gba`
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
      (source pointer of every string the two printers draw, and its callers).
    - Marker tour 340 scenes (`work/qa/marker_tour/`): 337 ok; retail_newgame, game_over, ending_credits only need
      `--frames 4000`. Every box reached shows its id. `jp_left.py --gba-ptrs` on the marker build: 0 runs.
- **Next (phase 5, `references/pipeline.md` §Width gate):**
  - **First: extract the five hidden text archives** after the script archive (`docs/re/text.md` §1b: character
    book, item/skill descriptions, equipment effects, map names; ~840 messages). The marker build shows the book in
    Japanese (m1_book). Generalise `tools/archive.py` (base, file count, end as parameters), dump them to their own
    `script/` files via `tools/extract.py` (roundtrip test + identity build must stay byte-exact), rebuild them in
    new space after the main archive, repoint the literal pools listed there (assert the old value first; sweep for
    other forms), add them to the marker build, re-run m1_book / m1_item / shop scenes to confirm ids.
  - game_over fails the warp even with `--frames 4000` on the marker build (passed on the original in phase 2):
    rerun on `build/goushouden_en.gba` and the original to see if the marker text breaks the battle/game-over path.
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
