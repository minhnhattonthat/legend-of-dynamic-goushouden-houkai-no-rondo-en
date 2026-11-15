# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 8. QA in the emulator: in progress (menu labels done incl. partner stock, shop sell, battle menus; battle effect sprites / SFX cut-ins / S5 / S7 left, then the gate tour). Phase 7 done 2026-11-16.

## Phase 8 session 5 (2026-11-16): sub-screens, list padding fix
- **New scenes** (tools/debug/scenes.txt, button presses after the warp): `m2_sptn` (party edit -> partner slot:
  パートナーストック, はずす / 全部はずす), `m2_shop_sell`, `m1_status_eq` (equipment list), `m1_status_sk` (status
  skill panel), `k_ode_item` / `k_ode_skill` (battle lists). Equipment has no はずす: the buttons live on m2_sptn.
- **Done, each seen in a cold-boot warp on the EN build:** PARTNER STOCK (its last 4 tiles are BATTLER STOCK's: same
  "R STOCK" pixels, dx=3), REMOVE / REMOVE ALL OBJ buttons (+ highlighted twins 2F9C08 / 2F9CBC via
  `gfxlabel.VARIANTS`: index remap 3->2 6->4 7->5 15->13, checked against the originals), shop sell tabs ITEMS /
  GEAR (D9) and 売る数 = QTY, battle item list pill ITEMS, battle command strip 361AE4 (the menu's other states:
  `gfxlabel.STRIPS`, drawn into the block's tiles keeping their gradient; commands seen English in every state).
- **Engine fix (engine.PAD_SITE 0x0E844):** list names are padded by printer p2 with spaces counted in characters
  (window+0x10C = 8 cells): under the VWF a pad advances 3 px, so a shorter English name left the tail of the one it
  replaced ("Remedy   e" in the shop sell list). Now padded while pen < line start + 8 * n (covers 69 px, the
  item_list field). Seen: shop buy/sell, item menu, status equipment list.
- `docs/re/graphics_nodiff.tsv`: flagged blocks done without a diff (Latin/digit art, Z symbols, the sweep's
  malformed 2FDC / 2FDCF0 rows = the 1スキル pill); `gfxleft.py` honours it: 97 left.
- **Found, not done:** (a) the boss's super-move cut-in shows big katakana SFX lettering (ドドドゲーン…, k_ode
  mashed ~f1700): find its block (unpacklog doesn't see the battle-effect loader 0x08011BEF: log that loader or
  vramfind the cut-in frame), redraw per D5. (b) クリティカル!! (362154 / 2F5C04), the "…UP" label (3621F4) and
  3625A8 never loaded in a mashed k_ode/o_battle (Cheer chosen, still no UP shown): they come through the other
  loader; try `vramfind` on ppudumps taken mid-animation (`--shot-every` + `L.dump_ppu`), or draw them by block
  with STRIPS/TILES and verify by forcing the effect.
- **Next, in order:** (1) the cut-in SFX + battle extras above. (2) leftover menu blocks in gfxleft (2F55A4 status,
  2F58B4 save/load, 2F74E4 / 2F7578 small captions on k_jump/party, 2F7B2C spoils banner, 2F8BB8 name entry,
  2F91C4 / 2FA8D4 shop, 2FD740-2FE9B8 from tour2): dump each scene, compare EN vs JP; a block whose label is
  already English through another block goes into graphics_nodiff.tsv with the reason. (3) S5 lettering
  3873C8-389898, S7 shop signs, S3, S6. (4) Gate tour + vqa.sh (codex), inkbox, textcover.

## Phase 8 session 4 (2026-11-16): status and party labels
- **Done, each seen in a cold-boot warp on the EN build:** status (m1_status): ATTACK / DEFENSE / SPEED right-aligned
  against the [AT]/[DF]/[DX] tags (3x5 font), GENDER, SELECT:SWITCH pill; gender value ♂ (D11). Party edit
  (m2_sparty, m2_bsel): SKILLS / SUPPORT OBJ pills (and their twin blocks 2FDCE0 / 2FDE1C), BATTLER STOCK.
- **Gender (D11, provisional):** block 2F6658 holds one kana per tile (こうげき ぼうぎょ すばやさ ➔ % U P せいべつ お
  と ん な ロ ボ _ 両 性). The value is 3 tile numbers from a list built at run time (EWRAM 0x0200C914 after load:
  14 15 00 / 14 16 17 / 18 19 1A / 1A 1B 1C), copied to the BG2 map by the rect blit at 0x080023B4 (tile base in
  r12). The list comes from a second decompressor (0x080CD674, lr 0x08006F1D) that tools/lua/unpacklog.lua does not
  log, so it isn't in work/blocks; not mapped. `gfxlabel.py` TILES["gender"] draws ♂ / ♀ / MECH / BOTH into the
  tiles each value owns (`draw gender`); the こ tile goes blank (status `repeats` waives its value position).
- **Tool changes:** `gfxlabel.py` TILES mode (draw straight into a block's tiles, preview work/gfx/<name>/tiles.png),
  `clear_left` option, OBJ clears may borrow fill from a neighbouring sprite (pills made of several sprites);
  `pixfont.SYM` (♂ ♀). `tools/lua/regwatch.lua` logs registers at every write into a range (who copies a map from
  where). `tools/gfxleft.py`: flagged sweep blocks with no diff yet (131 of 167; 29 of them Latin/digit art = no work).
- Gotchas: a label rect must cover the glyph's own rows (サポート starts on its pill's top border, y 48); a label
  whose tiles another screen shares must use the same rect relative to the tiles on both screens (SELECT:SEARCH on
  the book and SELECT:SWITCH on status share the セレクト tiles of block 2F6828: both rects 52x6, dy=-1); a rect
  touching a cap tile that differs between twin blocks stops the copy into the twin. Old dumps without log.txt
  (jp_m2_sparty was one) fail with "not found in any packed block": `rm -rf` the dump dir and `gfxlabel.py dump`.
- **Next, in order:** (1) equipment screen (アクセサリー, はずす, 全部はずす: 2F990C 2F99C0 2F9C08 2F9CBC 2FA8D4-2FAAB8)
  and システム (2FDCF0), バトラーズガッツ, カリスマ, 現在地, おたから: find each one's scene (scenes.txt; add one if
  missing), `gfxlabel.py dump`, add a SCREENS entry. (2) battle extras S4: クリティカル!! (362154, 2F5C04), the UP
  status label (3621F4), 3625A8 large kana, 362BD0 messages (status labels already copied ATTACK/DEFENSE there):
  find their scenes (o_battle, c_effect...). (3) S5 lettering 3873C8-389898, S7 shop signs, S3 301D08/3086C8, S6.
  (4) Gate tour + vqa.sh (codex), inkbox on choice boxes, textcover. `python -X utf8 tools/gfxleft.py` lists what
  is left; mark Latin-only or unused blocks done in docs/re/graphics.md.

## Phase 8 session 3 (2026-11-16): menu and battle graphics labels
- **`tools/gfxlabel.py`** (the S1/S4 redraw tool): per screen in `SCREENS` (scene from scenes.txt + label rects,
  English, class, palette indices to clear, fill/outline indices). `dump` warps the ORIGINAL there
  (`tools/ppuscene.py`: ppudump + `tools/lua/unpacklog.lua`), `grid SCENE x,y,w,h [bgN|obj]` prints palette indices
  (pick rects/clear sets from it), `info`, `draw` -> `gfx/<screen>_<BLOCK>.diff` + `work/gfx/<screen>/{orig,en}.png`.
  Screen composed with every pixel's VRAM source (`tools/gfxscreen.py`); VRAM->block from the unpack log's dst
  (exact), vramfind only as fallback (it took a duplicate tile from the wrong block once). Checks: a tile that also
  shows elsewhere must not change there (`repeats` rects waive a panel that repeats a label), a nibble written two
  ways, text outside its rect. A label is copied into another block only when that block holds >= 2 of its
  distinctive tiles and the screen doesn't load it (a shared kana tile, ア / る, once carried one label into another).
- **Fonts:** classes `small` (tools/pixfont.py 6-px bold caps, our own, 1-px ring), `btn` (same + drop shadow, the
  game's button style), `tiny` (3x5, where < 6 px/letter), `head` (Press Start 2P 8, OFL). docs/fonts.md.
- **Build:** gfx.insert merges every screen's diff of a block (conflict = error), packs with `lh5.pack(small=True)`
  (cost-based optimal parse, 1-10% smaller than greedy), and a block that still grows moves to free space with its
  32-byte record header; its entry in the sprite archive 0x2F459C is rewritten (`gfx.ARCHIVES`, loader 0x080010A8:
  R = A + u32[A + u32[A+8] + 4i], block = R + 0x20). Type-1/3 blocks re-typed to lh5 boot fine (seen in game).
  Another loader (0x08011BEF, base r7 = block - 0x80, e.g. 0x35F094) is not mapped yet: such a block must fit.
- **Done, each seen in a cold-boot warp on the EN build:** screen-title pills (MENU, ITEMS, PARTY, SPOILS, STATUS,
  SAVE, LOAD, PROFILES), main-menu buttons, item tabs USE/DROP/SORT + ITEM columns, battle commands
  FIGHT/ITEM/SWAP/RUN (k_ode), save/load FILE n, AREA, BATTLER, PARTNER, PROFILES n%, name entry HIRA/KATA/ABC +
  FWD/BACK/DEL/OK, shop BUY/SELL/EXIT, PRICE, MONEY/OWNED/QTY/TOTAL plates (and the field menu's MONEY), book
  SKILLS, VIEW, SELECT:SEARCH.
- **Next (superseded by session 4; (1)-(2) done there):** (1) status (m1_status, bg2 over bg3 texture): こうげき/ぼうぎょ/すばやさ + [AT]/[DF]/[DX] at
  x 8-63, y 88/112/136 (8 rows, gradient 7-10, outline 1): plan "ATTACK"/"DEFENSE"/"SPEED" in `small` over the
  whole x 8-63 (drop the bracket tags); せいべつ x 144-176 y 41-47 -> GENDER; the value おとこ (x 184-207) is one of
  several (おんな, 両性 in block 2F6658): edit those by block, not screen, or dump a female character; セレクトきりかえ
  tiny label. (2) party (m1_party/m2_sparty): 1スキル, 1サポート, バトラーストック (also on m2_bsel). (3) battle
  extras in S4: クリティカル!!, "UP" status labels, 3625A8 large kana, 362BD0 battle messages: find their scenes
  (o_battle, c_effect...). (4) S5 lettering, S7 shop signs, S3/S6. (5) Gate tour + vqa.sh, inkbox, textcover.
- `python -X utf8 tools/gfxlabel.py draw` (all screens) then build: run after any change to pixfont/classes.

## Phase 8 session 2 (2026-11-16)
- **Graphics pipeline works in game:** `tools/gfx.py` applies `gfx/<name>_<OFFSET>.diff` (changed bytes of the
  unpacked block only; no game art in git) to the ROM's block and repacks it as lh5 (type 2) **in place**; the
  game's unpack() accepts lh5 wherever the original codec was (verified: title block 0x2FAD2C was lh5 already, so
  a type-1/3 block re-typed to lh5 is still unproven: boot the first one and look). Our lh5 is smaller than the
  original packer, so most edits fit their slot; a block that doesn't fit needs relocation + its self-relative
  table entry (not written yet: gfx.insert stops with a message). `tests/test_engine.py` ALLOWED adds each edited
  block's slot (`gfx.ranges`).
- **Title (G1) done:** `tools/gfx_title.py draw` (BG3 rebuilt from a VRAM dump of the original title, scene
  retail_title + ppudump.lua into work/qa/p8_title_jp; regenerate that dump first on a fresh clone) -> LEGEND OF
  DYNAMIC / HOUKAI NO RONDO (ruby line) / "Rondo of Ruin" (Cinzel Bold 12, OFL; fonts/ + docs/fonts.md). Logo kept
  (D5). Minor: faint leftover pixels under the top line's right end and a dark plate behind the subtitle (bank-10
  sky has only 2 dark indices): polish, not blocking.
- `tools/dumpblocks.py` decodes all 10,225 packed blocks to work/blocks/ (47 MB) for
  `vramfind.py X.vram.bin work/blocks --fmt gba4`: the way to tie each S-group of the survey to its screen.
- Visual-QA gate under Orca: `docs/visual-qa-brief.md`, `tools/tour_sheets.py` (EN | JP per scene from two
  warp_all runs), `tools/vqa.sh` (codex exec -s read-only per qa_gate chunk -> work/qa/verdicts/). Run the gate
  tour **after** the graphics rows are done (every graphics change invalidates it): warp_all on the EN build into
  work/qa/tour_en and on the original into work/qa/tour_jp, tour_sheets.py, qa_gate init/todo (--size 12), vqa.sh.
- A preliminary warp_all of the pre-title-gfx EN build ran into work/qa/tour_en (--states, so work/states/ was
  regenerated from it); ending_credits and retail_newgame failed only for frames (now in warp_all MIN_FRAMES).
  Seen there: credits pair "Creator / Go Nagai  Ken Ishikawa" reads fine (o_ending); battle names/HP/DP fine.
  Still Japanese, all graphics: battle commands たたかう/アイテム/こうたい/にげる (S4, k_ode), item menu header
  アイテム, tabs つかう/すてる/せいとん, column heads アイテム/NUM (S1, m1_item).
- **Next, in order:** (1) S1 menu captions and S4 battle UI: per screen, ppudump on the original
  (`--script $SKILL/scripts/lua/probes/ppudump.lua` with the warp), `vramfind.py ... work/blocks`, then a generator
  like gfx_title.py (these are small framed labels on plain tiles: render with Silkscreen 8 px, clear the label
  rect, write the diff); the first type-1/type-3 block re-typed to lh5 must be booted before doing more. Check
  `vramfind.py --others` for tiles shared between screens. (2) S5 lettering, S7 shop signs (warp to the maps).
  (3) The gate tour (above) + vqa.sh verdicts, inkbox on choice boxes, textcover (needs a writer-side id log:
  dialogue is lh5-packed, so first-byte ROM reads can't prove coverage).

## Phase 7 review fixes (2026-11-16; review in ../.harness/reviews/...-phase7.md)
- I1: r0CD95C (ASCII -> fullwidth lookup, 2 bytes per code, read by 0x08003DE4) was translated as text; now a
  `romstr.DATA_SPANS` entry (status data). Test: every data span is byte-identical in the build.
- I2: lint fails on empty English unless listed in `script/keep_jp.txt` (the 145 SFX sprite names, phase 8 graphics).
- I3: wave-1 cuts restored where the full form now fits (fixes9: Sword, Death Mask, Shuriken, Lightning Flare,
  Jiro Shutendo). The engine route was measured (D8): a narrower font saves 2-5 px, too little. D8 is provisional;
  the remaining 55 short forms are listed in `docs/short-forms.md` for the user's sign-off.
- I4: the battle banner messages are stpcpy chains with no separator: "<enemy>" + r0D1FAC (100-byte stack buffer),
  "<item>" + r0D2234 (32-byte buffer), amount + r0D2270. The English read "Geninappeared!": the suffixes now carry a
  leading space (`lint.EDGE_OK`), and `windows.json` `composed` makes the lint check name + suffix against the
  buffer and the 230-px banner. The credit pairs have no code-literal reader (script-record field): check in game.
- I5: stub last lines fail the lint; `batches.py wrap` re-wraps balanced (193 dialogue entries); meant ones in
  `script/keep_stub.txt`. Minors: jp_left `--known tools/jp_known.txt`; check.py runs `batches.py check` (now 3 s);
  short forms keep the Avoid check; tests for stale readers and per-table write counts.
- Also: r0CFF38 "Kisarag" -> "Kisaragi Mansion". The "<item>を<n>個" message (0x08017FCE, RAM buffer 0x03004EE0)
  reads "Item:3pcs": check where it shows in phase 8.

## Phase 7 (done)
- `build.py insert_rom_strings` relocates every translated ROM string longer than its slot: written after the
  archives (0x800000+), each pointer site in its `ptrs` asserted to hold the old address in the original, then
  repointed (185 strings: 105 debug map names, 25 rec18, 26 code-pool, char/enemy/skill names). The lint treats
  bytes as soft when a string has pointers. `tests/test_build_en.py`: English build, romdiff with the write log,
  writes only in allowed ranges or a relocated string's own pointer sites, every relocated pointer reaches its text.
- All LONG ids merged (`tools/long.py` lists any left: none). Restored to glossary forms: debug map names
  (fixes6/fixes7: Science City, Lost Forest, Hill of Beginnings, Mirage Castle, Harenchi Gakuen, Dark Temple...),
  char_name full names (Immortal Corps C, Mechanical Beast A, Reaper Police 3...).
- Px-limited names got short forms (D8): `script/short_forms.tsv` (glossary check accepts exactly those) and
  work/qa/review/fixes5.tsv (rec18 people as "Initial. Surname", char_short "Kekko", "Aphro. A", skills
  "G.Tomahawk", "H.Boomerang", "RustHurricane", item "PsychoJenny"). Wave-1 px abbreviations (K.Sirene, Maru G.,
  Cut/Stars/Mask, Bolt/Blunt/Slash, book cuts) stay under D8: their limits are field px / book lines, not bytes.
- **Phase 8 must check (not linted in px):** the 26 relocated code-pool strings: credit staff pairs (table
  0x0D24F4-0x0D29C0, drawn by the printer in mode 2, ending_credits scene; now up to 36 bytes vs 27) and book
  series titles (pool 0x103xxx: "Goushouden", "Susano-oh"); enemy names now longer than their JP room are
  sprintf'd into "<enemy> appeared!" (battle banner; buffer size unknown); char_name has no measured field. The
  469 code-pool strings still have only byte limits (no px box): verify them on the phase 8 tour sheets.

## Review (read-only codex passes; no nested workers under Orca)
`python -X utf8 tools/pairs.py` (pairs files, work/qa/review/pairs/), `R=DIR JOBS=4 sh tools/review.sh [bNNN ..]`
(codex exec -s read-only per batch, prompt tools/review_prompt.txt; skips batches whose report exists),
`tools/review_findings.py [--rep DIR] [--tsv OUT]`, fixes hand-written as `id<TAB>EN` in
work/qa/review/fixesN.tsv and applied by `tools/apply_fixes.py` (whole entries by id, no pattern rewrites), then
`batches.py merge ... --overwrite` (`--partial` for b056-b086). A dialogue merge of all 55 batches takes ~3 min.
- Round 1 (work/qa/review/reports/, all 86 batches): 1 Critical + 92 Important; all adjudicated in fixes1/fixes2
  (one rejected, noted there), merged; 72 Minors in docs/polish.md. Build, check, smoke ok after.
- Names now follow the ROM's own kana short names (glossary "Decisions from earlier batches"): Nantomo Iyahaya
  (was Nanyu/Nanto), Kitani (was Onitani), Hatesate family, Koja Hatesate (was Nijija Hatesa), Daiko Hoin (was
  Hoin Taishi), Eisanbo Daihon (was Omoto Eisanbo), Hakase (was Hakayo). speakers.tsv updated to match.
- Round 2 (work/qa/review/reports2/, the 45 batches touched in round 1): 18 Important (ci2.tsv), fixed in
  fixes3/fixes4. Two rejected: the reviewer wanted Mido -> Shindo and Daihonei -> Daihon, but the ROM's kana short
  names bind, so the full names now follow them: 身堂竜馬 Ryoma Mido, 大本栄惨坊 Sanbo Daihonei (大本営参謀 pun).
  "Discharge"/"Blizzard" (r0DCA54 r0DCA5C r0DCB30 r0DCB38) are now LONG for the 7-byte skill_name field: relocate.
  Use JOBS=3 for review.sh: six codex processes at once ran the machine low on memory.
- Round 3 (work/qa/review/reports3/, the 14 batches changed in round 2): 0 Critical/Important, 10 Minors.
- Book cut added: series title "Iyahaya" for イヤハヤ南友 (B00.88 B00.89 B01.29 B01.39 B01.40): "Iyahaya Nantomo"
  is 112 px vs the 108-px book line and the JP keeps lines 2-3 blank.

## Phase 6 batches
`python -X utf8 tools/batches.py split|check|merge|fit` (docs/translator-brief.md). Batches were split once
(b001-b086; never re-split: `split` only adds ids not yet batched). Map: b001-b055 dialogue f00-f53 (b053 = tail
of f51), b056-b058 book, b059-b061 desc, b062 effect, b063-b066 place, b067-b076 rom misc + map names, b077-b079
char names, b080-b082 skills, b083-b085 items (rec18), b086 item descriptions.
- Merged: b001, wave 1 b056-b086 (2608 entries translated, lint 0 errors). Batch inputs and outputs are tracked in
  git now (`work/tl/`, un-ignored). `work/tl/names.tsv` (`tools/names.py`) = translated ROM/place names for wave 2.
- **LONG, left untranslated (105 ids):** `merge --partial` skipped ids whose full English doesn't fit the in-place
  byte limit or the field px: b070 (Hill of Beginnings map names), b073 (credit staff names / series titles), b078,
  b079, b081, b082 (names wider than char_short 48 px / skill 72 px), b084, b085 (49 name records r0DD8B8-r0DDD24),
  b086 (enemy names). Their full English is in `work/tl/bNNN.out.tsv`. Phase 7: relocate these strings (byte limits
  are only "in place") and widen fields per D4, then `merge` those batches. `batches.py merge --partial` prints them.
- **Abbreviated by wave 1 to fit (against D4, restore after relocation):** char_short names (K.Sirene, I.Kaiser,
  M.Ashura, Maru G., Jiro for 手天童子郎, Susanoo), skill words (Cut for 剣, Stars for 手裏剣, Mask for 死の面,
  Murakumo, Bolt Flare), item element words (Bolt/Blunt/Slash, Amulet/Stud/Band), debug map names (SciCity,
  LostForest9), book series titles ("Enma-kun" for Dororon Enma-kun) and book LONG cuts B00.20 B00.70 B00.82
  B01.03 B01.07 B00.08 B01.16.
- Wave 1 readings still unsure (reviewer: check against names.tsv and speakers.tsv): 果扨胴下 (Doshita Hatesa vs
  Doka Hatesate), 大本栄惨坊, 無幻大権, 法印大子, 墓世, 女蛮子 (Banji / Banko / Sukebanko), 真神, 鬼谷妖次郎;
  term drift merged before the glossary rows: "Phantom Castle" in items (glossary: Mirage Castle), "Death Police"
  in book B01 (glossary: Reaper Police). Fix these in the review pass.
- Wave 2 (b002-b055) was translated by one worker in a single pass (Orca refused subagents), all merged. Calls
  made there, now in glossary.md "Decisions from earlier batches" and new term rows: Demon King (Grade) vs Demon
  Lord Dante, Kigoku World, Kibutsu Clan, Dimension Prison, Moon of destruction / Sun of rebirth, Precog Clan,
  Yokai Patrol, Iyahaya / Hatesa families, Banji Suke, Ryoma Shindo, Beehive Nyudo. speakers.tsv: added Garo,
  Eriza Hyo, Tomahawk / Scissors Panther, Nijija Hatesa, Big Girl, Security Guard; 蛮子 Banko -> Banji, 果扨胴下
  -> Doshita Hatesa.
- Unsure (reviewer to confirm): 45.06 and 53.43 have an empty JP body (name tag only); the check refuses empty
  English, so they hold "...\n" (a box with "..." may now show where the JP shows an empty one). 男男子 read as
  "Danshi Otoko" (51.93, 52.10-11). 法印大子 as "Taishi Hoin", 豹絵里座 as "Eriza Hyo", 墓世 as "Hakayo".
  Item/enemy data (wave 1) still says HiveMonk (LONG, phase 7); dialogue says Beehive Nyudo. 鬼谷 is Kitani everywhere now.
- Review done (section "Review" above; names later changed in round 2: Ryoma Mido, Sanbo Daihonei). The wave 1
  unsure readings and term drift above were settled in round 1 (kana readings; Mirage Castle, Reaper Police); 真神, 男男子 have no kana form and stay as is.
- In-game pilot view not done: `retail_newgame` stops at the name entry (an empty name won't confirm: type a
  character first). Phase 8 needs a name-entry route or a warp past it.
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
      menu. Credits: the staff/series pairs (0x0D22E8.., reached from script-record fields such as 0x104090) are
      text drawn by the printer; any logo or title art in the credits is graphics (phase 8 checks both).
    - The "ASCII skill name blanks the battle skill list" bug was a shot-timing artefact (the window opens 0-6 frames
      later in some builds; shots at 2696-2700 catch it empty). `tools/bisect_marker.py --ink FRAME:X,Y,W,H[:N]`
      bisects a visual predicate now.
    - Script files are malloc'd at their unpacked size (no fixed buffer; ~148 KB heap free on a field map);
      build.py caps a file at 32 KB. Codes: `{g}` = obtained item name / money amount; `{!R}`...`{!W}` wrap
      transceiver / remote speech (printer style); keep them where the JP has them (lint checks counts).
- **Phase 8 so far:** k_ode warp (work/qa/p8_k_ode) draws the multi-enemy banner "Enemies appear!" cleanly. Still
  to see in game: a one-enemy battle ("<enemy> appeared!" with the new space; the longest, "Mechanical Beast Baron
  Ashura appeared!", is 39 bytes, x clamps to 0), a steal ("<item> stolen!"), the credit pairs (o_ending /
  ending_credits warps, work/qa/p8_o_ending has a first run), and the "<item>:<n>pcs" message (0x08017FCE).
- **Next (phase 8, `references/emulator-qa.md`, `references/graphics.md`):** tours with contact sheets and
  visual-QA verdicts (do them as a fresh read-only pass or `codex exec`: no nested workers), graphics text, inkbox,
  textcover; the "Phase 8 must check" list above. Effect reader 0x0809CC54 (from 0x09E9BA) not seen drawing.
  - Code-pool px mapping (469 strings, no record table): `tools/fields.py work/qa/fields` already maps 825 drawn
    ids to window / x / right-hand neighbour; turning that into per-id px limits would let the lint check them.
  - Also for phase 8: banner and other centred lines are centred by byte count (x = 120 - 7 * bytes in the
    battle banner), not by VWF width; SFX names (`sfx.json`) probably sprites via the kana lookup 0x0D9C58; the
    graphics-text survey groups; `{g}` width in game.
- **Open bugs:** none.
- **Waiting on the user:** (not blocking) sign-off on the D8 short forms in `docs/short-forms.md`: keep each, give
  another, or ask for the column re-layout. The run continues with them as shipped.
  (not blocking) D9 graphics-label wordings (docs/decisions.md): HIRA/KATA/ABC tabs, FWD/BACK/DEL/OK, PROFILES for
  キャラ図鑑, SPOILS for バトル収穫; the battler/partner counts on the save screen use the 3x5 font.
  (not blocking) D11 status-screen gender values ♂ / ♀ / MECH (ロボ) / BOTH (両性): symbols because the values share
  tiles; full words need the run-time tile list mapped first.
