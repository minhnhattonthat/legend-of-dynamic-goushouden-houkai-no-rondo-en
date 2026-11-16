# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 8. QA in the emulator: in progress (visual gate green on build 9045e3a5 (waived hotfix of 994585e0); text coverage: every ROM string and archive shown, dialogue 3068/5363: msgview c09-c15 left). Phase 7 done 2026-11-16.

## Phase 8 session 16 (2026-11-16): every ROM string and archive forced, labels triaged
- **`tools/coverage.py`**: coverage over tour_en3 + msgview + forcearc + forcestr, grouped by kind (`--list KIND`
  for ids, `--missing-out F`). The gate stays `$SKILL/scripts/textcover.py` on one LOGDIR.
- **`tools/forcestr.py`** (new): m1_item's list draws names with the menu printer 0x0800E3D0(win, r1 = string) from
  f400; forceview swaps r1 for each ROM string's build address (LOOP reload at f399, ~13 per reload). Run with
  `--chunks 8`: **all 1,332 non-waived ROM strings shown** (box messages, battle, credits, save, data-table names).
  Shots (`--shots`) show the names drawn in the item list. Proves read + drawn by the game's printer, not own-box fit.
- **forcearc:** desc 290/290 (per-id budget 150: 120 ran out), place 312/312, book/effect done before. **All
  archives covered.** Remaining coverage = dialogue only (msgview c05..c15 running when this was written).
- **Load box r0D3C60** (new scene `m1_load_yn`: save, soft reset, load, A): "Load this data?" ran onto the box's
  right border (JP ？ ends inside it) -> "Load data?". **Build 9045e3a5** (check ok, smoke ok, strings.tsv
  addresses unchanged): box seen in a cold-boot warp vs the original (work/qa/yn/cmp3.png), inkbox ok;
  `qa_gate.py waive` recorded for this build, **`qa_gate.py check` exits 0**.
- **msgview killed by the memory reaper at c09** (c00-c08 done: dialogue 3068/5363 shown). **Next:** rerun
  `python -X utf8 tools/msgview.py --chunks 16 --jobs 1 --resume` (skips c00-c08; ~7 chunks x ~8 min) with no
  other Mesen running, then `python -X utf8 tools/coverage.py`: any dialogue still missing -> rerun those ids or
  waive with a reason. Then the gate itself: gather the log dirs into one LOGDIR (textcover.py takes one) e.g.
  `textcover.py work/qa build/goushouden_en.strings.tsv --waive docs/text_unshown.tsv` (work/qa also holds logs
  of older builds: fine for archive/id-map ids, check before trusting it), and Phase 8 is done -> phase 9.
- **Erase prompts r0D3B84/BA0/BDC** (group 7 of the per-screen string table 0x08104618, getter 0x0808F7C0, a retail
  helper: reachup's "debug" root for it is wrong): drawn by the title's Yes/No widget 0x080C2200; no combo held at
  the title or from boot (15 tried) opens it; debug top-menu row 7 erases with no prompt. Covered by forcestr only;
  their Yes/No columns follow the session-12 rule (original はい/いいえ columns).
- **Graphics labels never displayed by a warp** (RESUME, CRITICAL!!/MISS/%UP, SHOP, SYM): each is unpacked by the
  game into VRAM in the EN build; RESUME and CRITICAL/MISS renders read English. Details + evidence paths in
  docs/re/graphics.md §Labels loaded but not displayed. Name entry has only 3 tab slots (SYM never shows).

## Phase 8 session 15 (2026-11-16): tour finished, visual gate green, archive forcing
- **Tour tour_en3 done** (356/356, `--resume`, log work/qa/tour_en3_run3.log). `tour_sheets.py`, `qa_gate.py init`
  (76 sheets changed), 7 chunks judged by codex (`JOBS=2 sh tools/vqa.sh`; old verdict files renamed `s13_chunk_*`
  so vqa.sh doesn't skip the new chunk names: **do this again before every new todo**). Only issue: the pharmacy
  plate MAMII / DRUGS vs glossary "Mamii Pharmacy": ruled the plate form (5 letters per line; glossary note +
  visual-qa-brief standing non-bug), work/qa/verdicts/recheck_004.tsv. **`qa_gate.py check` exits 0** on 994585e0.
- **New `tools/forcearc.py`**: forces every book/desc/effect/place message through 0x0800FE88 (forceview with
  FV_IF = the archive's base in this build, LOOP reload). Scenes (FVCALL probes): book m1_book f419, desc m1_book
  f403/f458 (m1_status_sk's call follows a scripted SELECT the reload doesn't replay), effect m2_sptn f633 (partner
  stock box), place m1_load f400. Shots checked: each draws in its own box. Run result: **book 148/148, effect 92/92,
  desc 270/290, place 11/312** (killed by the memory reaper). Rerun `python -X utf8 tools/forcearc.py --only
  desc,place` (it has no resume; ~15 min).
- **msgview:** c00-c04 done, c05 118/336 (killed). Rerun `msgview.py --chunks 16 --jobs 1 --resume` (~1 h left).
- **Field box messages (r0D00C8..r0D1400, ~125: joins, keys, Yes/No, Save):** 0x0807C970(str, r1, r2) is strlen +
  malloc + copy + 0x0807CA44(buf, r1, r2, 0); its twin **0x0807C9D0(id, r1, r2)** gets the buffer from 0x08017C14(id)
  then calls the same 0x0807CA44 at 0x0807C9F0. Plan: forceview FV_ADDR=0x0807C9E2 (just after 0x08017C14 returns),
  FV_REG r0 = each ROM string's address (strings.tsv), in a scene whose event uses 0x0807C9D0 (check map_290 first
  with FVCALL at 0x0807C9E2). Event code calling 0x0807C970 is per-map (126 BL sites 0x08023C80..0x080657FA).
- **Still open:** battle messages r0D1FB8..r0D2270, credits names r0D2BB0.. / series r0D2304.. (ending_credits
  hold), save/erase/load r0D3B84..r0D3F10, data-table names 0DB-0DE (~910: swap the pointer at a printer call in a
  list screen; forceview logs r3 now too).
- **Memory:** the reaper killed both runs again while another project's 4-6 Mesen (onmyou-taisenki, ~615 MB each)
  ran. Check `Get-CimInstance Win32_Process -Filter "Name='Mesen.exe'"` before a long run; ONE job at a time.

## Phase 8 session 14 (2026-11-16): tour resumed, text-coverage triage
- **Resume flags:** `warp_all.py --resume` keeps scenes whose shot + WARP_DONE log exist (same ROM and probes!);
  `msgview.py --resume` skips chunks already MSGVIEW_DONE with the same ids. tour_en3 was finished this way
  (log work/qa/tour_en3_run2.log). **Killed again by the low-memory reaper at 332/~356 (after map_286)**: rerun the
  same command with `--resume` (it skips the 332 done scenes; only ~24 left, a few minutes), ONE job, nothing else.
- **Coverage now (tour_en3 + msgview c00-c02, before waivers):** 980/8055 shown. Missing by kind: dialogue 4622
  (msgview covers them: run `msgview.py --chunks 16 --jobs 1 --resume`, c00/c01 done), book B 147, desc D 288,
  effect E 91, place P 311, ROM strings 1615.
- **Waivers:** `docs/text_unshown.tsv` (518: 78 not text = `status data` or blank, 439 debug-only, T00.00 unused).
  Debug-only evidence: field-test name list 0x080FA814 (0x137 ptrs, only the debug field test), test-menu strings
  r0D3008..r0D3B60 (`tools/reachup.py`: every reference roots at the debug コ menu 0x0808F758), developer sprite/BG
  test strings, the debug top-menu header. `tools/reachup.py ID..` walks pointer -> loader -> BL/pointer callers to
  root functions; its table-base guess (nearest referenced word <= 0x800 before) is wrong for tails of big tables
  (it put the save messages r0D3B84.. under 0x0808F758 too: those are retail, NOT waived).
- **ROM strings left (~1,100 after waivers), by kind and how to force them:**
  - field system box messages (joins "Battler X joined", keys, Yes/No, Save/Don't save: r0D00C8..r0D0FF0,
    r0D100C..): event code calls **0x0807C970(r0 = string, r1 = 2, r2 = -1)**. New `tools/lua/forceview.lua`
    (generic msgview: hook FV_ADDR, replace FV_REG by the next value of FV_VALS, LOOP reload) can force them; first
    find a scene that calls 0x0807C970 (run forceview without FV_VALS: it logs `FVCALL` per call).
  - battle messages (Ambushed!/First strike!/Run/escape/steal: r0D1Fxx, r0D2018.., 0x08C1E8 pool),
    credits (r0D2xxx ptrs @0x0D2xxx + series names @0x103xxx: ending_credits needs a longer hold), save/erase/load
    boxes r0D3B80..r0D3F38 (retail, need forcing or scenes).
  - data-table names (ptrs in 0x7B3000..0x7E4000): characters/enemies 0DB000 (~290), skills/items 0DC000/0DD000
    (~520), traits/effects 0DE000 (~94), item descriptions 0DD @7DC: need list viewers (fill inventory / skill
    lists by RAM poke, scroll) or a forced name lookup per kind.
  - archives B/D/E/P: all go through 0x0800FE88(id, archive, 1, dest): forceview on 0x0800FE88 with FV_REG r0 in
    a scene that shows that archive (m1_book for B, an item menu for D, status equipment for E, save slots / Japan
    map for P), filtering by r1 = archive base (add an FV_IF register filter to forceview.lua).
- **Next, in order:** (1) gate: `tour_sheets.py --en work/qa/tour_en3`, `qa_gate.py init ... --build`, `todo`,
  `JOBS=1 sh tools/vqa.sh`, fix, `check`. (2) msgview resume. (3) forceview for 0x0800FE88 archives and 0x0807C970
  box messages. (4) list viewers for names. Run ONE emulator job at a time (memory).

## Phase 8 session 13 (2026-11-16): vqa chunks 012-029, sign + credits fixes
- **vqa:** chunks 012-029 judged (codex read-only, `JOBS=2 sh tools/vqa.sh`): 347 ok, 3 new issues, all closed in
  work/qa/verdicts/recheck_003.tsv: map_135 plate MUMMY -> **MAMII** / DRUGS (glossary; all 4 sign entries), o_ending
  credit captions r0D2FE0 respaced to sit centred under the portraits (half-width space = 3 px), o_battle short
  names = D8 (now a standing non-bug in docs/visual-qa-brief.md). Seen in cold-boot warps work/qa/fix13.
- **Build 994585e0** (check ok). Re-tour started: `warp_all.py build/goushouden_en.gba --out work/qa/tour_en3
  --jobs 1 --script $SKILL/scripts/lua/probes/textcover.lua --var "RANGES='$(python tools/cover_ranges.py)'"`
  (one pass = gate shots + textcover logs). Don't rebuild while it runs: every scene loads build/goushouden_en.gba.
  **Killed by Claude Code's low-memory reaper** at 119/~356 scenes (map_063), together with a parallel
  `msgview.py --chunks 16 --jobs 1` (c00, c01 done 336/336 each, c02 partial). Cause: another project's 5 Mesen
  instances (onmyou-taisenki, ~3 GB) on the same machine. Rerun both only when that machine is free, ONE at a time
  (the tour first; warp_all has no resume, so rerun it whole into a fresh tour_en3; msgview `--only` can redo c02+).
- **Next:** `tour_sheets.py --en work/qa/tour_en3`, `qa_gate.py init work/qa/manifest.tsv work/qa/tour --glob
  "*.png" --build build/goushouden_en.gba`, `qa_gate.py todo ... --out-dir work/qa/chunks` (only changed sheets),
  vqa, `qa_gate.py check`. Then msgview (`--jobs 1`) + textcover on work/qa/tour_en3 + work/qa/msgview.

## Phase 8 session 12 (2026-11-16): gate tour, Yes/No boxes, forced message viewer
**Memory is the bottleneck:** each Mesen takes ~1 GB, another project's emulator shares the machine, and Claude Code
kills idle background shells when memory runs low (it killed both long runs this session). Run ONE long job at a
time (`--jobs 1`, `JOBS=1`), nothing else alongside.
- **Tour:** tour_en complete on build 0ee58113 (353 scenes + 3 new `*_yn`), tour_jp complete (sign scenes and `*_yn`
  rerun). `tour_sheets.py` -> work/qa/tour (356 sheets); `qa_gate.py init work/qa/manifest.tsv work/qa/tour --glob
  "*.png" --build build/goushouden_en.gba` (recorded build 0ee58113, the OLD build); chunks in work/qa/chunks (30 x
  12). `vqa.sh` judged chunk_000-005 (work/qa/verdicts), then was killed (memory). Issues so far: B00.00 one-word
  last line (fixed, recheck_002), name-entry kana grid (standing non-bug, D9, added to visual-qa-brief; recheck_001).
- **Fixed, seen in cold-boot shots:** the save overwrite box r0D3C98 ran past its 64-px box ("Old data will be",
  "No" clipped): now "Old data will / be erased. / Overwrite it?". All eight Yes/No boxes (r0D3BA0..r0D3EB0) placed
  Yes/No far from where the game draws its fixed cursor; now Yes / No start at the original はい / いいえ columns
  (x = 8*col, space = 3 px). Seen: m1_save_yn (inkbox margins = the original's, 2/2), m1_name_yn (matches the
  original). Not reached yet: load box r0D3C60 (needs save data), erase boxes, 取消してよろしいですか (m1_name_yn2
  doesn't reach it). New build 73ed6249: check ok, smoke ok.
- **Text coverage infrastructure (new):** build.py writes `build/goushouden_en.strings.tsv` (8,055 ids: archive
  messages -> their u16 id-map entry, read on every lookup by 0x08017E18 / 0x0800FE88; ROM strings -> where the build
  put them). `tools/cover_ranges.py` -> the RANGES for `$SKILL/scripts/lua/probes/textcover.lua` (verified: a
  map_290 warp logs dialogue 34.10 and the debug-menu strings). `tools/lua/msgview.lua` + `tools/msgview.py`: forced
  message viewer: map_290's entry event (4 messages) with the id swapped at 0x08017E18, a state reloaded whenever the
  event runs dry, mash.lua advancing; ~200 frames / ~1.4 s per message (12/12 test ok). The full run (5,363 ids, 16
  chunks) was killed by memory; per-chunk timeout is now 300 + 3 s per id.
- **Next, in order:** (1) re-tour on the current build (one job: `warp_all.py --out work/qa/tour_en --jobs 1`), then
  `tour_sheets.py`, `qa_gate.py init ... --build build/goushouden_en.gba` (keeps verdicts of unchanged sheets),
  `qa_gate.py todo`, `JOBS=1 sh tools/vqa.sh`, fix, `qa_gate.py check`. (2) `msgview.py --chunks 16 --jobs 1`, plus a
  warp_all run with `--script $SKILL/scripts/lua/probes/textcover.lua --var "RANGES='$(python tools/cover_ranges.py)'"
  --out work/qa/cover`, then `textcover.py work/qa work/qa/... build/goushouden_en.strings.tsv`: ROM strings (items,
  skills, enemies, names) need forcing too or waivers with reasons (docs/text_unshown.tsv). (3) Remaining Yes/No
  boxes above; RESUME / SHOP / SYM / CRITICAL!! / MISS labels still unseen.

## Phase 8 session 11 (2026-11-16): field teleport, S7 signs closed
- **Teleport:** warp.lua step `at=X:Y` (player pixels at map load; camera = X-120, Y-88; docs/re/debug.md §Field
  teleport). The game redraws the visible area screen-relative, so a ppudump of a teleported warp (camera a multiple
  of 8) is the real screen: gfxlabel SCREENS can point at such a scene. `tools/debug/mapshot.py N..` stitches whole
  maps (work/qa/maps/map_NNN.png + .txt with the at= per screen); warp.lua logs `FIELD map WxH cells camera X,Y`.
- **S7 done:** every map that loads an S7 tile set rendered whole (44 maps). Only signs: the pharmacy plate
  間身井薬局 on 135/147 (661050, sign135 already covers 147: same tiles; scene sign147 is its check), 245 (73E49C:
  new sign245), 244, 309/310. All seen MUMMY / DRUGS in cold-boot EN warps (sign245, sign147, map_135). The other
  tile sets place no sign anywhere (triaged in graphics_nodiff.tsv with the reason), 66D610 / 674910 / 3086C8 /
  426368 never load, 301D08 = world-map building icons. `gfxleft.py`: 0 left.
- warp_all: title_menu2 needs 3000 frames (MIN_FRAMES). Under load some original-ROM runs fail at start (exit 2,
  no run dir): rerun those with `--only`.
- **Tour state at session end:** the EN tour rerun on this build (`warp_all.py build/goushouden_en.gba --out
  work/qa/tour_en --jobs 3`) was killed by Claude Code at 53/~353 scenes: the machine ran low on memory. Rerun it
  (fewer jobs, nothing else running), then the original's sign scenes (`--only "^sign"` into work/qa/tour_jp;
  the rest of tour_jp is complete, 352 shots).
- **Next, in order:** (1) gate tour: tour_en + tour_jp -> `tools/tour_sheets.py` -> `qa_gate.py init work/qa/manifest.tsv
  work/qa/tour --glob "*.png" --build build/goushouden_en.gba` -> `qa_gate.py todo ... --size 12 --out-dir
  work/qa/chunks` -> `JOBS=3 sh tools/vqa.sh` -> fix issues -> `qa_gate.py check`. (2) inkbox on choice/centred
  boxes, textcover. (3) Labels drawn but not seen: RESUME (2FE9B8), SHOP (2F91C4), SYM (2F8BB8), CRITICAL!!/MISS
  popups: find a scene for each or record why none exists.

## Phase 8 session 10 (2026-11-16): pharmacy plate fix, map-camera recon (partial)
- **Fixed:** sign244's copy step had written MUMMY/DRUGS pieces into 7A0DD0, whose plate is a different 5-kanji
  sign (間身井薬局, same shop): maps 309/310 showed garbage. `SCREENS[...]["copy"]=False` now skips gfxlabel's
  copy step (set on every sign entry: map signs share glyph tiles across tile sets); new `sign309` (rect 100,16
  / 100,22) = MUMMY / DRUGS. Seen in a cold-boot warp on EN: maps 135, 244, 309, 310 all read MUMMY / DRUGS.
  73E49C (map 245) lost the stray copy and is back in gfxleft (its signs are other shops, not seen yet).
- **Finding signs, what was tried:** map_245 is 90x60 cells (720x480 px, 3x3 screens); BG screenblocks are 32x32
  ring buffers (only ~the screen is in VRAM). Walk tours work (`press=down*120` steps in a scene file passed with
  `--var "SCENES=[[C:/abs/file]]"`, `--shot-every 40`), but the spawn sits in a corner and walls/NPCs block
  straight walks: slow. A teleport would be better, not found yet:
  - map state struct 0x03004F10: +0x220/+0x222 = map w/h in 8-px cells, +0x2A0.. = ring-buffer fine scroll
    bytes (BG regs written at 0x0801989A from 0x03004F10+0x2A1..); streamer 0x0801A5F8(x, y, cellx, celly)
    divides by chunk size (+8 / +0xC) and gets a chunk via 0x0801BA04, map words = tile | flips<<14, palette per
    tile via 0x0801B7B0. A full-map render could reuse this (call it from Lua for every cell, or port it).
  - the player/camera world position: not found by ramsearch (dumps in work/qa/walk/d245, `ram_*.bin`).
- **Next, in order:** (1) a teleport or full-map render (above), then the S7 tile sets (list in session 8 Left,
  plus 66D610 / 674910 now in gfxleft); 73E49C's top tile row holds kanji sign halves (雑貨店舗-like). (2)
  3086C8 / 301D08 / 426368. (3) Gate tour (session 8 Next (3)).

## Phase 8 session 9 (2026-11-16): S7 map signs, pilot
- **Done, seen in a cold-boot warp on the EN build:** the マミー薬局 plate = MUMMY / DRUGS (two lines, `small`, no
  outline, ink 1 on plate e) on map_244 (tile set 73C13C) and map_135 (661050): gfxlabel SCREENS `sign244` /
  `sign135`, kind bg2. gfxlabel's copy step also wrote the plate into 73E49C and 7A0DD0 (maps 245, 309/310):
  **not seen there yet**. In 661050 the copy reached only the tiles that occur once, hence the separate sign135.
- **Method that works:** map BGs come out unscrolled in the ppudump but at a warp spawn the scroll is 0 in the
  small maps tried, so the screen rect = map rect: `gfxlabel.py grid map_NNN x,y,w,h bg2` shows the plate and which
  tile rows are shared (`*`): the plate's top tile row is one repeated tile, keep text off it. A sign off screen at
  spawn needs a scene that walks there (`map=N,press=right*60` style steps in tools/debug/scenes.txt) and a check
  that scroll is still 0 in the dump (or teach gfxscreen the scroll from the game's RAM copy).
- **Dead end:** the 800-byte blocks after a tile set (73DB20..73E134 for 73C13C, type 1, to EWRAM 0x020147D0+) are
  the map layers but not a plain 20x20 / 40x20 tilemap: rendering them gave no coherent picture. Not needed.
- **Which spawn shows a sign** (original warp shots work/qa/warp_all*/shots): 244 and 135 (both the pharmacy);
  002-030, 109, 115-126, 129-134, 136-139, 147, 245, 309, 310 show none at spawn: walk to find them.
- **Next, in order:** (1) check map_245 / 309 / 310 on EN (the copied plate). (2) The other S7 tile sets: walk each
  town map (start with 科学都市 129-139, 蓮沼街 245, ハレンチ学園 147) to find its signs, then SCREENS entries as above.
  (3) 3086C8 / 301D08 / 426368. (4) Gate tour (see session 8 Next (3)).

## Phase 8 session 8 (2026-11-16): title menu, spoils page 2, shop banner, sweep triage
- **Where the leftovers load:** `warp_all.py` now passes `--var` to probes; `--script tools/lua/unpackat.lua --var
  "SRCS='0x08..,..'"` over every scene (work/qa/unpackat) and every map (work/qa/unpackat_maps) on the original.
- **Done, seen in a cold-boot warp on the EN build:** title menu pills 2FD740 / 2FD884 / 2FD9BC = NEW GAME / CONTINUE
  / PROFILES (scenes `title_menu`; `title_menu2` = debug save, soft reset, Retail: the menu with save data);
  2FE9B8 コンティニュー = RESUME (same style, shows only with suspend data: **not seen**). Spoils page 2 (2F7B2C,
  scene `m1_crop2`): 入手したお金 / 入手したアイテム = PRIZE GOLD / PRIZE ITEMS (入手した's tiles are shared by
  both banners, お金 owns 24 px: GOLD; Bangers 13 = class `big`; the banner tab under the old text rebuilt by
  `fillat`).
- **Drawn by block, not seen:** shop banner 万屋 (2F91C4, loads with every shop at 0x060045E0 but no shop scene shows
  it) = SHOP; name entry 記号 tab (2F8BB8, loads with name entry, R only cycles 3 tabs) = SYM.
- `gfxlabel.STRIPS` runs take `dict(rows=2)` (a 2-row pill, text centred, cleared pixels take the row's commonest
  kept index; `x=` fixes the left edge) and `outline=None`. 1-row strips (battle2) unchanged.
- graphics_nodiff.tsv: 2F74E4 / 2F7578 (party panel frame tiles), 7 malformed rows inside done blocks, 2F3E74
  (digit font), 4F23B0 (title OBJ art: eclipse arcs).
- **Left (gfxleft: 21 rows):**
  - **S7 map signs:** tileset blocks at BG 0x06008000: 553FE8 (map_002-004), 56B4C0 (map_011-016), 5767BC
    (017-020), 59184C (026-030), 5C11B8 (045), 632C74 (109), 637A28 (115-126+), 661050 (129 135 139 147), 66A918
    (131 136), 6702B4 (133), 673C2C (134), 67A910 (046 137 138), 73C13C (244), 73E49C (245), 7A0DD0 (309 310).
    Method: `ppuscene.py map_NNN` dumps on the original, `tiles.py map` the BG screenblocks (walk the player if
    the sign is off screen) to see each sign whole, then a SCREENS entry per sign (kind bgN) or STRIPS/TILES
    straight into the tileset; `vramfind --others`: a sign tile shared with other map art must not change.
  - 3086C8: a 64x64 ロボ専 sign (black on white, 8x8 tiles); no scene or map loaded it: find its loader.
  - 301D08: loads at map_000 into EWRAM 0x0201B5E0 (a buffer, not VRAM): tiny building sprites, maybe no text.
  - 426368: thin katakana SFX (ガ…) over a bar, 39 tiles; never loaded by any scene or map warp (battle effect?).
- **Next, in order:** (1) S7 signs as above. (2) 3086C8 / 301D08 / 426368. (3) Gate tour: warp_all EN ->
  work/qa/tour_en, original -> tour_jp, `tour_sheets.py`, `qa_gate.py init/todo --size 12`, `JOBS=3 sh
  tools/vqa.sh` (codex is installed: codex-cli 0.167.1), then inkbox on choice boxes, textcover.

## Phase 8 session 7 (2026-11-16): battle popups, shop GEAR tab, sweep triage
- **Boss cut-in (session 5 (a)) is done:** with `tools/lua/mash.lua` (press A every N frames) on k_ode the boss
  super-move at ~f1700 loads 4 S5 glyph blocks (JP 389370 388CE8 388C68 3889E8 = ドガーン; EN 38966C 389034 389998
  388F10) and reads BLAM in the EN build: it is the SFX font, covered by session 6.
- **Battle popups drawn by block** (gfxlabel TILES runs now take {font small|tiny, ay, fill}): 2F5C04 is a sheet of
  digits 0-9, /, クリティカル!! (tiles 11-17), ミス (28-29), %UP (30-32); 362154 / 3621F4 hold the same tiles for
  the battle-effect loader. CRITICAL!! (6-px caps) and MISS (3x5) in the kana's ink 7/8/9/a + shadow 1. Verified
  only by unpacking the built ROM (`packed.unpack`): **not seen in game yet**: no warp shows a critical or a miss
  (a mashed k_ode and the game_over wipe never load 362154/3621F4; 2F5C04 loads as BG tiles in the shop, unused
  there). To see them: find what picks the popup (the loader 0x08011BEF's caller) and force it.
- **3625A8 = "GAME OVER" Latin art** (unpacked at the wipe, `tools/lua/unpackat.lua` logs a block's unpack frame /
  dst / lr, or every unpack from FROM): no work.
- **Shop accessory tab** (new scene `m2_shop_gear`): the other tab states (2FA8D4 green アイテム, 2FAB64 pink
  アクセサリー) were still Japanese; SCREENS["gear"] -> ITEMS / GEAR, seen in a cold-boot warp with both states.
- Triage into graphics_nodiff.tsv: malformed rows inside done blocks (2F6A44 2F6A64 2F6C00 2FAAB4 2FAAB8 2F89F0),
  Latin art (2F5FC8 HP/EXP/NEXT, 2F55A4 LV, 2F58B4 %). `gfxleft.py`: 39 left.
- **Next, in order:** (1) 2F91C4 (shop, BG at 060045E0: kanji plate fragments, maybe 小計/下限: find where it
  shows), 2F74E4 / 2F7578 (k_jump/party captions), 2F7B2C spoils banner, 2F8BB8 / 2F8C8C / 2F96C0 / 2F98CC /
  2FA1F0 framed labels (t3), 2FA408 / 2FA7F8 / 2FA8B0 headings, 2FD740-2FE9B8: per block `unpackat.lua --var
  "SRCS='0x08XXXXXX'"` over likely scenes to find where it loads, then a SCREENS entry. (2) Force a critical/miss
  to see the popups. (3) S7 shop signs (map tiles), S3 301D08 / 3086C8, S6 426368 4F23B0. (4) Gate tour + vqa.sh,
  inkbox, textcover.

## Phase 8 session 6 (2026-11-16): SFX cut-ins (S5)
- **S5 is the battle SFX font**, not title cards: 40 packed blocks 0x3873C8-0x389998, one 32x32 OBJ kana each, in
  the order of the kana lookup 0x0D9C58 (index i at 0x0D9CF4 - 4i, via table 0x08104D1C; 0x080C6258 matches each
  2-byte char of an SFX record name and stores the index). `tools/gfx_sfx.py draw` redraws 27 of them as A-Z ! in
  the game's style (Bangers, OFL; gradient b..3, outline 2, lower-left c-f, shadow 1); each letter went to a block
  whose packed slot fits it (`MAP`; the small-kana blocks are too small). The build writes the lookup codes
  (fullwidth), `extract.FULLWIDTH` covers the SFX name fields, English in `script/sfx_en.tsv` (`gfx_sfx.py names`
  -> sfx.json; check.py's test runs `gfx_sfx.check`).
- **The cut-in draws 4 glyph sprites only** (OAM log `tools/lua/oamlog.lua`: 6-letter FWOOM! showed FWOO; it loads
  a glyph per char but draws 4, 32 px apart, scrolling left from x 233): English SFX names are <= 4 letters. The JP
  names longer than 4 kana are cut the same way. Seen in a cold boot: c_effect (4,3) + A -> FOOM in full.
- Scene for it: `4,3,wait=60,press=a,wait=600` (effect 0 = ドワッ, letters at f414-480). Not added to scenes.txt.
- **Still open from session 5:** the boss super-move cut-in ドドドゲーン (k_ode mashed ~f1700) is NOT this font
  (ゲ isn't in the lookup): big lettering from the battle-effect loader 0x08011BEF, still Japanese.
- **Next, in order:** (1) that boss cut-in + クリティカル!! / UP / 3625A8 (session 5 (a)/(b)). (2) leftover menu
  blocks (`gfxleft.py`: 53 left; list from session 5 (2)). (3) S7 shop signs, S3, S6. (4) Gate tour + vqa.sh, inkbox,
  textcover.

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
