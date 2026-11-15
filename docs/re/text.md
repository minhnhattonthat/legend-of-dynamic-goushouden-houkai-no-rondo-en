# Text

Encoding: **Shift-JIS** (cp932), fullwidth only in practice (verified: dialogue in an EWRAM dump decodes as cp932;
the font charset lists only double-byte codes). Half-width 0x20 (space) and some ASCII appear inside control codes.

## 1. Script archive (story dialogue) (verified: decoded, the opening dialogue found in RAM)
- Root `X = 0x08104DC0`, referenced from code literal pools at 0x7DDC, 0x80BC, 0x8348, 0x8600, 0x17E8C.
- `X+0`: u16 count 0x429B (17,051), then 17,051 u16 entries: message id -> sequential message number (0xFFFF = none);
  5,363 ids are used, numbers 0..0x14F2. **guess**: number / 100 = file, number % 100 = slot.
- `X+0x8538` (ROM 0x10D2F8): 54 entries `{u32 offset from X, u32 unpacked size}`; files start at X+0x86E8 (0x10D4A8)
  and are bare lh5 streams (no header), packed back to back (the next offset = this offset + compressed length,
  verified for all 54). Archive ends at 0x132E74.
- Each unpacked file: 100 x u32 offsets, then the messages. 5,400 slots, 39 empty, 278,687 bytes of message data.
  File 53 slot 99 runs into trailing binary (padding/garbage after the last message): exclude in extraction.
- At run time a whole file is unpacked into EWRAM (around 0x0201D000..0x0201FFFF; the opening file sat at 0x0201D66C).

### Message format (counts over all 5,400 messages)
| bytes | count | meaning |
|---|---|---|
| `0D` | 12,352 | line break; the first line of a dialogue message is the speaker name (e.g. `不動明` CR `「黒い月が…」`) **guess** from RAM view |
| `00` | 5,699 | end of string (some messages hold more than one string) |
| `\p` (5C 70) | 1,484 | **guess**: new page / wait for key |
| `\s` (5C 73) | 327 | **guess**: player name (the hero is named at start; see 0x0201D9F0 RAM view `\s`) |
| `\g` (5C 67) | 2 | **guess**: item-get name |
| `!R`, `!W` (21 52 / 21 57) | 120 / 11 | **guess**: inline codes after `!` (e.g. `了!R明`, `着く!W`): colour/ruby or wait; check in phase 4 |
| `20` | 5,273 | half-width space (padding/alignment) |
| other bytes < 0x20 (`09` `0E` `10` `16`...) | a few each | mostly in file 53 slot 99 garbage; `09` seen once in a real line (`兜甲児<09>大変な`) |
Choices are plain strings in a message (`はい` `いいえ` after `！！ `). Lists of all codes go in phase 4.

## 2. Menu, item, location and system strings (plain SJIS in ROM)
- 1,118 null-terminated SJIS strings with >= 3 kana, almost all in 0x0CD000-0x0D5000 (426) and 0x0D9000-0x0DF000 (683).
  0x0CD000+: debug-test strings, location names (`関東スラム・マミー薬局Ｆ`), party join/leave messages, menu items,
  publisher credits (`株式会社バンプレスト`). 0x0D9000+: fixed-stride records: SFX/onomatopoeia names (stride 0x20 at
  0x0D9D44), character names, skills, weapons, items, equipment descriptions.
- 990 of the 1,118 have a direct u32 pointer (code literal pools across 0x16000-0x4D000 and tables at
  0x100000-0x104FFF); the rest sit inside fixed-length records. A string such as `如月ハニー` is stored once in ROM
  (0x0D027D) though used by many messages: names are also spelled out inside the script archive.
- Debug/test leftovers (`スプライトの表示をするテスト`, `バトルテスト`, `メニュー項目２１`, ESC `[12;12s` sequences) at
  0x0CDD50-0x0CDF40 and 0x0D1A6C, 0x0D31C0-0x0D3A10: likely a debug menu (phase 2 lead).
- Other hits (0x1F0CD8, 0x51F..0x78A) are font charsets or graphics noise, not text.
