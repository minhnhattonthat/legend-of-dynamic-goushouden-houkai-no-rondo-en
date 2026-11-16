"""forcearc.py: show every message of the small archives (book B, desc D, effect E, place P) in game (text coverage).

    python -X utf8 tools/forcearc.py [ROM] [--only book,desc] [--shots] [--limit N] [--out work/qa/forcearc]

All four go through the reader 0x0800FE88(id, archive, 1, dest). Per archive, one cold-boot run: warp to a scene
whose screen calls the reader for that archive once (found by tools/lua/forceview.lua without FV_VALS: FVCALL),
then tools/lua/forceview.lua swaps r0 (the id) on every call whose r1 is that archive's base in this build, and
reloads a state saved just before the call (LOOP) whenever IDLE frames pass, so each reload shows the next id
through the game's own drawing path. $SKILL textcover.lua logs the id-map reads, so
`textcover.py work/qa/forcearc build/goushouden_en.strings.tsv` counts them. --shots: fv_NNNN.png per id.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract  # noqa: E402
import cover_ranges  # noqa: E402
from skill import SKILL  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# archive dir, id prefix, scene, frame just before the scene's call (measured with FVCALL), frames per id
KINDS = {
    "book": ("B", "m1_book", 405, 214),         # FVCALL r0=1 f419 (desc 0x72 f403/f458 too)
    # FVCALL r0=0x72 f403 and f458 (skill line under the profile); m1_status_sk's one call (f515) comes from a
    # scripted SELECT press the state reload doesn't replay, so only the first id took there
    "desc": ("D", "m1_book", 395, 150),         # 2 ids per ~263-frame reload: 120/id ran out at 270/290
    "effect": ("E", "m2_sptn", 625, 214),       # FVCALL r0=1 f633 (partner stock: equipment effect box)
    "place": ("P", "m1_load", 392, 214),        # FVCALL r0=0 f400 (load screen)
}
IDLE, SHOT = 200, 150


def ids_of(kind):
    out = []
    for name in extract.script_files():
        if name.startswith(kind + "/"):
            out += [(e["msg"][0], e["id"]) for e in extract.load(name) if e.get("msg")]
    return out


def base_of(strings, ids):
    """Archive base in this build: the id-map entry of id n is at base + 2 + 2n (build.string_table)."""
    n, sid = ids[0]
    return strings[sid] - 2 - 2 * n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", default=str(ROOT / "build" / "goushouden_en.gba"))
    ap.add_argument("--only", help="comma list of " + ",".join(KINDS))
    ap.add_argument("--shots", action="store_true")
    ap.add_argument("--limit", type=int, help="first N ids only (a test)")
    ap.add_argument("--out", default=str(ROOT / "work" / "qa" / "forcearc"))
    a = ap.parse_args()
    rom = Path(a.rom).resolve()
    stsv = rom.with_suffix(".strings.tsv")
    strings = {}
    for line in stsv.read_text(encoding="utf-8").splitlines():
        sid, addr = line.split("\t")[:2]
        strings[sid] = int(addr, 16)
    ranges = cover_ranges.ranges(stsv)
    bad = 0
    for kind in (a.only.split(",") if a.only else KINDS):
        prefix, scene, frm, per = KINDS[kind]
        ids = ids_of(kind)[:a.limit] if a.limit else ids_of(kind)
        base = base_of(strings, ids)
        d = Path(a.out).resolve() / kind
        d.mkdir(parents=True, exist_ok=True)
        vals = d / "vals.txt"
        vals.write_text("".join("%d %s\n" % i for i in ids))
        cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), str(rom), "--out", str(d),
               "--script", str(ROOT / "tools" / "debug" / "warp.lua"), "--var", "SCENE='%s'" % scene,
               "--script", str(ROOT / "tools" / "lua" / "forceview.lua"), "--var", "FV_ADDR=0x0800FE88",
               "--var", "FV_IF='r1=0x%08X'" % base, "--var", "FV_VALS='%s'" % vals.as_posix(),
               "--var", "FV_FROM=%d" % frm, "--var", "LOOP=1", "--var", "IDLE=%d" % IDLE,
               "--script", str(Path(SKILL) / "scripts" / "lua" / "probes" / "textcover.lua"),
               "--var", "RANGES='%s'" % ranges,
               "--frames", str(frm + 600 + per * len(ids)), "--timeout", str(300 + 2 * len(ids))]
        if a.shots:
            cmd += ["--var", "FV_SHOTS=1", "--var", "FV_SHOT=%d" % SHOT]
        p = subprocess.run(cmd, capture_output=True, text=True)
        log = (d / "log.txt").read_text(encoding="utf-8", errors="replace") if (d / "log.txt").exists() else ""
        got = len(re.findall(r"^FV [0-9A-F]+ ", log, re.M))
        done = "FORCEVIEW_DONE" in log
        bad += not done
        print("%-6s %s base 0x%08X: exit %d, %d/%d ids%s" % (kind, scene, base, p.returncode, got, len(ids),
                                                              "" if done else "  NOT DONE"), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
