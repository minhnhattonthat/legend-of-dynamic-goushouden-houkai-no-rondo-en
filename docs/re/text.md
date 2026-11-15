# Text

Encoding: **Shift-JIS** (cp932), fullwidth only in practice (verified: dialogue in an EWRAM dump decodes as cp932;
the font charset lists only double-byte codes). Half-width 0x20 (space) and some ASCII appear inside control codes.

## 1. Script archive (story dialogue) (verified: decoded, the opening dialogue found in RAM)
- Root `X = 0x08104DC0`, referenced from code literal pools at 0x7DDC, 0x80BC, 0x8348, 0x8600, 0x17E8C.
- `X+0`: u16 count 0x429B (17,051), then 17,051 u16 entries: message id -> sequential message number (0xFFFF = none);
  5,363 ids are used, numbers 0..0x14F2. number / 100 = file, number % 100 = slot (**verified** phase 4: the 5,363
  numbers are exactly the 5,363 used slots, one id each; `msg` field in `script/archive/*.json`).
- `X+0x8538` (ROM 0x10D2F8): 54 entries `{u32 offset from X, u32 unpacked size}`; files start at X+0x86E8 (0x10D4A8)
  and are bare lh5 streams (no header), packed back to back (the next offset = this offset + compressed length,
  verified for all 54). Archive ends at 0x132E74.
- Each unpacked file: 100 x u32 offsets, then the messages. 5,400 slots, 5,363 used; the 37 empty ones are file
  53's slots 63..99. **verified** phase 4: parsed as Shift-JIS, every used slot is exactly one string with a single 00 at
  its end (the "file 53 garbage" and "5,699 00s" of recon came from byte-wise counting through SJIS trail bytes).
- The archive fills its ROM slot exactly (0 bytes slack); `tools/lh5.py` frees 121 bytes when it re-encodes every
  file. Any growth needs relocation (phase 7; 5 pointer sites in `archive.POINTER_SITES`).
- At run time a whole file is unpacked into EWRAM (around 0x0201D000..0x0201FFFF; the opening file sat at 0x0201D66C).

## 1b. Five more archives right after it (found phase 5, NOT YET EXTRACTED; verified: decoded with lh5 + split_file)
Same format (u16 count, count x u16 id -> number, then nfiles x {u32 offset, u32 size}, lh5 files of 100 slots),
read by 0x0800FE88(id, archive, 1, dest) (lh5 0x08006538 into a heap buffer, then strcpy of the slot). Back to back:

| base | ids | files | msgs | end | literal pools holding 0x08000000+base | content |
|---|---|---|---|---|---|---|
| 0x132E74 | 149 | 2 | 148 | 0x1348F8 | 0xADD8C | character book (キャラ図鑑, m1_book): name, 2 blank lines, description |
| 0x1348F8 | 3 | 1 | 1 | 0x13492D | none found | one test line (この物語の主人公); probably unused |
| 0x134930 | 293 | 3 | 290 | 0x13531E | 0x8843C, 0x9A548, 0xADE00 | item / skill descriptions (味方単体のＨＰを３０程度回復) |
| 0x135320 | 93 | 1 | 92 | 0x1355DC | 0x9CDF4, 0x9CE90, 0xA38EC | equipment effects (ＤＰ１０％ＵＰ\n精神防御＋５) |
| 0x1355DC | 313 | 4 | 312 | 0x135E6B | 0x96EEC, 0x96F98, 0x97328, 0x973D4 | map / place names (日本マップ) |

0x135E6C onward is other data. Found by tracing the book text: menu printer 0x0800E3D0 <- wrapper 0x0800E87C <-
0x080ADBD4(window, ?, ?, string) <- 0x080ADD1E, which fills a stack buffer from 0x0800FE88 with archive 0x08132E74
(`tools/lua/srcprobe.lua`). Search for the flag-masked forms too before repointing (pipeline §Checks).

### Message format (complete single-byte census, SJIS-aware parse of all 5,363 messages, phase 4)
| bytes | count | text form (`tools/sjis.py`) | meaning |
|---|---|---|---|
| `0D` | 12,127 | newline | line break; the first line of a dialogue message is the speaker name (e.g. `不動明` CR `「黒い月が…」`) **guess** from RAM view |
| `00` | 5,363 | (terminator, not in the text) | end of message, one per slot |
| `\p` (5C 70) | 1,481 | `{p}` | **verified** phase 5: the hero's name (34.10 `{p}` CR `ここには…` shows the name tag `メイン`, the default name r0D18BC; the marker build shows `D18`). Not a page break |
| `\s` (5C 73) | 325 | `{s}` | **guess** (phase 5): the heroine's name (`\p` is the hero = メイン "main"; the other default name is サブ "sub", r0D18C4) |
| `\g` (5C 67) | 2 | `{g}` | **guess**: item-get name (`{g}を手に入れた`, 00.01) |
| `!R`, `!W` (21 52 / 21 57) | 119 / 11 | `{!R}` `{!W}` | **guess**: inline codes (`了!R明`, `着く!W`, and `\p` CR `!R(…！)` at a line start) |
| `20` | 5,213 | space | half-width space (padding/alignment) |
| `!` alone, `(` `)` `:` | 1 each | literal | `\p!` CR in 29.10 (stray `!`), `!R(…！)` in 34.63, `朱紗:` in 29.10 |
| `09` | 1 | `[09]` | `兜甲児<09>大変な` (10.01) |
No other single byte occurs; there are no invalid double-byte pairs. Choices are plain strings in a message
(`はい` `いいえ` after `！！ `). Confirm `{p}` `{s}` `{g}` `{!R}` `{!W}` in the marker build (phase 5).

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

### Phase 4 extraction (`tools/romstr.py`, `tools/extract.py`; **verified** by `tests/test_extract.py`)
- String sections: 0x0CD95C-0x0D5000 and 0x0D9000-0x0DF000 (`romstr.TEXT_RANGES`; 0x0CD000-0x0CD95C is code).
  Strings are 4-aligned with 00 padding (compiler rodata), interleaved with binary tables.
- Pointer words live in code + tables below the archive (0..0x104DC0) and in the record tables at 0x7B311A-0x7ED9E0
  (not packed; 1,000 strings are pointed only from there). Words inside packed assets hit string addresses by chance
  (48 hits, all mid-string or misaligned), so they are not counted. No pointer lands inside a string.
- 1,849 pointed strings extracted to `script/rom/PPPPPP.json` (id `rOFFSET`, `ptrs` = sites, `max` = bytes in place
  up to the next 4-aligned boundary); 20 are ASCII only (format strings `POS:%d`, `SE:%d`, `DYNA_RPG_INIT`,
  `DUMMY`, English debug test lines) -> status `data`. Full-width-only ones (`ＨＰ＋２５％`, `ＬＯＡＤ　ＧＡＭＥ`,
  `？？？`) are text.
- 0x0D9C58-0x0D9CF8: one katakana per entry, pointed from a table at 0x104D40 (reverse order): a kana -> sprite
  lookup for the onomatopoeia, status `data`.
- Onomatopoeia records at 0x0D9CF8-0x0DAFB8: 150 x 0x20 `{u32 id, u32, u32, char name[20]}` (base pointer at
  0x0C63B0); 145 named, in `script/rom/sfx.json` (id `xNAMEOFFSET`, `rec`). **guess**: drawn as sprites through the
  kana lookup above, so English needs graphics work.
- 0x0CE010-0x0CE154: the ASCII -> fullwidth map rows (font.md) are status `data` (`romstr.DATA_SPANS`): the first
  marker build replaced them and every box went blank.
- `extract.FULLWIDTH` (r0D18BC / r0D18C4, the default hero / heroine names): read two bytes per char, so they are
  inserted as fullwidth (`sjis.fullwidth`); ASCII there blanked the name tag. Player names typed in game are
  fullwidth too; they draw with the VWF widths.
- Debug-menu strings (`デバック（菊池）ＭＥＮＵ`, `バトルエフェクトマスク１`, the ESC-sequence block at 0x0D3641) are
  extracted like the rest; flag the debug-only ones in the marker build.
- Coverage: no run of 2+ kana/kanji at any alignment in the sections outside an extracted string; outside the
  sections and the archive, no pointed string with 2+ kana and no unpointed one with 4+, except the font charset
  0x1F0CD8 and graphics bytes at 0x520422.
