-- OBJ render cycles per scanline (GBATEK: 1210 per line, 954 with DISPCNT bit 5 "H-Blank interval free"; a normal
-- OBJ costs its width, an affine one 10 + 2 * its box width; hardware and mGBA drop what is past the budget, Mesen
-- draws everything). Logs each frame from FROM whose worst line is over LIMIT (default: the budget), with that
-- line's OBJs in OAM order "i:x,y,wxh[A],tile" and the running total where the budget ran out (issue #1: the
-- speaker tag's last letter cut off in mGBA).
--   emu.py ... --script tools/lua/objcycles.lua [--var FROM=0] [--var LIMIT=900] [--var MAXN=40]
local SIZES = { [0] = { { 8, 8 }, { 16, 16 }, { 32, 32 }, { 64, 64 } }, [1] = { { 16, 8 }, { 32, 8 }, { 32, 16 }, { 64, 32 } },
  [2] = { { 8, 16 }, { 8, 32 }, { 16, 32 }, { 32, 64 } } }
local n, last = 0, ""
L.on_frame(function(f)
  if f < (FROM or 0) or n >= (MAXN or 40) then return end
  local m = emu.memType.gbaMemory
  local dispcnt = emu.read16(0x04000000, m)
  local budget = (dispcnt & 0x20) ~= 0 and 954 or 1210
  local objs = {}
  for i = 0, 127 do
    local a0 = emu.read16(0x07000000 + i * 8, m)
    local a1 = emu.read16(0x07000000 + i * 8 + 2, m)
    local a2 = emu.read16(0x07000000 + i * 8 + 4, m)
    local affine, dbl = (a0 & 0x100) ~= 0, (a0 & 0x200) ~= 0
    local shape = (a0 >> 14) & 3
    if (affine or not dbl) and shape ~= 3 then
      local wh = SIZES[shape][((a1 >> 14) & 3) + 1]
      local w, h = wh[1], wh[2]
      if affine and dbl then w, h = w * 2, h * 2 end
      objs[#objs + 1] = { i = i, x = a1 & 0x1FF, y = a0 & 0xFF, w = w, h = h, aff = affine, tile = a2 & 0x3FF,
        cost = affine and (10 + 2 * w) or w }
    end
  end
  local worst, wl = 0, 0
  for line = 0, 159 do
    local c = 0
    for _, o in ipairs(objs) do
      local dy = (line - o.y) & 0xFF
      if dy < o.h then c = c + o.cost end
    end
    if c > worst then worst, wl = c, line end
  end
  if worst <= (LIMIT or budget) then return end
  local parts, run, cut = {}, 0, nil
  for _, o in ipairs(objs) do
    if ((wl - o.y) & 0xFF) < o.h then
      run = run + o.cost
      if not cut and run > budget then cut = o.i end
      parts[#parts + 1] = string.format("%d:%d,%d,%dx%d%s,%X", o.i, o.x, o.y, o.w, o.h, o.aff and "A" or "", o.tile)
    end
  end
  local s = string.format("line %d: %d cycles of %d, budget runs out at OBJ %s | %s", wl, worst, budget,
    tostring(cut), table.concat(parts, " "))
  if s ~= last then
    n = n + 1
    L.log("f" .. f .. " " .. s)
    last = s
  end
end)
