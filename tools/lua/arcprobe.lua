-- Which archive does a scene read? Log each call of the archive reader 0x0800FE88(id r0, archive r1, ?, dest r3)
-- with the caller, deduplicated by (archive, caller). Archives: docs/re/text.md §1 / §1b (bases move in a build).
--   emu.py ROM --out DIR --script tools/debug/warp.lua --script tools/lua/arcprobe.lua --var "SCENE='m1_book'"
local seen = {}
L.on_exec(0x0800FE88, 0x0800FE88, function()
  local s = emu.getState()
  local key = string.format("%08X %08X", s["cpu.r1"], s["cpu.r14"])
  if seen[key] then return end
  seen[key] = true
  L.log(string.format("f%d arc=%08X id=%d lr=%08X dest=%08X", L.frame, s["cpu.r1"], s["cpu.r0"], s["cpu.r14"],
    s["cpu.r3"]))
end)
