-- Where do the glyph writers draw? At the half-width writer 0x0800C3A4 and the 12-px writer 0x0800C218 (both
-- called by the menu printer 0x0800E3D0 with the window in r0), log the window and the fields the half-width
-- writer builds its destination from: [w+0x84] buffer, [w+0x8C] u16 tile base, [w+0xA0], [w+0xAC], [w+0xB0].
--   emu.py ROM --out DIR --script tools/debug/warp.lua --script tools/lua/glyphdest.lua --var "SCENE='m1_book'"
local maxn = MAXN or 200
local from = FROM or 0
local n = 0
local function rd32(a) return emu.read32(a, emu.memType.gbaMemory, false) end
local function rd16(a) return emu.read16(a, emu.memType.gbaMemory, false) end
for name, at in pairs({ half = 0x0800C3A4, full = 0x0800C218, outl = 0x0800C6B0 }) do
  L.on_exec(at, at, function()
    if n >= maxn or L.frame < from then return end
    n = n + 1
    local s = emu.getState()
    local w = s["cpu.r0"]
    L.log(string.format("f%d %s w=%08X ch=%02X%02X buf=%08X base=%X A0=%d AC=%d B0=%d 88=%08X 90=%d 94=%d 98=%d 9C=%d",
      L.frame, name, w, s["cpu.r1"] & 0xFF, s["cpu.r2"] & 0xFF, rd32(w + 0x84), rd16(w + 0x8C), rd32(w + 0xA0),
      rd32(w + 0xAC), rd32(w + 0xB0), rd32(w + 0x88), rd32(w + 0x90), rd32(w + 0x94), rd32(w + 0x98), rd32(w + 0x9C)))
  end)
end
