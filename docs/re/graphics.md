# Graphics-text survey

Status: **static sweep done** (every packed block of all three codecs plus every uncovered ROM range); the tour has
covered boot -> title -> name entry -> opening -> first field only. Mid-game screens (chapter cards, game over,
ending, credits, shops, battles) get confirmed by warping once the phase-2 debug tool exists, and in the phase-5
marker tour. Decisions: D5 says translate all graphics text; keep the 豪翔伝 logo only (no official English version).
Confirmed by warp (phase 2): the game-over screen is the English graphic `GAME OVER` (scene `game_over`): nothing to
redraw. The game has no chapter cards (`docs/re/debug.md` §Story state).

## Static sweep (how it was done; rerun after any codec change)
1. `tools/scanpacked.py` -> `work/packed_blocks.json`: 10,225 blocks (type 1: 8,437, lh5: 1,279, type 3: 509),
   including all 119 blocks the unpack log saw. 8,123 type-1 blocks chain end to end into the next block, so they
   are real; low-ratio lh5/type-3 hits may be false positives (rendered anyway).
2. `tools/gfxsweep.py --out work/sweep`: 9,645 unique blocks; skipped and listed in `work/sweep/skipped.tsv`:
   6,196 tilemaps (u16 entries, few high-byte values; maps hold no pixels), 65 SJIS text, 137 tiny, 32 palettes,
   580 duplicates. 3,215 blocks drawn as gba4 (gba8 too when the nibble statistics say 8bpp) on 39 pages.
   `tools/gfxsweep.py --no-lh5 --raw ...` on every uncovered range >= 4 KiB from 0xE4000 (`tools/romcover.py`):
   106 ranges, 6 pages (`work/sweep_raw`), no text found.
3. `tools/sweep_quarters.py` (pages cut into 2x quarters: codex saw nothing on full pages) then two read-only codex
   passes (`tools/sweep_review.sh`, 4 and 2 pages per call), merged by `tools/sweep_merge.py` into
   **`docs/re/graphics_sweep.tsv`** (167 flagged blocks; 121 found by both passes, 45 by one). Codex misses at
   random: 0x3086C8 (large kanji, page 14) was found only by eye. Treat the list as a floor, not a ceiling; the
   marker tour and the phase-8 warps close the gap.

## Flagged groups (block offsets are packed-block starts; details per block in graphics_sweep.tsv)
| # | Blocks | Codec | What | Likely screen |
|---|---|---|---|---|
| S1 | 0x2F3BE4-0x2FEAE4 (81 blocks) | lh5 / t3 | menu captions and framed labels: ステータス, アイテム, おたから, アクセサリー, はずす, 全部はずす, システム, セーブ／ロード, パートナー, バトラーズガッツ, キャラ図鑑, カリスマ, 現在地, クリティカル!!, stat labels (UP, 両性), digits, HP/NEXT/AT/DF HUD glyphs | main menu, status, equipment, save, encyclopedia |
| S2 | 0x2FAD2C | lh5 | game title + subtitle (logo) | title screen (keep 豪翔伝 per D5; translate subtitle 崩界の輪舞曲) |
| S3 | 0x301D08, 0x3086C8 | lh5 | tiny boxed captions; large kanji on white | unknown (title/menu area) |
| S4 | 0x3618EC-0x362BD0 (10) | lh5 | battle commands たたかう / アイテム / こうたい / にげる, NAME/HP, クリティカル!!, battle messages | battle UI |
| S5 | 0x3873C8-0x389998 (40) | lh5 / t3 | battle SFX cut-in font: one 32x32 OBJ kana per block, in the order of the kana lookup 0x0D9C58 (う ふ ん ア ... ボ ピ; ピ = 0x389998, missed by the sweep) | **done** (phase 8): `tools/gfx_sfx.py` redraws 27 blocks as A-Z ! and rewrites their lookup codes (fullwidth); SFX names English in `script/sfx_en.tsv` (<= 4 letters: the cut-in draws 4 sprites). Seen in game: c_effect (4,3) + A shows FOOM |
| S6 | 0x426368, 0x4F23B0 | lh5 | small kana label above a sprite; large curved glyphs | unknown |
| S7 | 0x553FE8-0x7A0DD0 (17) | lh5 / t1 | shop signs and storefront lettering inside map tile sets (kanji, katakana, some Latin "SPORT") | town maps |
| - | 0x491224, 0x4AC9A4-0x4B3298 | t1 | "Z" sleep marks, arrows: not text, no work | sprites |

From the tour (font-drawn or not yet tied to a block):
| # | Screen | Element | Source | State |
|---|---|---|---|---|
| G1 | Title | 豪翔伝 logo + 崩界の輪舞曲 subtitle + menu | S2: BG3 tiles = block 0x2FAD2C at VRAM 0x1D20 (vramfind) | **done** (phase 8): `tools/gfx_title.py` -> gfx/title_2FAD2C.diff, repacked lh5 in place, seen in game (scene retail_title). Logo kept (D5); copyright lines are font text |
| G2 | Name entry | tabs ひらがな / カタカナ / 英語 | in S1/S3 **guess** | `work/qa/intro/s005000.mss` |
| G3 | Name entry | side buttons 進む / 戻る / 消す / 決定 | in S1/S3 **guess** | as G2 |
| G4 | Name entry | kana grid | runtime font **guess** | as G2 |

Not graphics (font-drawn SJIS strings, verified in ROM): name-entry confirm box `これでよろしいですか？` / `はい` /
`いいえ` (0x0D3E44), dialogue speaker plates and text.

## Labels loaded but not displayed by any warp (phase 8 session 16, EN build, cold boot)
Each one is unpacked into VRAM by the game (`tools/lua/unpackat.lua` log) and its tiles rendered from a ppudump
(`tiles.py render`, work/qa/lbl/): the English art is what the game loads; no scene puts it on screen.
- **RESUME** 2FE9B8 -> 0x060019E0 at the title (title_menu2, f1856, with NEW GAME / CONTINUE / PROFILES): the pill
  shows only with suspend data. 大出 row 9 (中断GAME) loads slot 2 through 0x080159B0(2) and prints `データ無し`;
  the title's choice 4 runs the resume 0x0808EF64. How retail writes a suspend is not found (the title doesn't call
  0x080159B0). Render: work/qa/lbl/ppu_title/pills_p1.png (all four pills English, same style).
- **CRITICAL!! / MISS / %UP** 2F5C04 -> 0x06003520 in the shop (m2_shop f365, unused there); battles load the same
  tiles from 362154 / 3621F4, but no warp lands a critical or a miss. Render: work/qa/lbl/ppu_m2_shop/crit_z.png.
- **SHOP** 2F91C4 -> 0x060045E0 in every shop (f377); no shop screen maps it. **SYM** 2F8BB8 -> 0x060003E0 with name
  entry (f358); the screen has three tab slots (HIRA / KATA / ABC, L and R cycle only those). Both checked by
  unpacking the built ROM (session 8); their VRAM tiles are not row-major, so the renders are not readable.

## To do (later phases)
1. Tie each group to its screen: dump VRAM on the screen, `vramfind.py` against the decoded blocks, corrupt to confirm
   (graphics.md §Find the source). S5 and S7 need warps (phase 2 debug tool).
2. Shop-sign tiles (S7) sit in shared map tile sets: redraw in place only after `vramfind.py --others` says unshared.
3. Re-encoders for types 1 and 3 (phase 3) before any graphics re-import.
