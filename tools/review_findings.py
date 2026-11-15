"""Collect reviewer findings from work/qa/review/reports/bNNN.txt (tools/review.sh).

    python -X utf8 tools/review_findings.py [--sev CRITICAL,IMPORTANT] [--batch bNNN] [--tsv OUT]

Prints per-batch counts and assessments, then each finding at the chosen severities as
`batch sev id` / `  JP: gist` / `  problem` / `  now: current EN` / `  sug: suggested EN`.
`--tsv OUT` writes batch, sev, id, gist, problem, current, suggestion (for docs/polish.md or an apply list).
Reports with no ASSESSMENT line are listed as incomplete.
"""
import argparse
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
REP = ROOT / "work" / "qa" / "review" / "reports"
TL = ROOT / "work" / "tl"


def current(batch):
    out = {}
    p = TL / f"{batch}.out.tsv"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "\t" in line:
                k, v = line.split("\t", 1)
                out[k] = v
    return out


def parse(path):
    finds, assess = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = [s.strip() for s in line.split(" | ")]
        if parts[0] in ("CRITICAL", "IMPORTANT", "MINOR") and len(parts) >= 5:
            finds.append((parts[0], parts[1], parts[2], parts[3], " | ".join(parts[4:])))
        elif parts[0] == "ASSESSMENT" and len(parts) >= 3:
            assess = " | ".join(parts[2:])
    return finds, assess


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sev", default="CRITICAL,IMPORTANT")
    ap.add_argument("--batch", action="append")
    ap.add_argument("--tsv")
    ap.add_argument("--quiet", action="store_true", help="counts only")
    ap.add_argument("--rep", default=str(REP), help="reports directory (a later review round)")
    a = ap.parse_args()
    rep = pathlib.Path(a.rep)
    sevs = set(a.sev.split(","))
    rows, incomplete, tot = [], [], {"CRITICAL": 0, "IMPORTANT": 0, "MINOR": 0}
    for p in sorted(rep.glob("b*.txt")):
        b = p.stem
        if a.batch and b not in a.batch:
            continue
        finds, assess = parse(p)
        if assess is None:
            incomplete.append(b)
        cnt = {s: sum(1 for f in finds if f[0] == s) for s in tot}
        for s in tot:
            tot[s] += cnt[s]
        if not a.quiet:
            print(f"{b} C{cnt['CRITICAL']} I{cnt['IMPORTANT']} M{cnt['MINOR']} {assess or '(no assessment)'}"[:150])
        cur = current(b)
        for sev, i, gist, prob, sug in finds:
            if sev in sevs:
                rows.append((b, sev, i, gist, prob, cur.get(i, "?"), sug))
    print(f"total {tot}; incomplete: {' '.join(incomplete) or 'none'}")
    if a.tsv:
        pathlib.Path(a.tsv).write_text(
            "".join("\t".join(c.replace("\t", " ") for c in r) + "\n" for r in rows), encoding="utf-8")
        print(f"{len(rows)} rows -> {a.tsv}")
    elif not a.quiet:
        for b, sev, i, gist, prob, cur, sug in rows:
            print(f"\n{b} {sev[0]} {i}\n  JP: {gist}\n  problem: {prob}\n  now: {cur}\n  sug: {sug}")


if __name__ == "__main__":
    main()
