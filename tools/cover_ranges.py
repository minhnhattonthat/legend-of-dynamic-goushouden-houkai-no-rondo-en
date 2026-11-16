"""cover_ranges.py: the RANGES value for textcover.lua from a build's strings.tsv (text coverage, phase 8).

    python -X utf8 tools/cover_ranges.py [build/goushouden_en.strings.tsv] [--gap 0x400]

Addresses closer than --gap merge into one range, so a read callback covers a few big spans instead of thousands
of strings. Prints lo-hi,lo-hi,... (hex, GBA addresses).
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ranges(path, gap=0x400):
    addrs = sorted({int(line.split("\t")[1], 16) for line in Path(path).read_text(encoding="utf-8").splitlines() if line})
    out = []
    for a in addrs:
        if out and a - out[-1][1] <= gap:
            out[-1][1] = a
        else:
            out.append([a, a])
    return ",".join("%X-%X" % (lo, hi + 1) for lo, hi in out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("strings", nargs="?", default=str(ROOT / "build" / "goushouden_en.strings.tsv"))
    ap.add_argument("--gap", type=lambda s: int(s, 0), default=0x400)
    a = ap.parse_args()
    print(ranges(a.strings, a.gap))


if __name__ == "__main__":
    main()
