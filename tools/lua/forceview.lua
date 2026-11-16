-- Forced viewer, generic form of msgview.lua (text coverage, phase 8): every call of a routine shows the next value
-- from a list, through the game's own drawing path.
--   emu.py ROM --script tools/debug/warp.lua --var "SCENE='...'" --script tools/lua/forceview.lua
--          --var FV_ADDR=0x0807C970 --var "FV_REG='r0'" --var "FV_VALS='C:/abs/vals.txt'" --var FV_FROM=500
--          [--var LOOP=1] [--var FV_SHOTS=1] [--var FV_ARGS='r1=2,r2=-1'] --script tools/lua/mash.lua --var FROM=..
-- On entry of FV_ADDR, from frame FV_FROM, register FV_REG is replaced by the next value of FV_VALS (one per line,
-- hex 0x.. or decimal; text after the value is ignored). FV_ARGS also forces other registers on each substitution.
-- Logs "FV <value> f<frame>" per substitution and "FORCEVIEW_DONE" when the list runs out (after HOLD frames).
-- Without FV_VALS it only logs the game's own calls ("FVCALL r0 r1 r2 r3 lr"). LOOP=1: a state saved at FV_FROM is
-- loaded again whenever IDLE frames pass with no call. FV_SHOTS=1: fv_<n>.png FV_SHOT frames after each one.
local addr, reg, from, hold, shotAt = FV_ADDR, "cpu." .. (FV_REG or "r0"), FV_FROM or 0, HOLD or 120, FV_SHOT or 90
local vals, nexti = {}, 1
if FV_VALS then
  for line in io.lines(FV_VALS) do
    local tok = line:match("^%s*(%S+)")
    local n = tok and tonumber(tok)
    if n then vals[#vals + 1] = n end
  end
end
local extra = {}
for k, v in string.gmatch(FV_ARGS or "", "(r%d+)=(-?%w+)") do
  local n = tonumber(v)
  if n < 0 then n = n + 0x100000000 end
  extra["cpu." .. k] = n
end
local idle, lastCall, state, loading = IDLE or 300, nil, OUT .. "forceview_loop.mss", false
local pending, doneAt = {}, nil
-- FV_IF='r1=0x08132E74': only calls with that register value count (one archive of the shared reader 0x0800FE88).
local ifReg, ifVal = string.match(FV_IF or "", "(r%d+)=(%w+)")
L.on_exec(addr, addr, function()
  local s = emu.getState()
  if ifReg and s["cpu." .. ifReg] ~= tonumber(ifVal) then return end
  if not FV_VALS then
    L.log(string.format("FVCALL %08X %08X %08X %08X lr %08X f%d", s["cpu.r0"], s["cpu.r1"], s["cpu.r2"], s["cpu.r3"],
      s["cpu.r14"] or 0, L.frame))
    return
  end
  if L.frame < from or nexti > #vals then return end
  lastCall = L.frame
  local v = vals[nexti]
  nexti = nexti + 1
  local set = { [reg] = v }
  for k, x in pairs(extra) do set[k] = x end
  emu.setState(set)
  L.log(string.format("FV %X f%d (was %X)", v, L.frame, s[reg]))
  if FV_SHOTS then pending[#pending + 1] = { f = L.frame + shotAt, n = nexti - 1 } end
  if nexti > #vals then doneAt = L.frame end
end)
L.on_frame(function(f)
  while pending[1] and f >= pending[1].f do
    L.shot(string.format("fv_%04d.png", pending[1].n))
    table.remove(pending, 1)
  end
  if doneAt and f >= doneAt + hold then
    L.log("FORCEVIEW_DONE f" .. f)
    L.finish(0)
  end
  if LOOP and FV_VALS then
    if f == from then L.save_state(state); lastCall = f end
    if f > from and not doneAt and not loading and lastCall and f - lastCall >= idle then
      loading = true
      L.log("FORCEVIEW_RELOAD f" .. f)
      L.load_state(state, function() loading = false; lastCall = L.frame end)
    end
  end
end)
