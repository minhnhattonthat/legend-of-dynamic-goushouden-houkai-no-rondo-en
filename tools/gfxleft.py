"""Flagged graphics blocks (docs/re/graphics_sweep.tsv) that no gfx/*.diff edits yet: the phase-8 to-do list.

    python -X utf8 tools/gfxleft.py [--all]

A block can be done without a diff of its own (pure Latin/digit art, or a screen that never shows it): mark those
in docs/re/graphics.md, not here. --all also prints the blocks that have a diff.
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    done = {int(m.group(1), 16) for p in (ROOT / "gfx").glob("*.diff")
            if (m := re.search(r"_([0-9A-F]{6})\.diff$", p.name))}
    rows = [r for r in csv.reader(open(ROOT / "docs" / "re" / "graphics_sweep.tsv", encoding="utf-8"), delimiter="\t")
            if r and not r[0].startswith("#")]
    left = 0
    for r in rows:
        try:
            off = int(r[0], 16)
        except ValueError:
            off = None
        has = off in done
        left += not has
        if not has or "--all" in sys.argv:
            print(("done " if has else "left ") + "\t".join(r[:4] + r[5:6]))
    print(f"{len(rows)} flagged, {left} without a diff")


if __name__ == "__main__":
    main()
