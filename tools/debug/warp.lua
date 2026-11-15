-- Cold-boot warp to any scene in tools/debug/scenes.txt, through the game's own leftover debug menus.
--   emu.py ROM --out DIR --script tools/debug/warp.lua --var "SCENE='field_019'" --frames 900 --sheet
--   optional: --var "STATE_OUT=[[C:/abs/work/states/x.mss]]"  save a state once the warp is done (+HOLD frames)
--             --var HOLD=240  frames after the last step before the warp_<scene>.png shot and STATE_OUT
-- Scenes: tools/debug/scenes.txt, plus map_NNN for any field-test map (tools/debug/maps.tsv). All of them, in
-- parallel, one shot each: python -X utf8 tools/debug/warp_all.py [--states]
--             --var "SCENES=[[C:/abs/scenes.txt]]"  another scene list (default ../debug/scenes.txt: Mesen runs
--             with tools/mesen as its working folder)
--
-- How it works (docs/re/debug.md): main() at 0x0807E454 ends with `bl 0x0807E2F4` (retail title loop) at ROM
-- 0x7E48A; the BL is redirected to the debug menu 0x0807E370 (entry 0 of that menu is the retail loop itself).
-- Each step of a scene is consumed at a hook point, by overwriting a register:
--   N        the next return of a list menu (0x08007570 -> bx at 0x080077AA, or 0x08007978 -> bx at 0x08007BCC):
--            r0 = N (the chosen row, 0-based)
--   map=N    the field test (0x080167A0) when A is pressed: r9 (the map index) = N at 0x08016AEC
--   wait=F   idle F frames
--   press=B  press button(s) B (a+up...) for 6 frames (B*N: N frames), then idle 40
--   hold=F   this scene's shot (and STATE_OUT) F frames after the last step instead of HOLD
--   wipe     in a field with random encounters: party HP 1, walk left/right until a battle, pin the enemies' HP,
--            mash A; done when the trio's battle HP are all 0 (the game over follows; docs/re/debug.md)
-- While a menu or map step is pending, the script presses A every 24 frames to make the menu return.

local DEBUG_MENU_BL, BL_ORIG, BL_NEW = 0x7E48A, { 0xFF, 0xF7, 0x33, 0xFF }, { 0xFF, 0xF7, 0x71, 0xFF }
local MENU_A_IN, MENU_A_RET = 0x08007570, 0x080077AA
local MENU_B_IN, MENU_B_RET = 0x08007978, 0x08007BCC
local FIELDTEST_IN, FIELDTEST_PICK = 0x080167A0, 0x08016AEC

local scene = assert(SCENE, "warp.lua: pass --var \"SCENE='name'\"")
local hold = HOLD or 240

-- scene list: name <TAB/spaces> steps (comma separated) [# note]
local function load_scenes(path)
  local t = {}
  for line in io.lines(path) do
    local l = line:gsub("#.*", ""):match("^%s*(.-)%s*$")
    if l ~= "" then
      local name, steps = l:match("^(%S+)%s+(%S+)$")
      if not name then error("scenes.txt: bad line: " .. line) end
      t[name] = steps
    end
  end
  return t
end
local scenes = load_scenes(SCENES or "../debug/scenes.txt")
-- map_NNN (tools/debug/maps.tsv) needs no line of its own: field test, map NNN
local mapn = scene:match("^map_(%d+)$")
local spec = scenes[scene] or (mapn and ("2,0,map=" .. tonumber(mapn))) or error("warp.lua: unknown scene " .. scene)

local steps = {}
for tok in spec:gmatch("[^,]+") do
  local k, v = tok:match("^(%a+)=(.+)$")
  if tok == "wipe" then steps[#steps + 1] = { kind = "wipe" }
  elseif not k then steps[#steps + 1] = { kind = "menu", n = tonumber(tok) or error("bad step " .. tok) }
  elseif k == "map" then steps[#steps + 1] = { kind = "map", n = tonumber(v) }
  elseif k == "wait" then steps[#steps + 1] = { kind = "wait", n = tonumber(v) }
  elseif k == "press" then steps[#steps + 1] = { kind = "press", b = v }
  elseif k == "hold" then hold = tonumber(v)
  else error("bad step " .. tok) end
end
L.log(string.format("WARP %s: %s (%d steps)", scene, spec, #steps))

-- redirect main()'s BL into the debug menu (the ROM in memory only; the file is not touched)
for i, b in ipairs(BL_ORIG) do
  local cur = emu.read(DEBUG_MENU_BL + i - 1, emu.memType.gbaPrgRom)
  if cur ~= b and cur ~= BL_NEW[i] then L.fail(string.format("warp.lua: unexpected byte at %06X: main() moved?", DEBUG_MENU_BL)) end
end
for i, b in ipairs(BL_NEW) do emu.write(DEBUG_MENU_BL + i - 1, b, emu.memType.gbaPrgRom) end

local cur = 1            -- index of the pending step
local waiting = nil      -- "menu" / "map" while a hook point is expected
local idle_until = 0
local done_at = nil

local function step() return steps[cur] end
local function finish_step(what)
  L.log(string.format("f%d step %d %s", L.frame, cur, what))
  cur = cur + 1
  if cur > #steps then done_at = L.frame; L.log(string.format("WARP_DONE f%d", L.frame)) end
end

local function set_reg(name, v) emu.setState({ ["cpu." .. name] = v }) end
local function on_menu_ret()
  local s = step()
  if s and s.kind == "menu" then
    local r0 = emu.getState()["cpu.r0"]
    set_reg("r0", s.n)
    finish_step(string.format("menu r0 %d -> %d", r0, s.n))
  end
end
L.on_exec(MENU_A_RET, MENU_A_RET, on_menu_ret)
L.on_exec(MENU_B_RET, MENU_B_RET, on_menu_ret)
L.on_exec(FIELDTEST_PICK, FIELDTEST_PICK, function()
  local s = step()
  if s and s.kind == "map" then
    local r9 = emu.getState()["cpu.r9"]
    set_reg("r9", s.n)
    finish_step(string.format("map %d -> %d", r9, s.n))
  end
end)

-- wipe: party records 0x02007264 (0x44 apart, HP u16 at +0, DP at +6); battlers are a heap block (0x020093B0 or
-- 0x02009390 seen) of 6 records 0x17C apart (HP u16 at +0, DP at +6, 1 at +0xA, 16 zero bytes before; slots 0-2
-- the trio, 3-5 enemies). The block is found by the trio's DP values; nothing is written there outside a battle.
local M = emu.memType.gbaMemory
local PARTY, BSTRIDE = 0x02007264, 0x17C
local battler = nil
local function battler_live(base, i)
  local a = base + i * BSTRIDE
  if emu.read16(a + 0xA, M) ~= 1 then return false end
  for o = -0x10, -2, 2 do if emu.read16(a + o, M) ~= 0 then return false end end
  return true
end
local function find_battlers()
  local dp0, dp1 = emu.read16(PARTY + 6, M), emu.read16(PARTY + 0x44 + 6, M)
  for a = 0x02008000, 0x0200C000, 4 do
    if emu.read16(a + 6, M) == dp0 and emu.read16(a + BSTRIDE + 6, M) == dp1 and battler_live(a, 0)
       and battler_live(a, 3) then return a end
  end
end
local function wipe_frame(s, f)
  if s.battle and not (battler_live(battler, 0) and battler_live(battler, 3)) then return end  -- over: time out
  if not s.battle then
    for i = 0, 2 do emu.write16(PARTY + i * 0x44, 1, M) end
    if f % 10 == 0 then battler = find_battlers() end
    if not battler then
      if f >= idle_until then L.press("left", 50); L.press("right", 50); idle_until = f + 100 end
      return
    end
    s.battle = true; s.pin = {}
    L.log(string.format("f%d wipe: battle, battlers at %08X", f, battler))
  end
  local BATTLER = battler
  for i = 3, 5 do
    local a = BATTLER + i * BSTRIDE
    local v = emu.read16(a, M)
    if not s.pin[i] and v > 0 then s.pin[i] = v end
    if s.pin[i] and v < s.pin[i] then emu.write16(a, s.pin[i], M) end
  end
  local dead = 0
  for i = 0, 2 do if emu.read16(BATTLER + i * BSTRIDE, M) == 0 then dead = dead + 1 end end
  if dead == 3 then finish_step("wipe: party down")
  elseif f % 24 == 0 then L.press("a", 4) end
end

L.on_frame(function(f)
  if done_at then
    if f == done_at + hold then
      L.shot("warp_" .. scene .. ".png")
      if STATE_OUT then L.save_state(STATE_OUT, function() L.log("STATE " .. STATE_OUT) end) end
    end
    return
  end
  local s = step()
  if s and s.kind == "wipe" then wipe_frame(s, f); return end
  if not s or f < idle_until then return end
  if (s.kind == "wait" or s.kind == "press") and s.started then
    finish_step(s.kind .. " " .. (s.b or s.n))   -- its idle time is over
  elseif s.kind == "wait" then s.started = true; idle_until = f + s.n
  elseif s.kind == "press" then
    local b, n = s.b:match("^(.-)%*(%d+)$")
    b, n = b or s.b, tonumber(n) or 6
    s.started = true
    L.press(b, n); L.press("-", 40); idle_until = f + n + 40
  elseif f % 24 == 0 then L.press("a", 4) end  -- menu / map: nudge the menu until its hook fires
end)
