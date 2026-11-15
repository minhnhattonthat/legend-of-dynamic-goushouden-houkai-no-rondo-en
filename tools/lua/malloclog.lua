-- Log every malloc (0x08000BE8, size in r0) and its caller from frame FROM, up to MAXN calls; with the OOM trap
-- (tools/lua/oom.lua) it shows which allocation eats the heap.
--   emu.py ROM --out DIR --script tools/debug/warp.lua --script tools/lua/malloclog.lua --var FROM=2600
local from, maxn, n = FROM or 0, MAXN or 400, 0
L.on_exec(0x08000BE8, 0x08000BE8, function()
  if L.frame < from or n >= maxn then return end
  n = n + 1
  local s = emu.getState()
  L.log(string.format("f%d malloc %d lr=%08X", L.frame, s["cpu.r0"], s["cpu.r14"]))
end)
