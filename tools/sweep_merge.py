"""sweep_merge.py: union of the codex sweep reviews -> docs/re/graphics_sweep.tsv (one row per flagged block).

Reads every */review*/chunk*.txt under the sweep dirs ("<file> | <label> | <kind> | <note>" lines), keys hits by block
label, keeps every kind/note seen and which passes found it. Rows from --add (label|kind|note) are hits seen by eye.

  python -X utf8 tools/sweep_merge.py [--dirs work/sweep work/sweep_raw] [--add "3086C8 4|jp-text|large kanji"]
"""
import argparse
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="*", default=["work/sweep", "work/sweep_raw"])
    ap.add_argument("--add", action="append", default=[])
    ap.add_argument("--out", default="docs/re/graphics_sweep.tsv")
    a = ap.parse_args()
    hits = {}
    for d in a.dirs:
        for f in sorted(glob.glob(os.path.join(ROOT, d, "review*", "chunk*.txt"))):
            tag = os.path.basename(os.path.dirname(f))
            for line in open(f, encoding="utf-8", errors="replace"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 4 or parts[1].lower() == "none":
                    continue
                label = re.sub(r"\s+", " ", parts[1])
                h = hits.setdefault((d, label), {"kinds": set(), "notes": [], "passes": set()})
                h["kinds"].add(parts[2])
                if parts[3] not in h["notes"]:
                    h["notes"].append(parts[3])
                h["passes"].add(tag)
    for s in a.add:
        label, kind, note = (x.strip() for x in s.split("|"))
        h = hits.setdefault(("by-eye", label), {"kinds": set(), "notes": [], "passes": set()})
        h["kinds"].add(kind)
        h["notes"].append(note)
        h["passes"].add("eye")

    def key(item):
        lab = item[0][1].split()[0]
        m = re.search(r"([0-9A-F]{6})", lab)
        return int(m.group(1), 16) if m else 0

    with open(os.path.join(ROOT, a.out), "w", encoding="utf-8", newline="\n") as o:
        o.write("# block\tfmt\tcodec\tkind\tfound by\tnote  (tools/sweep_merge.py; block = ROM offset of the packed "
                "block, or raw_ range start)\n")
        for (d, label), h in sorted(hits.items(), key=key):
            name, fmt = (label.split() + ["?"])[:2]
            codec = "t1" if name.startswith("t1_") else "t3" if name.startswith("t3_") else (
                "raw" if "raw" in d else "lh5")
            off = name.split("_")[-1]
            o.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (off, fmt, codec, "/".join(sorted(h["kinds"])),
                                                  ",".join(sorted(h["passes"])), "; ".join(h["notes"])))
    print("%d flagged blocks -> %s" % (len(hits), a.out))


if __name__ == "__main__":
    main()
