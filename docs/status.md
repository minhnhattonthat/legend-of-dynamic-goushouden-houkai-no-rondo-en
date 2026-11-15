# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1. Research and recon in progress (Step 0 done). Last build: none yet.
- **Done:**
  - Step 0: ROM pinned (`rom.sha1`), MesenCE 2.2.1 + GBA BIOS in `tools/mesen/`, smoke boot of the original passes
    (`tools/routes/boot.txt`), scripted input and Lua logging work, pre-commit check rejects a failing test,
    guard hook vendored in `.claude/hooks/` and blocking, decisions D1-D7 recorded.
  - Recon (see `docs/re/`): no earlier fan patch; text is Shift-JIS; script archive at 0x08104DC0 (54 lh5 files,
    5,400 messages) fully decodable with `tools/lh5.py`; ~1,118 menu/item/location strings in plain SJIS at
    0x0CD000-0x0DF000 (990 with direct pointers); control codes catalogued (meanings partly guessed); runtime font
    with a 1,691-glyph SJIS charset list at 0x081EFF98 (no half-width ASCII).
  - Savestates: `work/states/park_dialogue.mss` (first dialogue); `work/play/intro/` session (name entry -> park).
- **Next (to finish phase 1):**
  1. Graphics-text survey (`docs/re/graphics.md` "To do"): tour the menus/battle/shop and run the static sweep of
     all lh5 blocks; identify the type 1 and type 3 codecs (0x08002E64, 0x08001D70) if the sweep needs them.
  2. Confirm the guessed control codes (`\p`, `\s`, `\g`, `!R`, `!W`) by corrupting/editing one message in RAM.
  3. Locate the glyph bitmap layout behind the font descriptor table at ~0x0FA690.
  Then phase 2: debug tool (lead: debug/test strings at 0x0CDD50 and 0x0D31C0 suggest a leftover debug menu).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
