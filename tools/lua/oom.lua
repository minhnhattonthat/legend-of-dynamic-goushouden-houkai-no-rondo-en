-- Heap out-of-memory trap: malloc 0x08000BE8 on failure writes the requested size and the free total to
-- 0x06000000/04 and spins at 0x08000C82 (docs/re/memory.md). Log both once when the trap is hit; also log the caller
-- chain of the failing malloc (LR of malloc's caller is on the stack: logged as sp words).
--   emu.py ROM --out DIR --script tools/debug/warp.lua --script tools/lua/oom.lua --var "SCENE='game_over'"
local done = false
-- heap walk: blocks {u32 tag (0x55 = free), u32 size, u32 next}; the head pointer is read at 0x08000C5C ([r0])
local head = nil
local function rd32(a) return emu.read32(a, emu.memType.gbaMemory, false) end
L.on_exec(0x08000C5C, 0x08000C5C, function()
  if not head then
    head = emu.getState()["cpu.r0"]
    L.log(string.format("heap head ptr at %08X", head))
  end
end)
-- HEAPAT=frame: log the free total and the largest free block once at that frame (needs a failed walk earlier, or
-- HEAD=address of the head pointer)
head = HEAD
L.on_frame(function()
  local due = (HEAPAT and L.frame == HEAPAT) or (HEAPEVERY and HEAPFROM and L.frame >= HEAPFROM
    and L.frame % HEAPEVERY == 0)
  if due and head then
    local b, free, big, n = rd32(head), 0, 0, 0
    while b ~= 0 and n < 2000 do
      if HEAPDUMP then L.log(string.format("  block %08X tag=%X size=%d next=%08X", b, rd32(b), rd32(b + 4),
        rd32(b + 8))) end
      if rd32(b) == 0x55 then
        free = free + rd32(b + 4)
        if rd32(b + 4) > big then big = rd32(b + 4) end
      end
      b = rd32(b + 8)
      n = n + 1
    end
    L.log(string.format("f%d heap free=%d largest=%d blocks=%d", L.frame, free, big, n))
  end
end)
L.on_exec(0x08000C72, 0x08000C72, function()  -- r1 = request, r2 = free total, before the stores and the spin
  if done then return end
  done = true
  local s = emu.getState()
  L.log(string.format("f%d OOM request=%d free=%d lr=%08X", L.frame, s["cpu.r1"], s["cpu.r2"], s["cpu.r14"]))
end)
