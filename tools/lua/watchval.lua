-- Log writes into WATCH_LO..WATCH_HI with a nonzero value: frame, pc, addr, value, plus r0-r3 once per PC.
--   emu.py ... --script tools/lua/watchval.lua --var WATCH_LO=0x0201D9F0 --var WATCH_HI=0x0201DA10 [--var MAXN=200]
local lo, hi, maxn = WATCH_LO, WATCH_HI or WATCH_LO, MAXN or 200
local n = 0
local seen = {}
L.on_write(lo, hi, function(addr, value)
  if n >= maxn or value == 0 then return end
  local pc = L.pc()
  local s = emu.getState()
  local regs = ""
  if not seen[pc] then
    seen[pc] = true
    regs = string.format(" r0=%08X r1=%08X r2=%08X r3=%08X r4=%08X r5=%08X lr=%08X",
      s["cpu.r0"] or 0, s["cpu.r1"] or 0, s["cpu.r2"] or 0, s["cpu.r3"] or 0, s["cpu.r4"] or 0, s["cpu.r5"] or 0, s["cpu.r14"] or 0)
  end
  n = n + 1
  L.log(string.format("f%d pc=%08X addr=%08X val=%X%s", L.frame, pc, addr, value, regs))
end)
