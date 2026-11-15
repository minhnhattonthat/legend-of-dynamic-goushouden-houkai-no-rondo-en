-- Where is the CPU? Log the PC and LR once every EVERY frames from frame FROM (a hang or a wait loop shows as the
-- same few addresses).
--   emu.py ROM --out DIR --script tools/debug/warp.lua --script tools/lua/pcsample.lua --var FROM=2700
local from, every = FROM or 0, EVERY or 30
L.on_frame(function()
  if L.frame >= from and L.frame % every == 0 then
    local s = emu.getState()
    L.log(string.format("f%d pc=%08X lr=%08X sp=%08X", L.frame, s["cpu.r15"], s["cpu.r14"], s["cpu.r13"]))
  end
end)
