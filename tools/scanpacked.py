"""scanpacked.py: find every packed block in the ROM (types 1, 2, 3; docs/re/compression.md) -> work/packed_blocks.json.

A candidate is a 4-aligned header `type << 24 | size` (16 <= size <= 0x40000) that decodes without error
(type 1 also needs its `bits` word <= 4 and an even size). Candidates are ranked (seen in an unpack log first,
then type 1, lh5, type 3; then lower byte entropy of the output) and accepted greedily when they don't overlap an
accepted block. Rejected candidates are counted by reason, never dropped silently.

  python -X utf8 tools/scanpacked.py [--logs work/qa/*/log.txt]
Output rows: [offset, type, unpacked_size, packed_len, entropy, seen_in_log]
"""
import argparse
import glob
import json
import math
import os
import re
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import packed  # noqa: E402


def entropy(b):
    if not b:
        return 8.0
    c = Counter(b)
    n = len(b)
    return -sum(v / n * math.log2(v / n) for v in c.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", nargs="*", default=None)
    ap.add_argument("--max-entropy", type=float, default=7.2)
    a = ap.parse_args()
    rom = open(packed.ROM, "rb").read()
    logs = a.logs if a.logs is not None else glob.glob(os.path.join(packed.ROOT, "work", "qa", "*", "log.txt"))
    seen = set()
    for f in logs:
        for line in open(f, encoding="utf-8", errors="replace"):
            m = re.search(r"unpack src=(\w+)", line)
            if m and int(m.group(1), 16) >> 24 == 8:
                seen.add(int(m.group(1), 16) & 0x1FFFFFF)
    why = Counter()
    cands = []
    for off in range(0, len(rom) - 8, 4):
        hdr = struct.unpack_from("<I", rom, off)[0]
        typ, size = hdr >> 24, hdr & 0xFFFFFF
        if typ not in (1, 2, 3) or not 16 <= size <= 0x40000:
            continue
        if typ == 1:
            bits = struct.unpack_from("<I", rom, off + 4)[0]
            if bits > 4 or size & 1:
                why["t1 bad bits/odd size"] += 1
                continue
        try:
            _, out, used = packed.unpack(rom, off)
        except Exception as e:  # noqa: BLE001  (lh5 raises its own errors)
            why["t%d decode error" % typ] += 1
            continue
        if len(out) != size:
            why["t%d short" % typ] += 1
            continue
        h = entropy(out)
        if h > a.max_entropy and off not in seen:
            why["t%d noisy output" % typ] += 1
            continue
        cands.append((off, typ, size, used, round(h, 3), off in seen))
    rank = {1: 0, 2: 1, 3: 2}
    cands.sort(key=lambda c: (not c[5], rank[c[1]], c[4]))
    taken = bytearray(len(rom))
    acc = []
    for c in cands:
        off, used = c[0], c[3]
        if any(taken[off:off + used]):
            why["t%d overlaps a better block" % c[1]] += 1
            continue
        taken[off:off + used] = b"\x01" * used
        acc.append(c)
    acc.sort()
    out = os.path.join(packed.ROOT, "work", "packed_blocks.json")
    json.dump(acc, open(out, "w"))
    byt = Counter()
    for c in acc:
        byt[c[1]] += 1
    print("accepted %d blocks %s, %d logged sources (%d found)" % (
        len(acc), dict(byt), len(seen), sum(1 for c in acc if c[5])))
    print("covered %d bytes of ROM" % sum(c[3] for c in acc))
    for k, v in sorted(why.items()):
        print("  rejected %-28s %d" % (k, v))
    missing = sorted(seen - {c[0] for c in acc})
    if missing:
        print("logged but not accepted:", " ".join("%06X" % m for m in missing))


if __name__ == "__main__":
    main()
