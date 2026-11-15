"""findtables.py: find self-relative offset tables that reach given ROM offsets (recon, docs/re/compression.md).

The asset loaders compute src = B + u32[B + STRIDE * i] (e.g. 0x0801BA6A: base [r4+0x48], stride 8). Given known
packed-block offsets (from tools/lua/unpacklog.lua logs), list table bases B that reach several of them.

  python -X utf8 tools/findtables.py LOG.txt.. [--stride 8] [--span 0x8000]
"""
import argparse
import collections
import os
import re

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM = os.path.join(ROOT, "rom", "Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--stride", type=lambda s: int(s, 0), default=8)
    ap.add_argument("--span", type=lambda s: int(s, 0), default=0x8000)
    ap.add_argument("--top", type=int, default=40)
    a = ap.parse_args()
    rom = open(ROM, "rb").read()
    srcs = set()
    for f in a.logs:
        for line in open(f, encoding="utf-8", errors="replace"):
            m = re.search(r"unpack src=(\w+)", line)
            if m:
                s = int(m.group(1), 16)
                if 0x08000000 <= s < 0x08000000 + len(rom):
                    srcs.add(s - 0x08000000)
    w = np.frombuffer(rom, dtype="<u4").astype(np.int64)
    q = np.arange(len(w), dtype=np.int64) * 4
    v = q + w  # entry at q with value w reaches B + w where B = q - STRIDE*i; v - src = q - B
    order = np.argsort(v)
    vs = v[order]
    per = collections.defaultdict(set)
    for s in sorted(srcs):
        lo, hi = np.searchsorted(vs, s), np.searchsorted(vs, s + a.span)
        for k in order[lo:hi]:
            d = int(v[k]) - s
            if d % a.stride or w[k] == 0:
                continue
            b = int(q[k]) - d
            if b >= 0 and b % 4 == 0:
                per[b].add(s)
    best = sorted(per.items(), key=lambda kv: -len(kv[1]))[:a.top]
    print("%d logged sources" % len(srcs))
    for b, ss in best:
        if len(ss) < 2:
            break
        print("base %06X reaches %3d  e.g. %s" % (b, len(ss), " ".join("%06X" % x for x in sorted(ss)[:4])))


if __name__ == "__main__":
    main()
