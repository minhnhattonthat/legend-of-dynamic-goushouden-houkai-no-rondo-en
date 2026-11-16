"""coverage.py: text coverage over the current build's QA log dirs, grouped by kind (phase 8 summary).

    python -X utf8 tools/coverage.py [--dirs work/qa/tour_en3,work/qa/msgview,work/qa/forcearc,work/qa/forcestr] [--list KIND]
                                     [--missing-out F]

Reads every log.txt under the given dirs ("TEXT <hex>" lines from textcover.lua), maps them onto
build/goushouden_en.strings.tsv, drops docs/text_unshown.tsv waivers, and prints shown / waived / missing per kind:
dialogue (FF.SS), archives B/D/E/P, and ROM strings by 0x1000 page (rXXXXXX). --list KIND prints the missing ids of
one kind (a kind name as printed). The gate itself stays $SKILL/scripts/textcover.py on one LOGDIR.
"""
import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIRS = "work/qa/tour_en3,work/qa/msgview,work/qa/forcearc,work/qa/forcestr"


def kind(sid):
    if re.match(r"^\d\d\.", sid):
        return "dialogue"
    if sid[0] in "BDEP" and re.match(r"^[BDEP]\d", sid):
        return "arc_" + sid[0]
    if sid.startswith("r"):
        return "rom_" + sid[1:5]
    return "other_" + sid[:2]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dirs", default=DEFAULT_DIRS)
    ap.add_argument("--strings", default=str(ROOT / "build" / "goushouden_en.strings.tsv"))
    ap.add_argument("--waive", default=str(ROOT / "docs" / "text_unshown.tsv"))
    ap.add_argument("--list")
    ap.add_argument("--missing-out")
    a = ap.parse_args()
    seen = set()
    for d in a.dirs.split(","):
        p = ROOT / d
        if not p.exists():
            print(f"(no {d})", file=sys.stderr)
            continue
        for log in p.rglob("log.txt"):
            for m in re.finditer(r"^TEXT ([0-9A-Fa-f]+)", log.read_text(encoding="utf-8", errors="replace"), re.M):
                seen.add(int(m.group(1), 16))
    waived = set()
    for line in Path(a.waive).read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            parts = line.split("\t")
            if len(parts) > 1 and parts[1].strip():
                waived.add(parts[0])
    stats = defaultdict(Counter)
    missing = []
    for line in Path(a.strings).read_text(encoding="utf-8").splitlines():
        sid, addr = line.split("\t")[:2]
        k = kind(sid)
        if int(addr, 16) in seen:
            stats[k]["shown"] += 1
        elif sid in waived:
            stats[k]["waived"] += 1
        else:
            stats[k]["missing"] += 1
            missing.append((k, sid))
    if a.list:
        for k, sid in missing:
            if k == a.list:
                print(sid)
        return
    tot = Counter()
    for k in sorted(stats):
        c = stats[k]
        tot.update(c)
        if c["missing"]:
            print(f"{k:12} shown {c['shown']:5}  waived {c['waived']:4}  missing {c['missing']:5}")
    print(f"{'TOTAL':12} shown {tot['shown']:5}  waived {tot['waived']:4}  missing {tot['missing']:5}")
    if a.missing_out:
        Path(a.missing_out).write_text("".join(f"{s}\t{k}\n" for k, s in missing), encoding="utf-8")


if __name__ == "__main__":
    main()
