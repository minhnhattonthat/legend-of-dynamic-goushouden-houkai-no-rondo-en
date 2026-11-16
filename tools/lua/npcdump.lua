-- Log the field NPC table (pointer at 0x030052EC, 0x60-byte records; talk reads the message id at +0x10 + 2*n and
-- cycles the counter +0x49 mod 3, 0x08023DBC..) and the player position (0x03005230 +0x58 X, +0x56 Y), at frame AT.
--   emu.py ROM --script tools/debug/warp.lua --var "SCENE='map_135'" --script tools/lua/npcdump.lua --var AT=600
local at, n = AT or 600, N or 12
local M = emu.memType.gbaMemory
L.on_frame(function(f)
  if f ~= at then return end
  local base = emu.read32(0x030052EC, M)
  L.log(string.format("PLAYER x=%d y=%d  NPCBASE %08X", emu.read16(0x03005288, M), emu.read16(0x03005286, M), base))
  for i = 0, n - 1 do
    local r, words = base + i * 0x60, {}
    for o = 0, 0x5E, 2 do words[#words + 1] = string.format("%04X", emu.read16(r + o, M)) end
    L.log(string.format("NPC %d %s", i, table.concat(words, " ")))
  end
end)
