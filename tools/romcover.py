"""romcover.py: which parts of the ROM are accounted for by known lh5 blocks, and what the gaps look like.

Recon helper for the static graphics sweep (docs/re/graphics.md). Reads work/packed_blocks.json
(tools/scanpacked.py) and prints the uncovered regions of 4 KiB or more with
a rough content class (zero/ff fill, sjis text, thumb code, other).

  python -X utf8 tools/romcover.py [--min 4096]
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM = os.path.join(ROOT, "rom", "Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba")


def classify(b):
    if not b:
        return "empty"
    z = b.count(0) / len(b)
    f = b.count(0xFF) / len(b)
    if z > 0.9:
        return "zero"
    if f > 0.9:
        return "ff"
    sj = 0
    i = 0
    while i < len(b) - 1:
        c = b[i]
        if (0x81 <= c <= 0x9F or 0xE0 <= c <= 0xEF) and 0x40 <= b[i + 1] <= 0xFC:
            sj += 2
            i += 2
        else:
            i += 1
    if sj / len(b) > 0.4:
        return "sjis"
    # thumb code: many halfwords with top bits of push/pop/bl/ldr patterns
    hw = [b[k] | b[k + 1] << 8 for k in range(0, len(b) - 1, 2)]
    thumb = sum(1 for h in hw if (h >> 11) in (0x1E, 0x1F, 0x09, 0x0D, 0x0C, 0x01, 0x00, 0x04, 0x1C) or (h >> 8) in (0xB5, 0xBD, 0x47))
    if thumb / max(1, len(hw)) > 0.6:
        return "thumb?"
    return "other z=%.2f" % z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=lambda s: int(s, 0), default=4096)
    a = ap.parse_args()
    rom = open(ROM, "rb").read()
    blocks = json.load(open(os.path.join(ROOT, "work", "packed_blocks.json")))  # tools/scanpacked.py
    cov = bytearray(len(rom))
    for row in blocks:
        o, used = row[0], row[3]
        cov[o:o + used] = b"\x01" * min(used, len(rom) - o)
    # script archive (docs/re/text.md)
    cov[0x104DC0:0x132E74] = b"\x01" * (0x132E74 - 0x104DC0)
    total = sum(cov)
    print("covered %d / %d bytes (%.1f%%)" % (total, len(rom), 100 * total / len(rom)))
    i = 0
    while i < len(rom):
        if cov[i]:
            i += 1
            continue
        j = i
        while j < len(rom) and not cov[j]:
            j += 1
        if j - i >= a.min:
            # split long gaps into 64 KiB chunks for classification
            k = i
            while k < j:
                e = min(j, k + 0x10000)
                print("%06X-%06X %6X %s" % (k, e, e - k, classify(rom[k:e])))
                k = e
        i = j


if __name__ == "__main__":
    main()
