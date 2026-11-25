-- Run a player's mGBA / RetroArch-mGBA state in Mesen: start from a Mesen state in the same game mode (--state-in,
-- e.g. work/states/k_ode.mss for a battle), and at the first endFrame (scanline 160, where RetroArch states are
-- taken) overwrite IWRAM, EWRAM, VRAM, OAM, palette, the display IO registers and the CPU registers with the
-- tools/mgba_state.py dumps, then reload the pipeline at the player's PC.
--   python -X utf8 tools/mgba_state.py PLAYER.state1 work/p1
--   emu.py build/goushouden_en.gba --out D --state-in work/states/k_ode.mss --frames 600 --shot-every 10 \
--          --script tools/lua/mgba_load.lua --var "MGBA=[[C:/abs/work/p1]]"
-- Not copied: sound, DMA and timer registers, the scheduler. Game logic and RAM run true.
assert(MGBA, 'set --var "MGBA=[[dump prefix]]"')
dofile(MGBA .. ".lua")
local function inject(ext, mem)
  local d = L.read_file(MGBA .. "." .. ext)
  for i = 1, math.min(#d, emu.getMemorySize(mem)) do emu.write(i - 1, d:byte(i), mem) end
end
local done = false
emu.addEventCallback(L.safe(function()
  if done then return end
  done = true
  inject("iwram", emu.memType.gbaIntWorkRam)
  inject("ewram", emu.memType.gbaExtWorkRam)
  inject("vram", emu.memType.gbaVideoRam)
  inject("oam", emu.memType.gbaSpriteRam)
  inject("pram", emu.memType.gbaPaletteRam)
  local io = L.read_file(MGBA .. ".io")
  local function io_range(lo, hi)
    for a = lo, hi do emu.write(0x04000000 + a, io:byte(a + 1), emu.memType.gbaMemory) end
  end
  io_range(0x00, 0x03)   -- DISPCNT
  io_range(0x08, 0x55)   -- BG control, scroll, affine, window, mosaic, blend
  io_range(0x200, 0x201) -- IE
  io_range(0x208, 0x208) -- IME
  emu.setState(MGBA_REGS)
  L.log("mgba state injected: " .. MGBA_INFO)
end), emu.eventType.endFrame)
