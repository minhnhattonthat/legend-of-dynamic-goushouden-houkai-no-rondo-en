# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6. Translate in progress: set-up done (batches tool, name tags, glossary seed, synopsis, style
  reference, translator brief, pilot b001 = f00 merged). Batches in `work/tl/` (gitignored, on disk): b001-b086.
  Batch progress: see "Phase 6 batches" below.

## Phase 6 batches
`python -X utf8 tools/batches.py split|check|merge|fit` (docs/translator-brief.md). Batches were split once
(b001-b086; never re-split: `split` only adds ids not yet batched). Map: b001-b055 dialogue f00-f53 (b053 = tail
of f51), b056-b058 book, b059-b061 desc, b062 effect, b063-b066 place, b067-b076 rom misc + map names, b077-b079
char names, b080-b082 skills, b083-b085 items (rec18), b086 item descriptions.
- Merged: b001.
- Wave 1 dispatched (names first, so dialogue can use them): b077-b082, b083-b086 + b059-b062, b067-b076 +
  b063-b066, b056-b058. Translators run as general-purpose agents with the brief path (the plugin agent types were
  not registered in the Orca worker; `.claude/agents/` now vendors them for the next session as `translator` etc.).
- After wave 1: merge, write `build/names.tsv` (all rom name translations, JP<TAB>EN) for wave 2's read list, add
  recurring NEW TERMs to glossary.md; then wave 2 = b002-b055 (4-5 batches per agent, story order), then a
  reviewer pass per batch (read-only, `assets/reviewer-brief.md`; fix Critical/Important; Minors to docs/polish.md).
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
- **Next (phase 6, `references/translation.md`):** the batch plan above.
  - Short names: "Tomahawk Panther" is 96 px vs the 54-px battle_name / 48-px menu_name fields: pick short forms
    for char_short (D4 says engine first: widening the battle field means moving the HP gauge).
  - Carried to phase 7: map the 469 code-pool strings (`fields.py`: no record table) to boxes from the field-probe
    logs (help lines in the bottom box, battle messages in the banner) so the lint checks them in px; they already
    have in-place byte limits. Effect reader 0x0809CC54 (from 0x09E9BA) not seen drawing.
  - Carried to phase 8: banner and other centred lines are centred by byte count (x = 120 - 7 * bytes in the
    battle banner), not by VWF width; SFX names (`sfx.json`) probably sprites via the kana lookup 0x0D9C58; the
    graphics-text survey groups; `{g}` width in game.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
