-- Menu printer (0x0800E3D0, engine.PRINTERS p2): log every call (window r0, args, the string's first bytes, the
-- window's font mode) and every advance / half-width site hit (pen r6, mode). Tells which font a window draws
-- ASCII with and whether ASCII reaches a drawing path at all.
--   emu.py ROM --out DIR --script tools/debug/warp.lua --script tools/lua/p2probe.lua --var "SCENE='m1_book'"
local maxn = MAXN or 200
local from = FROM or 0  -- first frame to log
local n = 0
local function ok(a) return a >= 0x02000000 and a < 0x0A000000 end
local function rd8(a) if not ok(a) then return 0 end return emu.read(a, emu.memType.gbaMemory, false) end
local function rd32(a) if not ok(a) then return 0 end return emu.read32(a, emu.memType.gbaMemory, false) end
local function head(a, k)
  local t = {}
  for i = 0, k - 1 do t[#t + 1] = string.format("%02X", rd8(a + i)) end
  return table.concat(t)
end
L.on_exec(0x0800E3D0, 0x0800E3D0, function()
  if n >= maxn or L.frame < from then return end
  n = n + 1
  local s = emu.getState()
  local w = s["cpu.r0"]
  local mode = rd32(w + 0xE0)
  L.log(string.format("f%d call w=%08X str=%08X r2=%X r3=%08X lr=%08X mode=%d cw=%d %s", L.frame, w,
    s["cpu.r1"], s["cpu.r2"], s["cpu.r3"], s["cpu.r14"], mode, rd32(w + mode * 16 + 4), head(s["cpu.r1"], 12)))
  -- the window's per-font-mode blocks (16 bytes each, modes 0..3) and the words around the mode field
  local b = {}
  for m = 0, 3 do b[#b + 1] = head(w + m * 16, 16) end
  L.log("  modes " .. table.concat(b, " | "))
  for o = 0x40, 0xF0, 0x10 do L.log(string.format("  +%02X %s", o, head(w + o, 16))) end
end)
local SITES = { 0x0800E5DA, 0x0800E5F2, 0x0800E612, 0x0800E72A, 0x0800E73E, 0x0800E762, 0x0800E7CA, 0x0800E7E2,
  0x0800E820, 0x0800E676, 0x0800E68C, 0x0800E6C8 }
for _, site in ipairs(SITES) do
  L.on_exec(site, site, function()
    if n >= maxn or L.frame < from then return end
    n = n + 1
    local s = emu.getState()
    local w = s["cpu.r5"]
    L.log(string.format("f%d site=%08X pen=%d mode=%d w=%08X", L.frame, site, s["cpu.r6"], rd32(w + 0xE0), w))
  end)
end
