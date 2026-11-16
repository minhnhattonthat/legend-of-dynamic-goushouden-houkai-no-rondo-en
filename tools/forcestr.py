"""forcestr.py: draw every ROM string (rXXXXXX ids) through the menu printer in game (text coverage, phase 8).

    python -X utf8 tools/forcestr.py [ROM] [--ids FILE] [--chunks N] [--only K,..] [--shots] [--out work/qa/forcestr]

The item menu (scene m1_item) draws its list names with the menu printer 0x0800E3D0(window, string) via the wrapper
0x0800E87C, one call every ~2 frames from f400 (FVCALL probe: 12 names + header by f423). tools/lua/forceview.lua
swaps r1 (the string) on each of those calls for the next ROM string's address in this build and reloads a state
saved at f399 whenever IDLE frames pass with no call, so ~13 strings draw per reload. $SKILL textcover.lua logs the
reads, so `textcover.py` counts them. This proves each string is read and drawn by the game's menu printer, not
that it fits its own box: that stays with the tour, the width lint and visual QA.

--ids: one id per line (default: every rXXXXXX id of the build's strings.tsv not waived in docs/text_unshown.tsv).
Chunks keep each emulator run short (the memory reaper killed hour-long runs); a chunk with FORCEVIEW_DONE in its
log is skipped on a rerun unless its value list changed.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cover_ranges  # noqa: E402
from skill import SKILL  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCENE, FROM, IDLE, PER = "m1_item", 399, 60, 8   # PER: frames per string (13 per ~90-frame reload cycle)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", default=str(ROOT / "build" / "goushouden_en.gba"))
    ap.add_argument("--ids")
    ap.add_argument("--chunks", type=int, default=4)
    ap.add_argument("--only", help="comma list of chunk numbers")
    ap.add_argument("--shots", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "work" / "qa" / "forcestr"))
    a = ap.parse_args()
    rom = Path(a.rom).resolve()
    stsv = rom.with_suffix(".strings.tsv")
    strings = {}
    for line in stsv.read_text(encoding="utf-8").splitlines():
        sid, addr = line.split("\t")[:2]
        strings[sid] = int(addr, 16)
    if a.ids:
        ids = [x.split("\t")[0] for x in Path(a.ids).read_text(encoding="utf-8").split("\n") if x.strip()]
    else:
        waived = {x.split("\t")[0] for x in (ROOT / "docs" / "text_unshown.tsv").read_text(encoding="utf-8")
                  .splitlines() if "\t" in x and x.split("\t")[1].strip()}
        ids = [s for s in strings if s.startswith("r") and s not in waived]
    ranges = cover_ranges.ranges(stsv)
    n = max(1, a.chunks)
    size = -(-len(ids) // n)
    bad = 0
    for c in range(n):
        if a.only and str(c) not in a.only.split(","):
            continue
        part = ids[c * size:(c + 1) * size]
        if not part:
            continue
        d = Path(a.out).resolve() / ("c%02d" % c)
        d.mkdir(parents=True, exist_ok=True)
        vals = d / "vals.txt"
        text = "".join("0x%08X %s\n" % (0x08000000 | strings[s], s) for s in part)
        log = d / "log.txt"
        if vals.exists() and vals.read_text() == text and log.exists() and "FORCEVIEW_DONE" in log.read_text(
                encoding="utf-8", errors="replace"):
            print("c%02d done already (%d ids)" % (c, len(part)), flush=True)
            continue
        vals.write_text(text)
        cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), str(rom), "--out", str(d),
               "--script", str(ROOT / "tools" / "debug" / "warp.lua"), "--var", "SCENE='%s'" % SCENE,
               "--script", str(ROOT / "tools" / "lua" / "forceview.lua"), "--var", "FV_ADDR=0x0800E3D0",
               "--var", "FV_REG='r1'", "--var", "FV_VALS='%s'" % vals.as_posix(),
               "--var", "FV_FROM=%d" % FROM, "--var", "LOOP=1", "--var", "IDLE=%d" % IDLE,
               "--script", str(Path(SKILL) / "scripts" / "lua" / "probes" / "textcover.lua"),
               "--var", "RANGES='%s'" % ranges,
               "--frames", str(FROM + 600 + PER * len(part) * 3), "--timeout", str(300 + len(part))]
        if a.shots:
            cmd += ["--var", "FV_SHOTS=1", "--var", "FV_SHOT=30"]
        p = subprocess.run(cmd, capture_output=True, text=True)
        logt = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
        got = len(re.findall(r"^FV [0-9A-F]+ ", logt, re.M))
        done = "FORCEVIEW_DONE" in logt
        bad += not done
        print("c%02d: exit %d, %d/%d ids%s" % (c, p.returncode, got, len(part), "" if done else "  NOT DONE"),
              flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
