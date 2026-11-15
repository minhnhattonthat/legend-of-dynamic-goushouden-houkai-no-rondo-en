"""Whole-map picture of a field map, stitched from teleported warps (warp.lua's at=X:Y step), to find signs.

    python -X utf8 tools/debug/mapshot.py 245 [246 ..] [--rom ROM] [--jobs 4] [--out work/qa/maps]

Per map: one warp at the spawn reads the map size (warp.lua logs `FIELD map WxH cells camera X,Y`), then one warp
per screen of a grid (camera steps of 240 x 160, the last row/column flush with the map edge; player = camera +
(120, 88)). Writes OUT/map_NNN.png (the whole map, 1x, sprites included) and OUT/map_NNN.txt: one line per screen,
`camera_x camera_y  at=PX:PY`. A sign found at map pixel (mx, my) is on screen at (mx - cx, my - cy) in the warp
`2,0,map=NNN,at=PX:PY` (add it to tools/debug/scenes.txt and point a gfxlabel SCREENS entry at it: the game redraws
the visible area into VRAM screen-relative, so the ppudump BG rect is the screen rect when the camera is a multiple
of 8, which these grid cameras are, except a map edge flush at a size that isn't).
ROM defaults to the original in rom/.
"""
import argparse
import concurrent.futures as cf
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill import SKILL  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ORIG = next((ROOT / "rom").glob("*.gba"), None)
FIELD = re.compile(r"FIELD map (\d+)x(\d+) cells camera (\d+),(\d+)")


def warp(rom, out, name, spec):
    out.mkdir(parents=True, exist_ok=True)
    scenes = out / "scenes.txt"
    scenes.write_text(f"{name} {spec}\n", encoding="utf-8")
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), str(rom), "--out", str(out),
           "--script", str(ROOT / "tools" / "debug" / "warp.lua"), "--var", f"SCENE='{name}'",
           "--var", f"SCENES=[[{scenes.resolve().as_posix()}]]", "--frames", "900"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = (out / "log.txt").read_text(encoding="utf-8", errors="replace") if (out / "log.txt").exists() else ""
    m = FIELD.search(log)
    shot = out / f"warp_{name}.png"
    if r.returncode or not m or not shot.exists():
        raise SystemExit(f"{name}: warp failed (exit {r.returncode}): {r.stdout[-300:]}")
    return tuple(int(v) for v in m.groups()), shot


def steps(total, view):
    s = list(range(0, max(total - view, 0) + 1, view))
    if s[-1] < total - view:
        s.append(total - view)
    return s


def one_map(rom, n, out, jobs):
    work = out / f"map_{n:03d}"
    (w, h, _, _), _ = warp(rom, work / "spawn", f"m{n}", f"2,0,map={n}")
    W, H = w * 8, h * 8
    grid = [(cx, cy) for cy in steps(H, 160) for cx in steps(W, 240)]
    pic = Image.new("RGB", (max(W, 240), max(H, 160)))
    lines = []
    with cf.ThreadPoolExecutor(jobs) as ex:
        futs = {ex.submit(warp, rom, work / f"{cx}_{cy}", f"m{n}_{cx}_{cy}",
                          f"2,0,map={n},at={cx + 120}:{cy + 88}"): (cx, cy) for cx, cy in grid}
        for f in cf.as_completed(futs):
            cx, cy = futs[f]
            (_, _, rx, ry), shot = f.result()
            pic.paste(Image.open(shot).convert("RGB"), (rx, ry))
            lines.append(f"{rx} {ry}  at={cx + 120}:{cy + 88}" + ("" if (rx, ry) == (cx, cy) else f"  (asked {cx},{cy})"))
    pic.save(out / f"map_{n:03d}.png")
    (out / f"map_{n:03d}.txt").write_text("\n".join(sorted(lines, key=lambda s: tuple(map(int, s.split()[1::-1])))) + "\n",
                                          encoding="utf-8")
    print(f"map_{n:03d}: {W}x{H} px, {len(grid)} screens -> {out / f'map_{n:03d}.png'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("maps", nargs="+", type=int)
    ap.add_argument("--rom", default=str(ORIG))
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--out", default=str(ROOT / "work" / "qa" / "maps"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for n in a.maps:
        one_map(a.rom, n, out, a.jobs)


if __name__ == "__main__":
    main()
