-- Who asks unpack() (0x08000F58) for one source? Logs registers and 24 stack words when r0 == SRC, and every
-- Thumb BL return seen on the stack, to find the loader and its self-relative table (block relocation, phase 8).
--   emu.py ... --script tools/debug/warp.lua --var "SCENE='k_jump'" --script tools/lua/unpackwho.lua --var SRC=0x082F9318
L.on_exec(0x08000F58, 0x08000F59, function()
  local s = emu.getState()
  if (s["cpu.r0"] or 0) ~= SRC then return end
  local regs = {}
  for i = 0, 14 do regs[#regs + 1] = string.format("r%d=%08X", i, s["cpu.r" .. i] or 0) end
  L.log("f" .. L.frame .. " " .. table.concat(regs, " "))
  local sp = s["cpu.r13"] or 0
  local w = {}
  for i = 0, 23 do w[#w + 1] = string.format("%08X", emu.read32(sp + 4 * i, emu.memType.gbaMemory)) end
  L.log("  stack " .. table.concat(w, " "))
end)
