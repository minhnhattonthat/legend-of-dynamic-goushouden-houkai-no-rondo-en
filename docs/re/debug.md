# Debug tool (phase 2)

The game ships its developers' debug menus intact; only the call into them is gone. `tools/debug/warp.lua`
re-enables them in emulator memory (the ROM file is never changed) and drives them by overwriting registers at hook
points, so every scene below is reached from a cold boot with no save and no play.

## How the debug menu is reached (verified: boots, every entry opens)
- `main()` at 0x0807E454 ends with `bl 0x0807E2F4` at ROM 0x7E48A (bytes `FF F7 33 FF`). 0x0807E2F4 is the retail
  loop (title -> new game / load / ...).
- 0x0807E370 is the debug top menu デバックＭＥＮＵ (table 0x08100EC4, 8 rows, no callers). Row 0 製品版 calls the
  retail loop, so redirecting the BL to `FF F7 71 FF` (`bl 0x0807E370`) loses nothing.
- The top menu also checks ROM 0x087FFFFB for `200`; if present it copies a 24-byte string from 0x087FFFE7 into the
  header line (the build timestamp `Mon Sep 01 17:33:13 2003`).
- Jump table of the top menu at 0x0807E3EC: 製品版 0x0807E2F4, 大出 0x08080260, 努 0x0807FCE8 + 0x080166A0,
  コ 0x0807FCE8 + 0x0808F758, 菊池 0x0807FCE8 + 0x080C4430, 素材１確認 0x0807E49C, デバックデータ 0x0807FCE8,
  セーブデータ消去 0x08009534.

## Hook points used by warp.lua (verified)
| what | address | register |
|---|---|---|
| list menu A (top, 努, 大出 ...) | entry 0x08007570, return `bx r1` at 0x080077AA | r0 = chosen row |
| list menu B (コ, テスト1/2 ...) | entry 0x08007978 (r0 table, r1 cursor), return `bx r1` at 0x08007BCC | r0 = chosen row |
| field test (努 row 0) | 0x080167A0; A pressed -> 0x08016AEC | r9 = map index |

Field test: up/down -1/+1, left/right -10/+10 (r9), A loads the map through a jump table at 0x08016B10 (ids
0..0x11C; above that a default path that still loads, e.g. 300). Names: 0x137 SJIS pointers at 0x080FA814
(`tools/debug/maps.tsv`). Debug flag 0xFAD is set when L (key bit 9) is held on A, cleared otherwise (meaning unknown).

## Story state (partly verified)
- Event flags: bit array at 0x03004AA0; flag n = halfword (n >> 4), bit (n & 15). Set 0x08017B94(n), clear
  0x08017BBC(n), clear all 0x08017BFC. 0x08017BE4 clears 0x200 bytes at 0x030048A0 (all zero in every state seen).
- The opening sets flags 0x5B, 0x64-0x66 and 0xF63 by the first free-roam field (`tools/lua/flagdump.lua` diff).
- The game has no chapter cards: the strategy guide's contents list a common route then branches ("ルートの決定"),
  and nothing in the ROM strings or the opening tour shows a chapter title. Route-start warps need the flags each
  branch sets: add them when the event scripts are read (phase 4/5).
- Party: active trio records at 0x02007264 (0x44 apart, u16 HP at +0); battler stock 32 records at 0x02007520
  (0x44 apart, id at +0, HP at +4, DP at +0x10). Battle units are heap records 0x108 apart (0x0200D2E8 in the コ ODE
  battle, 0x0200DCA8 in a field battle): not at a fixed address.

## Battle state (verified: RAM dumps across a field battle, game over reached)
- Battlers: a heap block of 6 records 0x17C apart (0x020093B0 from one state, 0x02009390 from a cold-boot warp):
  slots 0-2 the trio, 3-5 the enemies; u16 HP +0, DP +6, 1 at +0xA, Lv +0x10, 16 zero bytes before HP. Copies of
  the trio's records sit 0x1A4 apart further up (display copies); writing those does nothing.
- Writing 0 to a battler's HP (or to the 0x108-stride unit records) is ignored: the battle still ends in a win. A
  battler only falls to real damage. Stock size does not matter: with stock present the trio falling still gives
  GAME OVER (こうたい opens the battler swap screen instead).
- **Game over** (scene `game_over`): `wipe` step in warp.lua: party record HP = 1, walk in 迷いの森１ (map 257) until
  an encounter, pin the enemies' HP each frame, mash A; the trio dies to enemy hits. `GAME OVER` (already an English
  graphic in the original) shows about +60..+120 frames after the third battler's HP hits 0, then the game returns
  to the field. No game-over text exists in the script archive or the plain ROM strings.

## Proof run (all 340 scenes, verified)
`warp_all.py --frames 3000 --states` on the original ROM: 47 named scenes + map_000..map_210 in `work/qa/warp_all/`,
map_211..map_310 in `work/qa/warp_all_rest/` (both 0 failed; sheets in `<out>/sheets/`, read by eye). Spawns that
look wrong but aren't warp bugs (map loaded, game alive):
- map_168 (hotel 1F) shows only a map edge; map_170 (hotel 3F) black at the spawn point; map_201 (魔王の城Ｄ) hero on black.
- map_267 is 黒ＢＧ ("black BG"): an all-black backdrop map by design.
- map_218..map_232 (家・風呂場1A..3E) are 15 variants of one bathroom; they look identical.
- map_290 (ダンテ５Ｄ) starts an entry event: a メイン dialogue box (「ここには…」) is up in the shot, so it's a free
  dialogue sample for phase 5/8.

## Not reached yet
- Route starts (see story state).
