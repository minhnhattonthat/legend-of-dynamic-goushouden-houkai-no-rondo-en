# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6. Translate: phase 5 (engine spike, marker build, width gate) is done; next is the translation
  set-up (glossary seed, synopsis, style pilot, batches tool), then batches. Builds: `build/goushouden_en.gba`
  (JP text through the new engine, sha1 c1843bf2, smoke ok), `build/goushouden_marker.gba` (`build.py --marker`).
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
- **Next (phase 6, `references/translation.md`):**
  - Glossary seed (`glossary.md`, D1-D5 policies are in `docs/decisions.md`): character names (Go Nagai cast:
    Devilman, Cutie Honey, Mazinger, Getter etc.: official English names where they exist, D2), skills, items,
    enemies, places from `script/rom` + `script/place`; term families (弱/中/強 etc.); sound-effect style, register.
  - `docs/synopsis.md` (story by chapter, who is who), then a pilot slice translated by hand, inserted, booted,
    and turned into `docs/style-reference.md`.
  - Copy `$SKILL/assets/batches.py` to `tools/`, fit its ADAPTER to `script/archive` + `script/rom` + the other
    archives with the px limits above (`lint.line_px` / `windows.json`), then batches with translator agents.
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
