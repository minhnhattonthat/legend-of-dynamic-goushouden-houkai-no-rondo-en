# Graphics-text survey

Status: **partial** (tour covered boot -> title -> name entry -> first park dialogue only). Static sweep not done.

| # | Screen | Element | Layer | Source guess | State / how to reach |
|---|---|---|---|---|---|
| G1 | Title | 豪翔伝 logo + small kana/kanji lines (崩界の輪舞曲 subtitle, menu) | BG | packed block (lh5?) | cold boot ~f900 (`work/qa/smoke_orig`) |
| G2 | Name entry | tabs ひらがな / カタカナ / 英語 | BG or OBJ | packed block | boot route + start (`work/qa/intro/s005000.mss`) |
| G3 | Name entry | side buttons 進む / 戻る / 消す / 決定 | BG | packed block | as G2 |
| G4 | Name entry | kana grid | font? (looks like the dialogue font) | runtime font **guess** | as G2 |

Not graphics (font-drawn, verified as SJIS strings in ROM): name-entry confirm box `これでよろしいですか？` / `はい` / `いいえ`
(0x0D3E44), dialogue speaker plates and text.

Decisions: D5 says translate all graphics text; keep the 豪翔伝 logo only because the game has no official English
version (no English release exists).

## To do (rest of phase 1)
1. Tour: main menu (status, items, skills, equipment, save), battle (commands, banners, damage text, result screen),
   shop, map/location banners, chapter cards, game over, ending and credits. Warping needs the phase-2 debug tool;
   until then record what a mashed route reaches.
2. Static sweep: unpack every block in `work/lh5_blocks.json` (and type 1/3 once decoded), render each as gba4 and gba8
   sheets with offsets (`tiles.py render`), read them in chunks, list every Japanese cell here. Print skipped blocks.
3. Log calls to 0x08000F58 during the tour to tie screens to blocks.
