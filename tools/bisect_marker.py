"""bisect_marker.py: find the ROM-string markers that break a scene (phase 5 marker-build triage).

  python -X utf8 tools/bisect_marker.py SCENE [--frames 4600] [--ways 4]

Builds `build.py --marker rom:LO-HI` variants (only the ROM strings in [LO, HI) get marker text), warps to SCENE
in each (tools/debug/warp_all.py) and narrows to the range whose markers make the warp fail, splitting the
current range `--ways` ways per round, in parallel. Assumes one culprit range (re-run on the rest after a fix).
Prints the culprit string ids. Work files: build/bisect_*.gba, work/qa/bisect/.
"""
import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import marker  # noqa: E402
from skill import SKILL  # noqa: E402


def inked(png, box, colours):
    """True if the crop x,y,w,h of png holds at least `colours` distinct colours (text drawn, not a blank fill)."""
    from PIL import Image
    x, y, w, h = box
    return len(set(Image.open(png).convert("RGB").crop((x, y, x + w, y + h)).getdata())) >= colours


def passes(lo, hi, scene, frames, tag, ink=None):
    rom = ROOT / "build" / ("bisect_%s.gba" % tag)
    subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "build.py"), "--marker", "rom:%X-%X" % (lo, hi),
                    "--out", str(rom)], check=True, capture_output=True)
    out = ROOT / "work" / "qa" / "bisect" / tag
    if ink:  # visual predicate: one shot at frame N, the box must hold drawn text
        frame, box, colours = ink
        subprocess.run([sys.executable, "-X", "utf8", SKILL + "/scripts/emu.py", str(rom), "--out", str(out),
                        "--script", str(ROOT / "tools" / "debug" / "warp.lua"), "--var", "SCENE='%s'" % scene,
                        "--frames", str(frame + 10), "--shots", str(frame)], capture_output=True)
        png = out / ("f%06d.png" % frame)
        return png.exists() and inked(png, box, colours)
    r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "debug" / "warp_all.py"), str(rom),
                        "--only", "^%s$" % scene, "--frames", str(frames), "--out", str(out)], capture_output=True)
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scene")
    ap.add_argument("--frames", type=int, default=4600)
    ap.add_argument("--ways", type=int, default=4)
    ap.add_argument("--ink", metavar="FRAME:X,Y,W,H[:COLOURS]",
                    help="pass = the shot at FRAME has text in the box (>= COLOURS distinct colours, default 4), "
                         "instead of = the warp succeeds (for blank-window bugs)")
    args = ap.parse_args()
    ink = None
    if args.ink:
        parts = args.ink.split(":")
        ink = (int(parts[0]), tuple(int(v) for v in parts[1].split(",")), int(parts[2]) if len(parts) > 2 else 4)
    offs = sorted(t[0] for t in marker.rom_markers())
    cand = offs
    rnd = 0
    while len(cand) > 1:
        rnd += 1
        k = min(args.ways, len(cand))
        parts = [cand[i * len(cand) // k:(i + 1) * len(cand) // k] for i in range(k)]
        with ThreadPoolExecutor(k) as ex:
            res = list(ex.map(lambda ip: passes(ip[1][0], ip[1][-1] + 1, args.scene, args.frames,
                                                "r%d_%d" % (rnd, ip[0]), ink), enumerate(parts)))
        bad = [p for p, ok in zip(parts, res) if not ok]
        print("round %d: %d strings in %d parts, failing: %s" % (
            rnd, len(cand), k, ", ".join("%06X-%06X" % (p[0], p[-1]) for p in bad) or "none"), flush=True)
        if not bad:
            print("no single part fails alone: the breakage needs markers from several parts")
            print("candidates: " + " ".join("r%06X" % o for o in cand))
            return
        cand = bad[0]
    print("culprit: r%06X" % cand[0])


if __name__ == "__main__":
    main()
