"""Apply hand-written review fixes to the batch outputs, one whole entry per line (no pattern rewrites).

    python -X utf8 tools/apply_fixes.py FIXES.tsv [--dry]

FIXES.tsv: `id<TAB>new English` (line breaks as the two characters \\n, like work/tl/bNNN.out.tsv); `#` lines are
comments. Each id must exist in exactly one work/tl/bNNN.out.tsv; the entry's text is replaced as written.
Prints the batches touched, to re-merge with `tools/batches.py merge bNNN ... --overwrite`.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TL = ROOT / "work" / "tl"


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        sys.exit(__doc__)
    dry = "--dry" in args
    fixes = {}
    for line in pathlib.Path(args[0]).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        k, v = line.split("\t", 1)
        if k in fixes:
            sys.exit(f"{k} twice in fixes")
        fixes[k] = v
    where = {}
    files = {}
    for p in sorted(TL.glob("b[0-9][0-9][0-9].out.tsv")):
        lines = p.read_text(encoding="utf-8").split("\n")
        files[p] = lines
        for n, line in enumerate(lines):
            k = line.split("\t", 1)[0]
            if k in fixes:
                if k in where:
                    sys.exit(f"{k} in two batches")
                where[k] = (p, n)
    missing = [k for k in fixes if k not in where]
    if missing:
        sys.exit(f"ids not found: {' '.join(missing)}")
    touched = set()
    changed = 0
    for k, (p, n) in where.items():
        new = f"{k}\t{fixes[k]}"
        if files[p][n] != new:
            files[p][n] = new
            touched.add(p)
            changed += 1
    if not dry:
        for p in touched:
            p.write_text("\n".join(files[p]), encoding="utf-8", newline="\n")
    print(f"{changed} entries changed in {len(touched)} batches{' (dry run)' if dry else ''}")
    print(" ".join(sorted(p.name.split(".")[0] for p in touched)))


if __name__ == "__main__":
    main()
