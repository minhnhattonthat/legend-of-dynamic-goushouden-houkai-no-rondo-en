-- Where does drawn text come from? Log the source pointer of each character the dialogue printer (0x0800E898)
-- reads (r5 at 0x0800E95A) and every glyph lookup's pair + caller, deduplicated by 16-byte source line.
--   emu.py ROM --out DIR --script tools/debug/warp.lua --script tools/lua/srcprobe.lua --var "SCENE='m1_book'"
local seen = {}
local function rd8(a) return emu.read(a, emu.memType.gbaMemory, false) end
-- the menu printer 0x0800E3D0(window r0, string r1): one log line per call
L.on_exec(0x0800E3D0, 0x0800E3D0, function()
  local s = emu.getState()
  local p = s["cpu.r1"]
  if seen[p] then return end
  seen[p] = true
  local b = {}
  for i = 0, 23 do b[#b + 1] = string.format("%02X", rd8(p + i)) end
  L.log(string.format("f%d p2 src=%08X lr=%08X %s", L.frame, p, s["cpu.r14"], table.concat(b, " ")))
end)
-- its wrapper 0x0800E87C(window r0, ?, string r2): log the caller
L.on_exec(0x0800E87C, 0x0800E87C, function()
  local s = emu.getState()
  L.log(string.format("f%d wrap str=%08X r1=%08X lr=%08X", L.frame, s["cpu.r2"], s["cpu.r1"], s["cpu.r14"]))
end)
L.on_exec(0x080ADBD4, 0x080ADBD4, function()
  local s = emu.getState()
  L.log(string.format("f%d adbd4 str=%08X lr=%08X", L.frame, s["cpu.r3"], s["cpu.r14"]))
end)
L.on_exec(0x0800E95A, 0x0800E95A, function()
  local s = emu.getState()
  local p = s["cpu.r5"]
  local key = p & ~0xF
  if seen[key] then return end
  seen[key] = true
  local b = {}
  for i = 0, 15 do b[#b + 1] = string.format("%02X", rd8(p + i)) end
  L.log(string.format("f%d src=%08X lr=%08X %s", L.frame, p, s["cpu.r14"], table.concat(b, " ")))
end)
