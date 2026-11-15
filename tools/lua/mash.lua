-- Press BTN (default a) for 4 frames every EVERY frames from FROM to TO: play through a battle after a warp.
--   emu.py ... --script tools/debug/warp.lua --var "SCENE='k_ode'" --script tools/lua/mash.lua --var FROM=600
local from, to, every, btn = FROM or 0, TO or 1e9, EVERY or 24, BTN or "a"
L.on_frame(function(f)
  if f >= from and f <= to and (f - from) % every == 0 then L.press(btn, 4) end
end)
