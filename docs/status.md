# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5. VWF in all three fonts; dialogue, book, description, item list and battle name budgets measured
  and linted; ROM strings classified by record table; an ASCII battle-skill-list bug to fix, then the effect /
  place-name boxes and the remaining menu/battle field budgets finish the width gate. Builds: `build/goushouden_en.gba`
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
    - ROM-string fields: `tools/lua/fieldprobe.lua` logs every menu-printer string (window, pen x/y, font mode);
      `warp_all.py --script` runs it on every scene (`work/qa/fields/`, 47 non-map scenes); `tools/fields.py` maps the
      marker ids to fields and (`TABLES`, `category()`) classifies every script/rom string by the record table that
      points at it: char_name / char_short (0xF0 records at 0x7B31C8), skill_name / skill_name2 (0x44 at 0x7BC7C4),
      rec18 (items, equipment, misc; 0x18 at 0x7C1F00), item_desc_rom (0x7DBF10), enemy_name (0x5C at 0x7DF910),
      map_name (0x0FA814); 469 strings sit in code pools only. Lint now checks ROM strings in px against every
      `windows.json` box whose `categories` match (item_list -> rec18 69 px; battle_name -> char_short 54 px, measured).
- **Next (phase 5, `references/pipeline.md` §Width gate):**
  - **BUG (engine, blocks the skill budgets): an ASCII skill name blanks the whole battle skill list.** Repro:
    `build.py --marker rom:DBD70-DBD78 --out build/qa_sk1.gba`, scene game_over, `--shots 2700`: the スキル window
    (w=0200E850, list drawn by 0x080863E8 -> 0x0800E3D0) shows no names, icons or DP for the battler whose row 0 is
    the ASCII string; the next battler's list (no ASCII) draws (work/qa/sk1). The JP-text engine build draws fine, and
    the printer takes the normal 8-px path (p2probe, work/qa/sk1p), so something after the print (icon/DP pass,
    a length or SJIS walk over the name?) bails on ASCII. Find it (watch the window's BG map / the DP draw), fix,
    then measure the skill field (JP: name x~25, DP column ~x=95).
  - Battle fields still to measure (fieldprobe game_over log): command banner skill name (w=0200E3E0 x=43, 12-px
    mode), enemy name + message (w=02010E80, enemy name sprintf'd with a battle message), battle message r0D1F9C
    (x=15); party/menu name windows (m1_party/m2_top w=0200A8C0 x=0); m2_sparty skill list (x=8); map-name banner
    (w=020088B0, map_name table, game_over / o_party_forest); credits (ending_credits, w=02008A60). Shots at chosen
    frames: `emu.py ... --shots N,M` (see work/qa/fields_go).
  - "Tomahawk Panther" is 96 px vs the 54-px battle name field: short names will need the field widened (D4: engine
    first) or the HP gauge moved; decide when translating names.
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
- **Open bugs:** ASCII skill name blanks the battle skill list (see Next; repro build/qa_sk1.gba, work/qa/sk1).
- **Waiting on the user:** nothing.
