-- Log CPU registers at every write into a range (who copies what from where): one line per write.
--   emu.py ... --script tools/lua/regwatch.lua --var WATCH_LO=0x0600F16E [--var WATCH_HI=...] [--var FROM=400]
-- Each line: frame, pc, address, value, r0-r12 (GBA, Mesen state keys cpu.r[N]).
local lo = assert(WATCH_LO, "set --var WATCH_LO=0x...")
local hi, from = WATCH_HI or lo, FROM or 0
local keys
L.on_write(lo, hi, function(addr, value)
  if L.frame < from then return end
  local s = emu.getState()
  if not keys then
    keys = {}
    for k, _ in pairs(s) do if k:match("^cpu%.r") then keys[#keys + 1] = k end end
    table.sort(keys)
  end
  local regs = {}
  for _, k in ipairs(keys) do regs[#regs + 1] = string.format("%s=%X", k:sub(5), s[k]) end
  L.log(string.format("f%d pc=%08X addr=%08X val=%X %s", L.frame, L.pc(), addr, value or 0, table.concat(regs, " ")))
end)
