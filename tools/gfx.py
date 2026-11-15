"""Edited packed graphics blocks (phase 8). gfx/<name>_<OFFSET>.diff holds only the changed bytes of the unpacked
block (`OFFSET HEXBYTES` per line, block-relative; the repo carries no game art), written by a per-screen generator
(tools/gfx_title.py ...). The build applies it to the ROM's own block and repacks it as type 2 (lh5) in place at
OFFSET: the game's unpack() dispatches on the header, so any original codec can become lh5 (verified in game on the
title, docs/re/graphics.md G1). The new stream must fit the original block's packed size; bytes after it stay as
they were (never read).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import lh5  # noqa: E402
import packed  # noqa: E402

DIR = ROOT / "gfx"


def make_diff(old, new):
    """Text diff of two equal-length byte strings: one line per run of changed bytes."""
    assert len(old) == len(new)
    lines, i = [], 0
    while i < len(new):
        if old[i] == new[i]:
            i += 1
            continue
        j = i
        while j < len(new) and (old[j] != new[j] or (j + 1 < len(new) and old[j + 1] != new[j + 1])):
            j += 1
        lines.append("%05X %s" % (i, new[i:j].hex().upper()))
        i = j
    return "\n".join(lines) + "\n"


def apply_diff(raw, text):
    out = bytearray(raw)
    for line in text.splitlines():
        if line.strip():
            off, data = line.split()
            b = bytes.fromhex(data)
            o = int(off, 16)
            if o + len(b) > len(out):
                raise SystemExit("gfx diff writes past the block end at %X" % o)
            out[o:o + len(b)] = b
    return bytes(out)


def blocks():
    """[(offset, path)] for every edited block."""
    out = []
    for p in sorted(DIR.glob("*.diff")):
        m = re.search(r"_([0-9A-F]{6})\.diff$", p.name)
        if m:
            out.append((int(m.group(1), 16), p))
    return out


def ranges(orig):
    """Allowed write ranges: each edited block's original packed slot."""
    return [(off, off + packed.unpack(orig, off)[2]) for off, _ in blocks()]


def insert(orig, put):
    for off, path in blocks():
        _, raw, size = packed.unpack(orig, off)
        new = apply_diff(raw, path.read_text())
        if new == raw:
            continue
        data = lh5.pack(new)
        if len(data) > size:
            raise SystemExit("%s: repacked %d bytes > slot %d at %06X (relocate: not done yet)"
                             % (path.name, len(data), size, off))
        put(off, data, "gfx %s" % path.stem)
