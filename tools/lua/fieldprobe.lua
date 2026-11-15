-- Field budgets for the width gate: log every string the menu printer 0x0800E3D0 (window r0, string r1) draws,
-- once per (window, pen x, pen y, text), with the window's geometry, and the pen after the call (read at the next
-- call / next frame). On the marker build the text starts with the ROM string's offset (`D0000:abc...`), so
-- tools/fields.py maps each drawn field to its script/rom id and to the next field on the same row.
--   warp_all.py build/goushouden_marker.gba --script tools/lua/fieldprobe.lua --out work/qa/fields
-- Log line: FIELD f<frame> w=<window> x=<pen x> y=<pen y> ec=<+EC> ee=<+EE> m=<font mode> cw=<cell w> end=<pen x
-- after> s=<text, non-ASCII bytes as \xx>
local seen, pending = {}, nil
local function ok(a) return a >= 0x02000000 and a < 0x0A000000 end
local function rd8(a) if not ok(a) then return 0 end return emu.read(a, emu.memType.gbaMemory, false) end
local function rd16s(a)
  local v = rd8(a) | (rd8(a + 1) << 8)
  if v >= 0x8000 then v = v - 0x10000 end
  return v
end
local function rd32(a) if not ok(a) then return 0 end return emu.read32(a, emu.memType.gbaMemory, false) end
local function text(p)
  local t = {}
  for i = 0, 63 do
    local c = rd8(p + i)
    if c == 0 then break end
    if c >= 0x20 and c < 0x7F and c ~= 0x5C then t[#t + 1] = string.char(c) else t[#t + 1] = string.format("\\%02X", c) end
  end
  return table.concat(t)
end
local function flush()
  if pending then
    L.log(pending.line .. string.format(" end=%d s=%s", rd32(pending.w + 0xD8), pending.s))
    pending = nil
  end
end
L.on_exec(0x0800E3D0, 0x0800E3D0, function()
  flush()
  local s = emu.getState()
  local w, p = s["cpu.r0"], s["cpu.r1"]
  local mode = rd32(w + 0xE0)
  local x, y = rd32(w + 0xD8), rd32(w + 0xDC)
  local str = text(p)
  local key = string.format("%08X %d %d %s", w, x, y, str)
  if seen[key] then return end
  seen[key] = true
  pending = { w = w, s = str, line = string.format("FIELD f%d w=%08X src=%08X lr=%08X x=%d y=%d ec=%d ee=%d m=%d cw=%d",
    L.frame, w, p, s["cpu.r14"], x, y, rd16s(w + 0xEC), rd16s(w + 0xEE), mode, rd32(w + mode * 16 + 4)) }
end)
L.on_frame(flush)
