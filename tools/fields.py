"""fields.py: which screen field each marker string was drawn in (phase 5 width gate).

  python -X utf8 tools/fields.py [DIR]          DIR = a warp_all run with tools/lua/fieldprobe.lua (work/qa/fields)
  python -X utf8 tools/fields.py DIR --groups   one line per (scene, window, x, font): the ids drawn there

Reads FIELD lines from DIR/<scene>/log.txt. On the marker build every ROM string starts with its offset
(`D0000:abc`) and every archive message with its id (`E00.12 The quick`), so each drawn string maps to an id.
Prints id, scene, window, pen x / y, font mode, cell width, and the x of the next string the same window drew on
the same row (the field's right-hand neighbour, if any).
"""
import argparse
import collections
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINE = re.compile(r"FIELD f(\d+) w=(\w+) src=(\w+) lr=(\w+) x=(-?\d+) y=(-?\d+) ec=\S+ ee=\S+ m=(\d+) cw=(\d+) "
                  r"end=\S+ s=(.*)$")
MID = re.compile(r"^(?:\\[0-9A-F]{2})*([0-9A-F]{5}):|^(?:\\[0-9A-F]{2})*([BDEPT][0-9A-F]{2}\.[0-9]{2})")


# Record tables holding pointers to script/rom strings (ROM offsets of the pointer words): name, first site, last
# site, record stride, field offset in the record. A string belongs to every table one of its `ptrs` falls in.
TABLES = (
    ("char_name", 0x7B31C8, 0x7BB9BC, 0xF0, 0x0),    # battler / partner full name (デビルマン, 如月ハニー)
    ("char_short", 0x7B31C8, 0x7BB9BC, 0xF0, 0x4),   # short name (ハニー, トマホーク・Ｐ)
    ("skill_name", 0x7BC7C4, 0x7C159C, 0x44, 0x0),   # skill name (シザーアタック, ヒール)
    ("skill_name2", 0x7BC7C4, 0x7C159C, 0x44, 0x4),  # skill name, second copy
    ("rec18", 0x7C1F00, 0x7C78B4, 0x18, None),       # 0x18-byte records: items, equipment, misc names
    ("item_desc_rom", 0x7DBF10, 0x7DC0B8, 0x4, 0x0), # item descriptions (ROM copy)
    ("enemy_name", 0x7DF910, 0x7E54B4, 0x5C, 0x0),   # enemy names (パンサー団員)
    ("map_name", 0x0FA814, 0x0FACF0, 0x4, 0x0),      # map names (日本マップ, 飛鳥邸・外): debug warp list
)


def category(e):
    """The record tables a script/rom entry is pointed from (empty: code literal pools / small tables)."""
    out = []
    for p in e.get("ptrs", ()):
        a = int(p, 16)
        for name, lo, hi, stride, off in TABLES:
            if lo <= a <= hi + 3 and (off is None or (a - lo) % stride == off):
                out.append(name)
    return sorted(set(out))


def rom_entries():
    import json
    es = {}
    for f in sorted((ROOT / "script" / "rom").glob("0*.json")):
        for e in json.loads(f.read_text(encoding="utf-8")):
            es[e["id"]] = e
    return es


def rows(d):
    for log in sorted(Path(d).glob("*/log.txt")):
        scene = log.parent.name
        for ln in log.read_text(encoding="utf-8", errors="replace").splitlines():
            m = LINE.search(ln)
            if not m:
                continue
            f, w, src, lr, x, y, mode, cw, s = m.groups()
            k = MID.match(s)
            mid = ("r0" + k.group(1)) if k and k.group(1) else (k.group(2) if k else None)
            yield dict(scene=scene, f=int(f), w=w, src=src, lr=lr, x=int(x), y=int(y), m=int(mode), cw=int(cw),
                       s=s, id=mid)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir", nargs="?", default=str(ROOT / "work" / "qa" / "fields"))
    ap.add_argument("--groups", action="store_true")
    a = ap.parse_args()
    rs = list(rows(a.dir))
    byrow = collections.defaultdict(list)
    for r in rs:
        byrow[(r["scene"], r["w"], r["y"])].append(r["x"])
    es = rom_entries()
    cat = lambda i: ("/".join(category(es[i])) or "pool") if i in es else ""  # noqa: E731
    if a.groups:
        g = collections.defaultdict(list)
        for r in rs:
            g[(r["scene"], r["w"], r["x"], r["m"], r["cw"], r["lr"])].append(r["id"] or r["s"][:12])
        for (scene, w, x, m, cw, lr), ids in sorted(g.items()):
            cats = sorted({cat(i) for i in ids if i})
            print("%-14s w=%s x=%-4d m=%d cw=%-2d lr=%s n=%-3d [%s] %s" % (
                scene, w, x, m, cw, lr, len(ids), ",".join(cats), " ".join(sorted(set(ids)))[:120]))
        return
    for r in rs:
        nxt = sorted(x for x in byrow[(r["scene"], r["w"], r["y"])] if x > r["x"])
        print("%-8s %-14s w=%s x=%-4d y=%-4d m=%d cw=%-2d next=%-4s %s" % (
            r["id"] or "-", r["scene"], r["w"], r["x"], r["y"], r["m"], r["cw"], nxt[0] if nxt else "-", r["s"][:40]))


if __name__ == "__main__":
    main()
