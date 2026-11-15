# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5. Engine spike and marker build next (phase 4 done: extract + roundtrip/coverage tests). Last build:
  `build/goushouden_en.gba` sha1 8a037eff3a44b1667ec5e81ca8c1ff03537366b2 (= the original, now built through
  `script/`), smoke ok.
- **Done:**
  - Step 0 and phase 1 (see git history and `docs/re/`): ROM pinned, MesenCE 2.2.1, codecs verified, script archive
    and menu strings located, graphics-text survey (`docs/re/graphics.md`).
  - Phase 2 (`docs/re/debug.md`): the game's own debug menus drive `tools/debug/warp.lua`; `tools/debug/scenes.txt`
    (47 named scenes) plus `map_NNN` for all 293 field maps; proof run 340/340 from a cold boot.
  - Phase 3: `build.py` identity build byte-identical (`tests/test_identity.py`), lh5 encoder `tools/lh5.py`.
  - Phase 4 (`docs/re/text.md` §1 table, §2 "Phase 4 extraction"): `tools/sjis.py` codec (cp932, `0D` = newline,
    `{p}` `{s}` `{g}` `{!R}` `{!W}`, `[XX]` for anything else, `[ ] { }` escaped). `tools/extract.py dump` wrote
    `script/archive/f00..f53.json` (5,363 messages, `msg` = game message ids) and `script/rom/*.json` (1,849 pointed
    strings, 60 of them status `data`: 20 ASCII-only, 40 kana-lookup entries; `sfx.json` 145 onomatopoeia record names). `build.py` inserts from
    `script/` (archive slots rebuilt from JSON; translated ROM strings in place, `max` bytes). `tests/test_extract.py`:
    codec fuzz, every slot and string re-encodes to its bytes, script/ matches the ROM, coverage (no kana/kanji run
    left in the string sections, no text outside them but 2 waived non-text hits), English reaches the ROM.
- **Next (phase 5, `references/pipeline.md` §Marker, `references/platform-gba.md`):**
  - Engine spike: how the renderer draws ASCII/half-width (font descriptor table ~0x0FA690, `docs/re/font.md`);
    pick half-width/VWF; prove it in game with a torture line.
  - Marker build (`build.py --marker`?): every line `[id] marker` at full box width; tour with warp_all; confirm
    `{p}` `{s}` `{g}` `{!R}` `{!W}` meanings, flag debug-only strings (debug menu text in `script/rom/0CD000..0D9000`),
    find non-text strings, measure every box variant (width gate) and record budgets.
  - Archive space: the archive fills its slot exactly (0 slack; re-encoding all files frees 121 bytes). English will
    grow it: relocate (free space: 0x7F05B4-0x800000 is 0xFF fill, 64 KiB, too small for 188 KB; expanding the ROM
    past 8 MiB is the likely route) and repoint `archive.POINTER_SITES`. ROM strings in place have `max` bytes; longer
    ones need relocation + repointing every `ptrs` site (phase 7).
  - SFX names (`sfx.json`) are probably drawn as sprites via the kana lookup at 0x0D9C58 (guess): check in game.
  - Carried: route starts need branch flags (not gating); tie each graphics survey group to its screen by VRAM
    dump; edited graphics repack as type 2 (`docs/re/compression.md`).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
