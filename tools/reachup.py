"""reachup.py: who can reach a ROM string, walking references up to their root functions (text-coverage waivers).

  python -X utf8 tools/reachup.py [--rom ROM] ID..       ids from script/rom/*.json (r0D3024), or `--all-missing F`

For each pointer to the string (`ptrs` in its json entry): a pointer word inside code is a literal pool -> the function
that loads it; a pointer inside a data table -> the code that loads the table's base (the nearest literal-pool word
pointing at or up to 0x800 bytes before it). Then up the call graph: BL callers, plus any literal-pool word holding
the function's address (function pointers, jump tables: their table base is followed the same way). Prints the root
functions (nothing calls or points at them). A string whose every root is a debug-menu entry (docs/re/debug.md:
DEBUG_ROOTS) is debug-only. Static and conservative: a root outside DEBUG_ROOTS is reported as `retail?`.
"""
import argparse
import glob
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from funcof import func_start, loaders  # noqa: E402

CODE_END = 0x104DC0
# debug top menu 0x0807E370 (no callers) and its jump table 0x0807E3EC targets other than 製品版 (retail loop)
DEBUG_ROOTS = {0x07E370, 0x080260, 0x07FCE8, 0x0166A0, 0x08F758, 0x0C4430, 0x07E49C, 0x009534}


def load_rom(path):
    return open(path, "rb").read()


class Graph:
    def __init__(self, rom):
        self.rom = rom
        self.bl = {}
        for p in range(0, CODE_END - 4, 2):
            hi, lo = struct.unpack_from("<HH", rom, p)
            if hi & 0xF800 == 0xF000 and lo & 0xF800 == 0xF800:
                off = ((hi & 0x7FF) << 12 | (lo & 0x7FF) << 1)
                if off & 0x400000:
                    off -= 0x800000
                self.bl.setdefault(p + 4 + off, []).append(p)
        self.words = {}
        for p in range(0, CODE_END, 4):
            w = struct.unpack_from("<I", rom, p)[0]
            if 0x08000000 <= w < 0x08000000 + CODE_END:
                self.words.setdefault((w & ~1) - 0x08000000, []).append(p)

    def holders(self, loc):
        """Functions that use the word at `loc`: as a literal pool, else via the base of the table holding it."""
        lds = loaders(self.rom, loc)
        if lds:
            return {func_start(self.rom, x) for x in lds} - {None}
        for base in range(loc, max(0, loc - 0x800), -4):
            out = set()
            for ref in self.words.get(base, []):
                out |= {func_start(self.rom, x) for x in loaders(self.rom, ref)} - {None}
            if out:
                return out
        return set()

    def up(self, func):
        """Callers of func: BL sites, and functions holding a pointer to it."""
        out = {func_start(self.rom, c) for c in self.bl.get(func, [])} - {None, func}
        for ref in self.words.get(func, []):
            out |= self.holders(ref) - {func}
        return out

    def roots(self, loc, cap=400):
        seen, todo, roots = set(), list(self.holders(loc)), set()
        if not todo:
            return {None}
        while todo and len(seen) < cap:
            f = todo.pop()
            if f in seen:
                continue
            seen.add(f)
            if f in DEBUG_ROOTS:
                roots.add(f)
                continue
            ups = self.up(f)
            if not ups:
                roots.add(f)
            todo += list(ups)
        if todo:
            roots.add("cap")
        return roots


def entries():
    out = {}
    for f in glob.glob(str(ROOT / "script" / "rom" / "0*.json")):
        for e in json.load(open(f, encoding="utf-8")):
            out[e["id"]] = e
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--rom", default=str(next((ROOT / "rom").glob("*.gba"))))
    ap.add_argument("--all-missing", help="file with one id per line (textcover's NEVER SHOWN ids)")
    a = ap.parse_args()
    ids = list(a.ids)
    if a.all_missing:
        ids += [x.strip() for x in open(a.all_missing, encoding="utf-8") if x.strip().startswith("r")]
    g = Graph(load_rom(a.rom))
    ents = entries()
    for i in ids:
        e = ents[i]
        roots = set()
        for p in e["ptrs"]:
            roots |= g.roots(int(p, 16))
        kind = "debug" if roots and all(r in DEBUG_ROOTS for r in roots) else "retail?"
        names = " ".join("-" if r is None else r if isinstance(r, str) else "%06X" % r
                         for r in sorted(roots, key=str))
        print("%s\t%s\t%s\t%s" % (i, kind, names, e["en"][:40].replace("\n", " ")))


if __name__ == "__main__":
    main()
