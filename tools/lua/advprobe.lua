-- At the half-width (font mode 3) advance sites of the printer, log the pen, the char bytes on the stack and at r4,
-- and the window's font mode: tells the VWF hook where the drawn pair lives.
--   emu.py ROM --out DIR --script tools/debug/warp.lua --script tools/lua/advprobe.lua --var "SCENE='map_290'"
local maxn = MAXN or 80
local n = 0
local function rd8(a) return emu.read(a, emu.memType.gbaMemory, false) end
local function rd32(a) return emu.read32(a, emu.memType.gbaMemory, false) end
for _, site in ipairs({ 0x0800F288, 0x0800F300, 0x0800F316, 0x0800F352, 0x0800F126 }) do
  L.on_exec(site, site, function()
    if n >= maxn then return end
    n = n + 1
    local s = emu.getState()
    local sp, r4, r6 = s["cpu.r13"], s["cpu.r4"], s["cpu.r6"]
    L.log(string.format("f%d site=%08X pen=%d sp1C=%02X sp1D=%02X r4=%08X [r4]=%02X [r4-1]=%02X mode=%d",
      L.frame, site, s["cpu.r7"], rd8(sp + 0x1C), rd8(sp + 0x1D), r4, rd8(r4), rd8(r4 - 1), rd32(r6 + 0xE0)))
  end)
end
