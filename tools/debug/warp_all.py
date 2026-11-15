"""Warp to every scene in tools/debug/scenes.txt from a cold boot, in parallel, and collect one shot per scene.

    python -X utf8 tools/debug/warp_all.py [ROM] [--only REGEX] [--jobs 4] [--frames 1500] [--states] [--out DIR]

ROM defaults to build/goushouden_en.gba if it exists, else the original in rom/. Each scene runs
emu.py ROM --out DIR/<scene> --script tools/debug/warp.lua --var SCENE=... ; the scene passes when its log has
WARP_DONE and the run exits 0. --states also saves work/states/<scene>.mss (the "regen all states" command: run it
after engine, font or graphics changes). Writes DIR/summary.tsv and DIR/shots/<scene>.png; exit 1 if any failed.
"""
import argparse
import concurrent.futures as cf
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill import SKILL  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCENES = ROOT / "tools" / "debug" / "scenes.txt"
ORIG = next((ROOT / "rom").glob("*.gba"), None)


MAPS = ROOT / "tools" / "debug" / "maps.tsv"
# scenes that need more frames than --frames (game_over walks to a random battle, then loses it: WARP_DONE ~f4040)
MIN_FRAMES = {"game_over": 4500}


def scene_names():
    """scenes.txt entries, then map_NNN for every map in maps.tsv not marked discarded."""
    out = []
    for line in SCENES.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line.split()[0])
    for line in MAPS.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        mid, _name, discarded = line.split("\t")
        if discarded == "0":
            out.append(f"map_{int(mid):03d}")
    return out


def run(rom, scene, out, frames, states, scripts=()):
    d = out / scene
    shutil.rmtree(d, ignore_errors=True)
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), str(rom), "--out", str(d),
           "--script", str(ROOT / "tools" / "debug" / "warp.lua"), "--var", f"SCENE='{scene}'",
           "--frames", str(max(frames, MIN_FRAMES.get(scene, 0))), "--timeout", "600"]
    for s in scripts:
        cmd += ["--script", str(Path(s).resolve())]
    if states:
        st = (ROOT / "work" / "states" / f"{scene}.mss").as_posix()
        cmd += ["--var", f"STATE_OUT=[[{st}]]"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = (d / "log.txt").read_text(encoding="utf-8", errors="replace") if (d / "log.txt").exists() else ""
    m = re.search(r"WARP_DONE f(\d+)", log)
    ok = p.returncode == 0 and m is not None
    shot = d / f"warp_{scene}.png"
    if not shot.exists():
        shot = d / "final.png"
    if shot.exists():
        shutil.copy(shot, out / "shots" / f"{scene}.png")
    why = "" if ok else (f"exit {p.returncode}" if p.returncode else "no WARP_DONE")
    return scene, ok, m.group(1) if m else "-", why


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?")
    ap.add_argument("--only", help="regex on scene names")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--frames", type=int, default=1500)
    ap.add_argument("--states", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "work" / "qa" / "warp_all"))
    ap.add_argument("--script", action="append", default=[], help="extra Lua probe for every scene (repeatable)")
    a = ap.parse_args()
    rom = Path(a.rom) if a.rom else (ROOT / "build" / "goushouden_en.gba")
    if not rom.exists():
        rom = ORIG
    out = Path(a.out)
    (out / "shots").mkdir(parents=True, exist_ok=True)
    names = [n for n in scene_names() if not a.only or re.search(a.only, n)]
    print(f"{len(names)} scenes on {rom.name}, {a.jobs} jobs", flush=True)
    res = []
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for r in ex.map(lambda n: run(rom, n, out, a.frames, a.states, a.script), names):
            res.append(r)
            print(("ok  " if r[1] else "FAIL") + f" {r[0]} done@{r[2]} {r[3]}", flush=True)
    with open(out / "summary.tsv", "w", encoding="utf-8") as f:
        f.write("scene\tok\twarp_done_frame\tnote\n")
        for s, ok, fr, why in res:
            f.write(f"{s}\t{int(ok)}\t{fr}\t{why}\n")
    bad = [r[0] for r in res if not r[1]]
    print(f"{len(res) - len(bad)}/{len(res)} ok" + (f"; failed: {' '.join(bad)}" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
