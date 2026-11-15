-- Log the frame of every unpack() (0x08000F58) of the blocks in SRCS (GBA addresses, comma-separated string),
-- with its destination (r1) and return address, to find the scene and moment a block loads (phase 8 graphics).
-- Without SRCS: every unpack from frame FROM on (the battle-effect loader 0x08011BEF calls it too).
--   emu.py ... --script tools/debug/warp.lua --var "SCENE='game_over'" --script tools/lua/unpackat.lua
--     --var "SRCS='0x082F5C04,0x08362154'"
local want, any = {}, true
for s in string.gmatch(SRCS or "", "[^,]+") do want[tonumber(s)] = true; any = false end
local from = FROM or 0
L.on_exec(0x08000F58, 0x08000F59, function()
  local s = emu.getState()
  local r0 = s["cpu.r0"] or 0
  if not (want[r0] or (any and L.frame >= from)) then return end
  L.log(string.format("f%d unpack %08X dst=%08X lr=%08X", L.frame, r0, s["cpu.r1"] or 0, s["cpu.r14"] or 0))
end)
