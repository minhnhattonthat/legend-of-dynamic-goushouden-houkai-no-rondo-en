"""test_packed.py: check tools/packed.py against blocks the game itself decoded (dumped by tools/lua/unpacklog.lua).

  python -X utf8 tools/test_packed.py [DUMPDIR ...]     (default: work/qa/*/dumps)
Prints ok/mismatch per type; exit 1 on any mismatch or decode error. Skips (exit 0) when no dumps exist.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import packed  # noqa: E402


def main():
    dirs = sys.argv[1:] or glob.glob(os.path.join(packed.ROOT, "work", "qa", "*", "dumps"))
    files = sorted(p for d in dirs for p in glob.glob(os.path.join(d, "*.bin")))
    if not files or not os.path.exists(packed.ROM):
        print("no dumps or no ROM: skipped")
        return 0
    rom = open(packed.ROM, "rb").read()
    stats = {}
    bad = 0
    for p in files:
        b = os.path.basename(p)
        src = int(b[:8], 16) & 0x1FFFFFF
        ref = open(p, "rb").read()
        typ = int(b.split("_")[1].split(".")[0])
        try:
            _, out, _ = packed.unpack(rom, src)
            good = out == ref
            if not good:
                i = next((k for k in range(min(len(out), len(ref))) if out[k] != ref[k]), min(len(out), len(ref)))
                print("MISMATCH %s at %X (%d vs %d bytes)" % (b, i, len(out), len(ref)))
        except packed.DecodeError as e:
            good = False
            print("ERROR %s %s" % (b, e))
        s = stats.setdefault(typ, [0, 0])
        s[0 if good else 1] += 1
        bad += not good
    for t, (ok, ng) in sorted(stats.items()):
        print("type %d: %d ok, %d bad" % (t, ok, ng))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
