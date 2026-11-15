-- Log every call to the packed-file unpacker unpack(src, dst) at 0x08000F58 (docs/re/compression.md):
-- frame, src, dst, header word (type << 24 | size), caller. With DUMP_DIR set (absolute path), also write each
-- distinct block's decoded output to DUMP_DIR/<src>_<type>.bin. The dump is taken at 0x08000FDA, where the
-- decoders (types 1-3) have filled the temp buffer r4 (r5 bytes) and before it is copied to dst.
--   emu.py ... --script tools/lua/unpacklog.lua [--var "DUMP_DIR=[[C:/abs/dir]]"]
local seen = {}
local cur = nil

L.on_exec(0x08000F58, 0x08000F59, function()
  local s = emu.getState()
  local src, dst, lr = s["cpu.r0"] or 0, s["cpu.r1"] or 0, s["cpu.r14"] or 0
  local hdr = 0
  if src >= 0x02000000 and src < 0x0A000000 then hdr = emu.read32(src, emu.memType.gbaMemory) end
  local key = string.format("%08X", src)
  local first = not seen[key]
  seen[key] = true
  L.log(string.format("f%d unpack src=%08X dst=%08X hdr=%08X lr=%08X%s", L.frame, src, dst, hdr, lr, first and " new" or ""))
  cur = first and {src = src, typ = hdr >> 24} or nil
end)

L.on_exec(0x08000FDA, 0x08000FDB, function()
  if not (DUMP_DIR and cur) then return end
  local s = emu.getState()
  local buf, size = s["cpu.r4"] or 0, s["cpu.r5"] or 0
  if size == 0 or size > 0x40000 or cur.typ < 1 or cur.typ > 3 then cur = nil return end
  local t = {}
  for i = 0, size - 1 do t[#t + 1] = string.char(emu.read(buf + i, emu.memType.gbaMemory)) end
  local f = io.open(string.format("%s/%08X_%d.bin", DUMP_DIR, cur.src, cur.typ), "wb")
  if f then f:write(table.concat(t)) f:close() end
  cur = nil
end)
