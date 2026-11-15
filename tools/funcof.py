"""funcof.py: the Thumb function that holds a literal pool word, and the BL sites that call it (recon helper).

  python -X utf8 tools/funcof.py ROM OFFSET..     OFFSET = file offset of a literal pool word (hex)

The function start is the nearest `push {..., lr}` (0xB5xx) before the first instruction that loads the word
(ldr rX, [pc, #imm]); callers are every BL in the ROM's code area whose target is that start.
"""
import struct
import sys


def loaders(rom, pool):
    """Thumb `ldr rX, [pc, #imm]` instructions (up to 1 KiB before) that load the word at `pool`."""
    out = []
    for at in range(max(0, pool - 1024), pool, 2):
        h = struct.unpack_from("<H", rom, at)[0]
        if h & 0xF800 == 0x4800 and ((at + 4) & ~3) + (h & 0xFF) * 4 == pool:
            out.append(at)
    return out


def func_start(rom, at):
    for p in range(at, max(0, at - 0x2000), -2):
        h = struct.unpack_from("<H", rom, p)[0]
        if h & 0xFF00 == 0xB500:
            return p
    return None


def bl_callers(rom, target, code_end=0x100000):
    out = []
    for p in range(0, min(len(rom), code_end) - 4, 2):
        hi, lo = struct.unpack_from("<HH", rom, p)
        if hi & 0xF800 == 0xF000 and lo & 0xF800 == 0xF800:
            off = ((hi & 0x7FF) << 12 | (lo & 0x7FF) << 1)
            if off & 0x400000:
                off -= 0x800000
            if p + 4 + off == target:
                out.append(p)
    return out


def main():
    rom = open(sys.argv[1], "rb").read()
    for a in sys.argv[2:]:
        pool = int(a, 16)
        lds = loaders(rom, pool)
        starts = sorted({func_start(rom, x) for x in lds} - {None})
        for s in starts:
            calls = bl_callers(rom, s)
            print("pool %06X loaded at %s  func %06X  called from %s" % (
                pool, " ".join("%06X" % x for x in lds), s, " ".join("%06X" % c for c in calls) or "-"))


if __name__ == "__main__":
    main()
