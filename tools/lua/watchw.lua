-- Who writes LO..HI? Log PC, LR and r0-r3 for each write from frame FROM (up to MAXN).
--   emu.py ROM --out DIR --script tools/debug/warp.lua --script tools/lua/watchw.lua --var LO=0x02011040 --var HI=0x0201104C
local lo, hi, from, maxn, n = LO, HI or LO, FROM or 0, MAXN or 40, 0
L.on_write(lo, hi, function(addr, value)
  if L.frame < from or n >= maxn then return end
  n = n + 1
  local s = emu.getState()
  L.log(string.format("f%d write %08X=%X pc=%08X lr=%08X r0=%08X r1=%08X r2=%08X r3=%08X r4=%08X r5=%08X", L.frame,
    addr, value, s["cpu.r15"], s["cpu.r14"], s["cpu.r0"], s["cpu.r1"], s["cpu.r2"], s["cpu.r3"], s["cpu.r4"],
    s["cpu.r5"]))
end)
