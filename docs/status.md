# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool next (phase 1 recon done). Last build: none yet.
- **Done:**
  - Step 0: ROM pinned (`rom.sha1`), MesenCE 2.2.1 + GBA BIOS in `tools/mesen/`, smoke boot of the original passes
    (`tools/routes/boot.txt`), scripted input and Lua logging work, pre-commit check rejects a failing test,
    guard hook vendored in `.claude/hooks/` and blocking, decisions D1-D7 recorded.
  - Phase 1 recon (see `docs/re/`): no earlier fan patch; text is Shift-JIS; script archive at 0x08104DC0 (54 lh5
    files, 5,400 messages); ~1,118 menu/item/location strings in plain SJIS at 0x0CD000-0x0DF000 (990 with direct
    pointers); control codes catalogued (meanings partly guessed); runtime font charset at 0x081EFF98 (no ASCII);
    free space = growing the ROM past 8 MiB.
  - All packed formats decoded and verified against game output (`tools/packed.py`, `tests/test_codecs.py`): type 1
    (u16 LZSS), type 2 (lh5), type 3 (bit LZ), 0x63 (stored). `tools/scanpacked.py` finds 10,225 blocks.
  - Graphics-text survey: static sweep of every block and every uncovered range, two codex passes ->
    `docs/re/graphics.md` (groups S1-S7: menu captions, title logo, battle UI, large outlined title lettering,
    shop signs) and `docs/re/graphics_sweep.tsv` (167 blocks).
  - Savestates: `work/states/park_dialogue.mss`; `work/play/intro/` (name entry -> park); `work/qa/tour1/s*.mss`
    (mashed tour to the first field, every 5000 frames).
- **Next (phase 2, debug tool):**
  1. Leads: debug/test strings at 0x0CDD50-0x0CDF40 and 0x0D31C0-0x0D3A10 (`スプライトの表示をするテスト`,
     `バトルテスト`, `メニュー項目２１`) suggest a leftover debug menu; find the code that references them.
  2. Otherwise: find the scene/map id and story-flag RAM (`ramsearch.py`), write `tools/debug/warp.lua` and
     `tools/debug/scenes.txt` (title, name entry, menu screens, a battle, a shop town, each chapter card, game
     over, ending, credits), one cold-boot shot per entry.
  Carried from phase 1 (not gating): confirm control codes `\p \s \g !R !W` (phase 4/5 marker build shows them);
  glyph bitmap layout behind the font descriptor table ~0x0FA690 (phase 5); tie each survey group to its screen
  by VRAM dump + `vramfind.py` once warps exist.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
