# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 8. QA in the emulator: not started. Phase 7 done 2026-11-16: build green (check.py 39 tests + lint
  0 errors; romdiff --writes clean, 2246 writes; smoke ok; build sha1 2d0b5d4b...).

## Phase 7 (done)
- `build.py insert_rom_strings` relocates every translated ROM string longer than its slot: written after the
  archives (0x800000+), each pointer site in its `ptrs` asserted to hold the old address in the original, then
  repointed (185 strings: 105 debug map names, 25 rec18, 26 code-pool, char/enemy/skill names). The lint treats
  bytes as soft when a string has pointers. `tests/test_build_en.py`: English build, romdiff with the write log,
  writes only in allowed ranges or a relocated string's own pointer sites, every relocated pointer reaches its text.
- All LONG ids merged (`tools/long.py` lists any left: none). Restored to glossary forms: debug map names
  (fixes6/fixes7: Science City, Lost Forest, Hill of Beginnings, Mirage Castle, Harenchi Gakuen, Dark Temple...),
  char_name full names (Immortal Corps C, Mechanical Beast A, Reaper Police 3...).
- Px-limited names got short forms (D8): `script/short_forms.tsv` (glossary check accepts exactly those) and
  work/qa/review/fixes5.tsv (rec18 people as "Initial. Surname", char_short "Kekko", "Aphro. A", skills
  "G.Tomahawk", "H.Boomerang", "RustHurricane", item "PsychoJenny"). Wave-1 px abbreviations (K.Sirene, Maru G.,
  Cut/Stars/Mask, Bolt/Blunt/Slash, book cuts) stay under D8: their limits are field px / book lines, not bytes.
- **Phase 8 must check (not linted in px):** the 26 relocated code-pool strings: credit staff pairs (table
  0x0D24F4-0x0D29C0, drawn by the printer in mode 2, ending_credits scene; now up to 36 bytes vs 27) and book
  series titles (pool 0x103xxx: "Goushouden", "Susano-oh"); enemy names now longer than their JP room are
  sprintf'd into "<enemy> appeared!" (battle banner; buffer size unknown); char_name has no measured field. The
  469 code-pool strings still have only byte limits (no px box): verify them on the phase 8 tour sheets.

## Review (read-only codex passes; no nested workers under Orca)
`python -X utf8 tools/pairs.py` (pairs files, work/qa/review/pairs/), `R=DIR JOBS=4 sh tools/review.sh [bNNN ..]`
(codex exec -s read-only per batch, prompt tools/review_prompt.txt; skips batches whose report exists),
`tools/review_findings.py [--rep DIR] [--tsv OUT]`, fixes hand-written as `id<TAB>EN` in
work/qa/review/fixesN.tsv and applied by `tools/apply_fixes.py` (whole entries by id, no pattern rewrites), then
`batches.py merge ... --overwrite` (`--partial` for b056-b086). A dialogue merge of all 55 batches takes ~3 min.
- Round 1 (work/qa/review/reports/, all 86 batches): 1 Critical + 92 Important; all adjudicated in fixes1/fixes2
  (one rejected, noted there), merged; 72 Minors in docs/polish.md. Build, check, smoke ok after.
- Names now follow the ROM's own kana short names (glossary "Decisions from earlier batches"): Nantomo Iyahaya
  (was Nanyu/Nanto), Kitani (was Onitani), Hatesate family, Koja Hatesate (was Nijija Hatesa), Daiko Hoin (was
  Hoin Taishi), Eisanbo Daihon (was Omoto Eisanbo), Hakase (was Hakayo). speakers.tsv updated to match.
- Round 2 (work/qa/review/reports2/, the 45 batches touched in round 1): 18 Important (ci2.tsv), fixed in
  fixes3/fixes4. Two rejected: the reviewer wanted Mido -> Shindo and Daihonei -> Daihon, but the ROM's kana short
  names bind, so the full names now follow them: 身堂竜馬 Ryoma Mido, 大本栄惨坊 Sanbo Daihonei (大本営参謀 pun).
  "Discharge"/"Blizzard" (r0DCA54 r0DCA5C r0DCB30 r0DCB38) are now LONG for the 7-byte skill_name field: relocate.
  Use JOBS=3 for review.sh: six codex processes at once ran the machine low on memory.
- Round 3 (work/qa/review/reports3/, the 14 batches changed in round 2): 0 Critical/Important, 10 Minors.
- Book cut added: series title "Iyahaya" for イヤハヤ南友 (B00.88 B00.89 B01.29 B01.39 B01.40): "Iyahaya Nantomo"
  is 112 px vs the 108-px book line and the JP keeps lines 2-3 blank.

## Phase 6 batches
`python -X utf8 tools/batches.py split|check|merge|fit` (docs/translator-brief.md). Batches were split once
(b001-b086; never re-split: `split` only adds ids not yet batched). Map: b001-b055 dialogue f00-f53 (b053 = tail
of f51), b056-b058 book, b059-b061 desc, b062 effect, b063-b066 place, b067-b076 rom misc + map names, b077-b079
char names, b080-b082 skills, b083-b085 items (rec18), b086 item descriptions.
- Merged: b001, wave 1 b056-b086 (2608 entries translated, lint 0 errors). Batch inputs and outputs are tracked in
  git now (`work/tl/`, un-ignored). `work/tl/names.tsv` (`tools/names.py`) = translated ROM/place names for wave 2.
- **LONG, left untranslated (105 ids):** `merge --partial` skipped ids whose full English doesn't fit the in-place
  byte limit or the field px: b070 (Hill of Beginnings map names), b073 (credit staff names / series titles), b078,
  b079, b081, b082 (names wider than char_short 48 px / skill 72 px), b084, b085 (49 name records r0DD8B8-r0DDD24),
  b086 (enemy names). Their full English is in `work/tl/bNNN.out.tsv`. Phase 7: relocate these strings (byte limits
  are only "in place") and widen fields per D4, then `merge` those batches. `batches.py merge --partial` prints them.
- **Abbreviated by wave 1 to fit (against D4, restore after relocation):** char_short names (K.Sirene, I.Kaiser,
  M.Ashura, Maru G., Jiro for 手天童子郎, Susanoo), skill words (Cut for 剣, Stars for 手裏剣, Mask for 死の面,
  Murakumo, Bolt Flare), item element words (Bolt/Blunt/Slash, Amulet/Stud/Band), debug map names (SciCity,
  LostForest9), book series titles ("Enma-kun" for Dororon Enma-kun) and book LONG cuts B00.20 B00.70 B00.82
  B01.03 B01.07 B00.08 B01.16.
- Wave 1 readings still unsure (reviewer: check against names.tsv and speakers.tsv): 果扨胴下 (Doshita Hatesa vs
  Doka Hatesate), 大本栄惨坊, 無幻大権, 法印大子, 墓世, 女蛮子 (Banji / Banko / Sukebanko), 真神, 鬼谷妖次郎;
  term drift merged before the glossary rows: "Phantom Castle" in items (glossary: Mirage Castle), "Death Police"
  in book B01 (glossary: Reaper Police). Fix these in the review pass.
- Wave 2 (b002-b055) was translated by one worker in a single pass (Orca refused subagents), all merged. Calls
  made there, now in glossary.md "Decisions from earlier batches" and new term rows: Demon King (Grade) vs Demon
  Lord Dante, Kigoku World, Kibutsu Clan, Dimension Prison, Moon of destruction / Sun of rebirth, Precog Clan,
  Yokai Patrol, Iyahaya / Hatesa families, Banji Suke, Ryoma Shindo, Beehive Nyudo. speakers.tsv: added Garo,
  Eriza Hyo, Tomahawk / Scissors Panther, Nijija Hatesa, Big Girl, Security Guard; 蛮子 Banko -> Banji, 果扨胴下
  -> Doshita Hatesa.
- Unsure (reviewer to confirm): 45.06 and 53.43 have an empty JP body (name tag only); the check refuses empty
  English, so they hold "...\n" (a box with "..." may now show where the JP shows an empty one). 男男子 read as
  "Danshi Otoko" (51.93, 52.10-11). 法印大子 as "Taishi Hoin", 豹絵里座 as "Eriza Hyo", 墓世 as "Hakayo".
  Item/enemy data (wave 1) still says HiveMonk (LONG, phase 7); dialogue says Beehive Nyudo. 鬼谷 is Kitani everywhere now.
- Review done (section "Review" above; names later changed in round 2: Ryoma Mido, Sanbo Daihonei). The wave 1
  unsure readings and term drift above were settled in round 1 (kana readings; Mirage Castle, Reaper Police); 真神, 男男子 have no kana form and stay as is.
- In-game pilot view not done: `retail_newgame` stops at the name entry (an empty name won't confirm: type a
  character first). Phase 8 needs a name-entry route or a warp past it.
- **Done:**
  - Step 0, phases 1-4 (see git history and `docs/re/`): ROM pinned, MesenCE 2.2.1, codecs, debug warp tool
    (`tools/debug/`, 340 scenes), identity build (`build.py --verify`), extraction to `script/` (`tools/sjis.py`).
  - Phase 5 (`docs/re/font.md`, `docs/re/memory.md`, `tools/engine.py`):
    - English is plain ASCII, 1 byte/char. Dialogue draws with the half-width font (mode 3, 6 px), menus/lists with
      the 8x8 font (mode 1, 8 px); the book is inserted fullwidth (12-px font). VWF on every advance site of both
      printers (`engine.PRINTERS`), tabular digits. set_cursor clamps x at 0 (centred overlong lines corrupted the
      heap). Right-hand overflow tested in the save slot (200-char place name: no OOM).
    - Hidden archives (book, desc, effect, place, test) extracted, relocated and repointed (`archive.ARCHIVES`).
    - Marker tour 340 scenes ok; every box reached shows its id; `jp_left.py --gba-ptrs` on the marker build: 0 runs.
    - **Width gate** (`tools/windows.json`, all measured in game with the shot named per box; `tools/lint.py`
      checks archive messages per box and ROM strings by record table, `tools/fields.py` TABLES):
      dialogue 192/184 px x 2 lines per page, name tag 36 bytes, `{p}`/`{s}` 84 px, `{g}` 72 px (guess);
      book 108 px x 7 (12-px), desc 224 px x 1, effect 76 px x 2 (8-px, party screen partner panel), place names
      114 px (save slot 現在地); ROM strings: item_list 69 px and equip_list 70 px (rec18), battle_name 54 px and
      menu_name 48 px (char_short), skill_list 72 px (battle, skill_name2), skill_party 76 px (both skill copies),
      battle_banner 230 px (skill_name, enemy_name). Map names (map_name table) show only in the leftover debug
      menu; credits are graphics (phase 8).
    - The "ASCII skill name blanks the battle skill list" bug was a shot-timing artefact (the window opens 0-6 frames
      later in some builds; shots at 2696-2700 catch it empty). `tools/bisect_marker.py --ink FRAME:X,Y,W,H[:N]`
      bisects a visual predicate now.
    - Script files are malloc'd at their unpacked size (no fixed buffer; ~148 KB heap free on a field map);
      build.py caps a file at 32 KB. Codes: `{g}` = obtained item name / money amount; `{!R}`...`{!W}` wrap
      transceiver / remote speech (printer style); keep them where the JP has them (lint checks counts).
- **Next (phase 8, `references/emulator-qa.md`, `references/graphics.md`):** tours with contact sheets and
  visual-QA verdicts (do them as a fresh read-only pass or `codex exec`: no nested workers), graphics text, inkbox,
  textcover; the "Phase 8 must check" list above. Effect reader 0x0809CC54 (from 0x09E9BA) not seen drawing.
  - Code-pool px mapping (469 strings, no record table): `tools/fields.py work/qa/fields` already maps 825 drawn
    ids to window / x / right-hand neighbour; turning that into per-id px limits would let the lint check them.
  - Also for phase 8: banner and other centred lines are centred by byte count (x = 120 - 7 * bytes in the
    battle banner), not by VWF width; SFX names (`sfx.json`) probably sprites via the kana lookup 0x0D9C58; the
    graphics-text survey groups; `{g}` width in game.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
