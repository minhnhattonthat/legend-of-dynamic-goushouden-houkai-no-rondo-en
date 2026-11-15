# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 4. Extract next (phase 3 done: identity build byte-identical, as a test). Last build:
  `build/goushouden_en.gba` sha1 8a037eff3a44b1667ec5e81ca8c1ff03537366b2 (= the original), smoke ok.
- **Done:**
  - Step 0 and phase 1 (see git history and `docs/re/`): ROM pinned, MesenCE 2.2.1, codecs verified, script archive
    and menu strings located, graphics-text survey (`docs/re/graphics.md`).
  - Phase 2 (`docs/re/debug.md`): the game's own debug menus drive `tools/debug/warp.lua`; `tools/debug/scenes.txt`
    (47 named scenes) plus `map_NNN` for all 293 field maps; proof run 340/340 from a cold boot
    (`tools/debug/warp_all.py`, `--states` regenerates `work/states/<scene>.mss`).
  - Phase 3: `build.py` (rom check -> `tools/archive.py` reads all 54 lh5 files of the script archive and rebuilds
    it; unchanged files keep their original stream -> byte-identical ROM). lh5 encoder in `tools/lh5.py`
    (smaller than the original packer; round-trips all 54 files and all 10,106 scanned packed blocks).
    `build.py --reencode --out build/reencode.gba` puts every file through our encoder: map_290's dialogue
    matches the original in game. `tests/test_identity.py` (identity, re-encoded archive reads back, slot
    split/join, lh5 edge cases, graphics blocks repacked as type 2) runs in `tools/check.py`.
- **Next (phase 4, `references/pipeline.md` §Extract):** extract the script archive to `script/` JSON (one file per
  archive file; `archive.split_file` gives the 100 slots; split each slot at `00` into strings; id = file/slot/index;
  keep `jp`), and the menu/item strings (plain SJIS, 990 with u32 pointers + fixed-stride records, `docs/re/text.md`
  §2) to their own JSON; `tbl/` or a cp932 codec with control codes `\p \s \g !R !W 0D` as tags; a roundtrip test
  (re-encoding every string gives the original bytes, text ranges fully covered) wired into `tools/check.py`, then
  hook the insert path into `build.py` (identity must stay green). Archive growth past 0x132E74 needs relocation +
  the 5 pointer sites in `archive.POINTER_SITES` (not written yet; the encoder leaves ~120 bytes of slack).
  Later, not gating: route starts need the branch flags (phase 4/5; no chapter cards). Carried from phase 1:
  confirm control codes; glyph bitmap layout behind the font descriptor table ~0x0FA690 (phase 5); tie each survey
  group to its screen by VRAM dump. Edited graphics: repack as type 2 (`docs/re/compression.md`, a guess until a
  phase 8 boot).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
