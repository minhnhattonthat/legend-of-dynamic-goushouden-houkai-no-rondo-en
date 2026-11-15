-- Boot into the leftover debug menu (デバックＭＥＮＵ, 0x0807E370) instead of the retail loop.
-- main() at 0x0807E454 ends with `bl 0x0807E2F4` (retail title loop) at 0x0807E48A; the debug menu's first
-- entry (製品版) calls that same loop, so redirecting the BL keeps the game fully playable.
--   emu.py ROM --out DIR --script tools/debug/dbgmenu.lua [--route r.txt]
local BL_AT = 0x7E48A                  -- ROM offset of the BL
local ORIG = { 0xFF, 0xF7, 0x33, 0xFF }  -- bl 0x0807E2F4
local NEW  = { 0xFF, 0xF7, 0x71, 0xFF }  -- bl 0x0807E370

local function rom_write(off, bytes)
  for i, b in ipairs(bytes) do emu.write(off + i - 1, b, emu.memType.gbaPrgRom) end
end
local function rom_read(off, n)
  local t = {}
  for i = 0, n - 1 do t[#t + 1] = emu.read(off + i, emu.memType.gbaPrgRom) end
  return t
end

local cur = rom_read(BL_AT, 4)
for i = 1, 4 do
  if cur[i] ~= ORIG[i] and cur[i] ~= NEW[i] then
    L.fail(string.format("dbgmenu: unexpected bytes at %06X (build moved main?)", BL_AT))
  end
end
rom_write(BL_AT, NEW)
local chk = rom_read(BL_AT, 4)
assert(chk[3] == NEW[3], "dbgmenu: ROM write did not stick")
L.log("dbgmenu: BL redirected to 0x0807E370")
