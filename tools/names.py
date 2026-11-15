"""names.py: work/tl/names.tsv, every translated short ROM / place string (names of characters, enemies, skills,
items, maps, places) as JP<TAB>EN, for dialogue translators to look names up (docs/translator-brief.md).

    python -X utf8 tools/names.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    seen = {}
    for path in sorted((ROOT / "script").glob("*/*.json")):
        if path.parent.name not in ("rom", "place"):
            continue
        for e in json.loads(path.read_text(encoding="utf-8")):
            jp, en = e.get("jp", "").strip(), e.get("en", "").strip()
            if jp and en and e.get("status") != "data" and "\n" not in jp and len(jp) <= 16:
                seen.setdefault(jp, en)
    out = ROOT / "work/tl/names.tsv"
    out.write_text("".join(f"{j}\t{e}\n" for j, e in sorted(seen.items())), encoding="utf-8", newline="\n")
    print(f"{len(seen)} names -> {out}")


if __name__ == "__main__":
    main()
