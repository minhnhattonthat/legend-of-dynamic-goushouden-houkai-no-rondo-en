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
    """{offset: [path, ..]} for every edited block (several screens may edit one block: tools/gfxlabel.py)."""
    out = {}
    for p in sorted(DIR.glob("*.diff")):
        m = re.search(r"_([0-9A-F]{6})\.diff$", p.name)
        if m:
            out.setdefault(int(m.group(1), 16), []).append(p)
    return out


# Sprite/cell archives (docs/re/compression.md §Where blocks live): loader 0x080010A8 reads record
# R = A + u32[A + u32[A + 8] + 4*i]; R holds a 32-byte header, then the packed block (src = R + 0x20).
ARCHIVES = [0x2F459C]


def site(orig, off):
    """The u32 table entry that reaches the block at off (record = off - 0x20), or None."""
    import struct
    for a in ARCHIVES:
        t = a + struct.unpack_from("<I", orig, a + 8)[0]
        for i in range(4096):
            p = t + 4 * i
            if p + 4 > len(orig):
                break
            if a + struct.unpack_from("<I", orig, p)[0] == off - 0x20:
                return a, p
    return None


def packs(orig):
    """{offset: (new lh5 stream, slot size)} for every edited block that changed."""
    out = {}
    for off, paths in sorted(blocks().items()):
        _, raw, size = packed.unpack(orig, off)
        new = merged(raw, paths)
        if new != raw:
            out[off] = (lh5.pack(new, small=True), size)
    return out


def ranges(orig):
    """Allowed write ranges: each edited block's original packed slot, and the table entry of a relocated one."""
    out = [(off, off + packed.unpack(orig, off)[2]) for off in sorted(blocks())]
    for off, (data, size) in packs(orig).items():
        if len(data) > size and site(orig, off):
            p = site(orig, off)[1]
            out.append((p, p + 4))
    return out


def merged(raw, paths):
    """Apply every diff of one block; two diffs writing one byte two ways is an error."""
    out, owner = bytearray(raw), {}
    for p in paths:
        new = apply_diff(raw, p.read_text())
        for i in range(len(raw)):
            if new[i] != raw[i]:
                if i in owner and out[i] != new[i]:
                    raise SystemExit("gfx: %s and %s write byte %X of the block two ways" % (owner[i], p.name, i))
                out[i], owner[i] = new[i], p.name
    return bytes(out)


def insert(orig, put, cur=None):
    """Repack every edited block in place; one that grew moves (with its 32-byte record header) to cur, and its
    archive table entry is rewritten. Returns the new free-space cursor."""
    import struct
    for off, (data, size) in packs(orig).items():
        if len(data) <= size:
            put(off, data, "gfx %06X" % off)
            continue
        hit = site(orig, off)
        if hit is None or cur is None:
            raise SystemExit("gfx %06X: repacked %d bytes > slot %d and no archive entry reaches it (add its "
                             "archive to gfx.ARCHIVES: tools/lua/unpackwho.lua)" % (off, len(data), size))
        a, p = hit
        cur = (cur + 3) & ~3
        put(cur, orig[off - 0x20:off] + data, "gfx %06X relocated" % off)
        put(p, struct.pack("<I", cur - a), "gfx %06X table entry" % off)
        cur += 0x20 + len(data)
    return cur
