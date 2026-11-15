-- Log the story variable block (0x030048A0, 0x200 bytes) and event-flag bits (0x03004AA0, FLAG_BYTES bytes) as hex
-- at frame AT (default 2), one "VARS"/"FLAGS" line each, for diffing story progress between savestates.
--   emu.py ROM --out DIR --state-in S.mss --frames 3 --script tools/lua/flagdump.lua [--var AT=2]
local at, nflag = AT or 2, FLAG_BYTES or 0x200
local function hex(base, n)
  local t = {}
  for i = 0, n - 1 do t[#t + 1] = string.format("%02X", emu.read(base + i, emu.memType.gbaMemory)) end
  return table.concat(t)
end
L.on_frame(function(f)
  if f == at then
    L.log("VARS " .. hex(0x030048A0, 0x200))
    L.log("FLAGS " .. hex(0x03004AA0, nflag))
  end
end)
