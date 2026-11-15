"""Reviewer pairs files from the translation batches (references/translation.md §Review).

    python -X utf8 tools/pairs.py [bNNN ...] [--out work/qa/review/pairs]

One file per batch: every entry as `>> id | speaker | JP` then `   EN: ...`, in batch order, with the last 2
entries of the previous batch and the first 2 of the next as context (`   ctx` lines, not to be judged).
Reads work/tl/bNNN.tsv (id, speaker, form, limit, JP) and work/tl/bNNN.out.tsv (id, English).
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TL = ROOT / "work" / "tl"


def load(batch):
    src = []
    for line in (TL / f"{batch}.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        src.append((cols[0], cols[1], cols[-1]))
    en = {}
    out = TL / f"{batch}.out.tsv"
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            if "\t" in line:
                k, v = line.split("\t", 1)
                en[k] = v
    return [(i, spk, jp, en.get(i, "")) for i, spk, jp in src]


def fmt(entry, ctx=False):
    i, spk, jp, en = entry
    jp = jp.replace("\\n", " / ")
    en = en.replace("\\n", " ")
    if ctx:
        return f"   ctx {i} | {spk} | {jp}\n   ctx EN: {en}\n"
    return f">> {i} | {spk} | {jp}\n   EN: {en}\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batches", nargs="*")
    ap.add_argument("--out", default=str(ROOT / "work" / "qa" / "review" / "pairs"))
    a = ap.parse_args()
    allb = sorted(p.name[:-4] for p in TL.glob("b[0-9][0-9][0-9].tsv"))
    want = a.batches or allb
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for b in want:
        if b not in allb:
            sys.exit(f"no batch {b}")
        k = allb.index(b)
        parts = []
        if k > 0:
            parts += [fmt(e, True) for e in load(allb[k - 1])[-2:]]
        parts += [fmt(e) for e in load(b)]
        if k + 1 < len(allb):
            parts += [fmt(e, True) for e in load(allb[k + 1])[:2]]
        (out / f"{b}.txt").write_text("".join(parts), encoding="utf-8")
    print(f"{len(want)} pairs files in {out}")


if __name__ == "__main__":
    main()
