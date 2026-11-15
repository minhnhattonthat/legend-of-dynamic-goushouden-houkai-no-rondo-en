"""long.py: the batch English that `batches.py merge --partial` left out (LONG ids), and why.

  python -X utf8 tools/long.py [--all]    one line per id: batch, id, bytes/room, px/field per box, ptr count, EN

Reads work/tl/bNNN.out.tsv for every batch and lists ids whose English is not in script/ yet (or, with --all,
every ROM string whose shipped English is over a field). Phase 7 uses it to plan relocation and field widening.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import batches  # noqa: E402
import extract  # noqa: E402
import lint  # noqa: E402
import sjis  # noqa: E402


def entries():
    out = {}
    for path in sorted((ROOT / "script").glob("*/*.json")):
        import json
        for e in json.loads(path.read_text(encoding="utf-8")):
            out[e["id"]] = (path.parent.name, e)
    return out


def measure(part, e, en):
    """[(label, have, limit)] for every limit the English goes over."""
    over = []
    if part == "rom":
        off = int(e["id"][1:], 16)
        n = len(sjis.encode(sjis.fullwidth(en) if off in extract.FULLWIDTH else en))
        if n > e["max"]:
            over.append(("bytes", n, e["max"]))
        for box in lint.rom_boxes(e):
            win = lint.WINDOWS[box]
            widths = {"8": lint.char_widths8, "12": lint.char_widths12}.get(win.get("font"), lint.char_widths)()
            px = lint.line_px(en, widths)
            if px > win["px"]:
                over.append((box, px, win["px"]))
    else:
        errs = batches.width_problems(part, e, en.replace("\n", "\\n"))
        over += [("box", m, "") for m in errs]
    return over


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="also shipped ROM strings over a field")
    args = ap.parse_args()
    es = entries()
    seen = set()
    for out in sorted((ROOT / "work" / "tl").glob("b*.out.tsv")):
        for line in out.read_text(encoding="utf-8").splitlines():
            if "\t" not in line:
                continue
            i, en = line.split("\t", 1)
            if i not in es or i in seen:
                continue
            part, e = es[i]
            if e.get("en"):
                continue
            seen.add(i)
            en = batches.final_en(part, e, en)
            over = measure(part, e, en)
            print("%s\t%s\t%s\tptrs=%d\t%r" % (out.name[:4], i, " ".join("%s %s/%s" % o for o in over) or "fits",
                                              len(e.get("ptrs", ())), en))
    if args.all:
        for i, (part, e) in es.items():
            if part == "rom" and e.get("en") and e.get("status") != "data":
                over = measure(part, e, e["en"])
                if over:
                    print("shipped\t%s\t%s\tptrs=%d\t%r" % (i, " ".join("%s %s/%s" % o for o in over),
                                                         len(e.get("ptrs", ())), e["en"]))


if __name__ == "__main__":
    main()
