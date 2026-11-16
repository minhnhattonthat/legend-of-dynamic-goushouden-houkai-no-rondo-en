"""msgview.py: show every script message in game through the forced message viewer (text coverage, phase 8).

    python -X utf8 tools/msgview.py [ROM] [--chunks 8] [--jobs 2] [--only FILE] [--shots] [--out work/qa/msgview]

Splits the message ids (script/archive/*.json `msg`, first id per slot) into chunks; each chunk is one cold-boot
run: warp to map_290 (its entry event shows 4 messages), tools/lua/msgview.lua swaps the id at the lookup
0x08017E18 and reloads a state before the event whenever it runs dry, tools/lua/mash.lua advances the boxes, and
$SKILL textcover.lua logs the id-map reads, so `textcover.py work/qa/msgview build/goushouden_en.strings.tsv`
counts them. --only: a file of message ids (decimal) to show instead of all. --shots: one shot per message
(msg_<id>.png in the chunk dir) for reading the boxes. Prints, per chunk, how many ids it reached.
"""
import argparse
import concurrent.futures as cf
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract  # noqa: E402
import cover_ranges  # noqa: E402
from skill import SKILL  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FRAMES_PER_MSG = 260  # measured: map_290 + mash every 24 frames (box open, 1-3 pages, close) plus reload slack
SCENE, MV_FROM, MASH_FROM = "map_290", 500, 340


def all_ids():
    out = []
    for name in extract.script_files():
        if name.startswith("archive/"):
            out += [e["msg"][0] for e in extract.load(name) if e.get("msg")]
    return out


def run(rom, ids, d, ranges, shots):
    d.mkdir(parents=True, exist_ok=True)
    (d / "ids.txt").write_text("".join("%d\n" % i for i in ids))
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), str(rom), "--out", str(d),
           "--script", str(ROOT / "tools" / "debug" / "warp.lua"), "--var", "SCENE='%s'" % SCENE,
           "--script", str(ROOT / "tools" / "lua" / "msgview.lua"),
           "--var", "IDS='%s'" % (d / "ids.txt").as_posix(), "--var", "MV_FROM=%d" % MV_FROM, "--var", "LOOP=1",
           "--script", str(ROOT / "tools" / "lua" / "mash.lua"), "--var", "FROM=%d" % MASH_FROM,
           "--script", str(Path(SKILL) / "scripts" / "lua" / "probes" / "textcover.lua"), "--var", "RANGES='%s'" % ranges,
           "--frames", str(MV_FROM + 1000 + FRAMES_PER_MSG * len(ids)),
           "--timeout", str(300 + 3 * len(ids))]  # measured ~1.4 s of wall clock per message with 3 emulators up
    if shots:
        cmd += ["--var", "MV_SHOTS=1"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    log = (d / "log.txt").read_text(encoding="utf-8", errors="replace") if (d / "log.txt").exists() else ""
    got = len(re.findall(r"^MSG \d+", log, re.M))
    return d.name, p.returncode, got, len(ids), "MSGVIEW_DONE" in log


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", default=str(ROOT / "build" / "goushouden_en.gba"))
    ap.add_argument("--chunks", type=int, default=8)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--only")
    ap.add_argument("--shots", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "work" / "qa" / "msgview"))
    a = ap.parse_args()
    rom = Path(a.rom).resolve()
    a.out = str(Path(a.out).resolve())  # the Lua side opens ids.txt from the emulator's own working dir
    ids = [int(x) for x in Path(a.only).read_text().split()] if a.only else all_ids()
    ranges = cover_ranges.ranges(rom.with_suffix(".strings.tsv"))
    n = max(1, min(a.chunks, len(ids)))
    parts = [ids[i::n] for i in range(n)]
    bad = 0
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        futs = [ex.submit(run, rom, part, Path(a.out) / ("c%02d" % i), ranges, a.shots) for i, part in enumerate(parts)]
        for f in cf.as_completed(futs):
            name, code, got, want, done = f.result()
            bad += not done
            print("%s: exit %d, %d/%d messages%s" % (name, code, got, want, "" if done else "  NOT DONE"), flush=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
