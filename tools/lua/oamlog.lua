-- Log the visible OBJs whose tile number is in [TLO, THI) every EVERY frames from FROM to TO:
-- frame, then "x,y,tile" per OBJ (x, y as the hardware sees them: 9-bit x, 8-bit y).
--   emu.py ... --script tools/lua/oamlog.lua --var TLO=0xFE --var THI=0x15E --var FROM=400 --var TO=520
local tlo, thi = TLO or 0, THI or 1024
local from, to, every = FROM or 0, TO or 1e9, EVERY or 2
L.on_frame(function()
  local f = L.frame
  if f < from or f > to or (f - from) % every ~= 0 then return end
  local out = {}
  for i = 0, 127 do
    local a0 = emu.read16(0x07000000 + i * 8, emu.memType.gbaMemory)
    local a1 = emu.read16(0x07000000 + i * 8 + 2, emu.memType.gbaMemory)
    local a2 = emu.read16(0x07000000 + i * 8 + 4, emu.memType.gbaMemory)
    local tile = a2 & 0x3FF
    local hidden = (a0 & 0x300) == 0x200
    if not hidden and tile >= tlo and tile < thi then
      out[#out + 1] = string.format("%d,%d,%X", a1 & 0x1FF, a0 & 0xFF, tile)
    end
  end
  L.log(string.format("f%d %s", f, table.concat(out, " ")))
end)
