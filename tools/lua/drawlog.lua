-- Log every glyph draw: the per-glyph draw functions (args: r0 = text window struct, r1/r2 = SJIS bytes, r3 = ?)
-- with the window's cursor/stride fields, so the advance per glyph and the box geometry can be read.
--   emu.py ROM --out DIR --state-in work/states/X.mss --script tools/lua/drawlog.lua [--var MAXN=400]
local maxn = MAXN or 400
local n = 0
local function rd32(a) return emu.read32(a, emu.memType.gbaMemory, false) end
L.on_exec(0x0800AC34, 0x0800AC34, function()
  if n >= maxn then return end
  local s = emu.getState()
  L.log(string.format("f%d lookup ch=%02X%02X lr=%08X", L.frame, s["cpu.r0"] & 0xFF, s["cpu.r1"] & 0xFF, s["cpu.r14"]))
end)
local FUNCS = { 0x0800CB08, 0x0800CCAC }
for _, f in ipairs(FUNCS) do
  L.on_exec(f, f, function()
    if n >= maxn then return end
    n = n + 1
    local s = emu.getState()
    local w = s["cpu.r0"]
    local fields = {}
    for _, o in ipairs({ 0x98, 0x9C, 0xA0, 0xA4, 0xA8, 0xAC, 0xB0, 0xB4, 0xB8, 0x1A4, 0x1B0 }) do
      fields[#fields + 1] = string.format("%X=%X", o, rd32(w + o))
    end
    L.log(string.format("f%d fn=%08X w=%08X ch=%02X%02X r3=%08X lr=%08X %s", L.frame, f, w,
      s["cpu.r1"] & 0xFF, s["cpu.r2"] & 0xFF, s["cpu.r3"], s["cpu.r14"], table.concat(fields, " ")))
  end)
end
