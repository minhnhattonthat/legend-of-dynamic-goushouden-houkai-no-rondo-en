-- Forced message viewer (text coverage, phase 8): every dialogue lookup shows the next message from a list.
--   emu.py ROM --script tools/debug/warp.lua --var "SCENE='map_290'" --script tools/lua/msgview.lua
--          --var "IDS='C:/abs/ids.txt'" --var MV_FROM=500 --var LOOP=1 [--var MV_SHOTS=1]
--          --script tools/lua/mash.lua --var FROM=340        (tools/msgview.py runs it in parallel chunks)
-- 0x08017E18(r0 = message id) looks the id up in the script archive's id map and unpacks the file
-- (docs/re/text.md §1); on entry, from frame MV_FROM, r0 is replaced by the next id from IDS (one decimal message id
-- per line). Logs "MSG <id> f<frame>" per substitution and "MSGVIEW_DONE" when the list runs out (then stops,
-- after HOLD frames). Without IDS it only logs the game's own lookups ("MSGCALL <id>").
-- MV_SHOTS=1: a screenshot msg_<id>.png MV_SHOT frames after each substitution (the box drawn). (Not SHOTS /
-- FROM: emu.py and mash.lua use those globals.)
local from, hold, shotAt = MV_FROM or 0, HOLD or 120, MV_SHOT or 90
local ids, nexti = {}, 1
if IDS then
  for line in io.lines(IDS) do
    local n = tonumber(line)
    if n then ids[#ids + 1] = n end
  end
end
-- LOOP=1: save a state at frame MV_FROM and load it again whenever IDLE frames pass with no lookup (the scene's
-- event ran out of messages), so one short event (map_290's 4-message entry event) shows the whole list.
local idle, lastCall, state, loading = IDLE or 300, nil, OUT .. "msgview_loop.mss", false
local pending, doneAt = {}, nil
L.on_exec(0x08017E18, 0x08017E18, function()
  local r0 = emu.getState()["cpu.r0"]
  if not IDS then L.log(string.format("MSGCALL %d f%d", r0, L.frame)); return end
  if L.frame < from or nexti > #ids then return end
  lastCall = L.frame
  local id = ids[nexti]
  nexti = nexti + 1
  emu.setState({ ["cpu.r0"] = id })
  L.log(string.format("MSG %d f%d (was %d)", id, L.frame, r0))
  if MV_SHOTS then pending[#pending + 1] = { f = L.frame + shotAt, id = id } end
  if nexti > #ids then doneAt = L.frame end
end)
L.on_frame(function(f)
  while pending[1] and f >= pending[1].f do
    L.shot(string.format("msg_%05d.png", pending[1].id))
    table.remove(pending, 1)
  end
  if doneAt and f >= doneAt + hold then
    L.log("MSGVIEW_DONE f" .. f)
    L.finish(0)
  end
  if LOOP and IDS then
    if f == from then L.save_state(state); lastCall = f end
    if f > from and not doneAt and not loading and lastCall and f - lastCall >= idle then
      loading = true
      L.log("MSGVIEW_RELOAD f" .. f)
      L.load_state(state, function() loading = false; lastCall = L.frame end)
    end
  end
end)
