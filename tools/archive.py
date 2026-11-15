"""archive.py: the script archive at ROM 0x104DC0 (docs/re/text.md §1).

Layout (X = 0x104DC0, all offsets relative to X):
  X+0       u16 count (0x429B), then count x u16: message id -> message number (0xFFFF = none)
  X+0x8538  54 x {u32 offset, u32 unpacked size}: one bare lh5 stream per file, back to back from X+0x86E8
  end       0x132E74 (the next table starts there)
Each unpacked file: 100 x u32 slot offsets (0 = empty slot), then the message bytes in slot order.

  read(rom)                    -> Archive (files = list of File(raw, stream))
  Archive.build()              -> archive bytes; unchanged files keep their original stream (byte-exact identity)
  split_file(raw) / join_file  -> 100 slots (bytes or None) and back
"""
import struct

import lh5

BASE = 0x104DC0
END = 0x132E74
NFILES = 54
NSLOTS = 100
POINTER_SITES = (0x7DDC, 0x80BC, 0x8348, 0x8600, 0x17E8C)  # literal pools holding 0x08104DC0


class File:
    def __init__(self, raw, stream):
        self.orig_raw = raw
        self.raw = raw
        self.stream = stream  # original lh5 stream for orig_raw

    def packed(self):
        if self.raw == self.orig_raw:
            return self.stream
        return lh5.encode(self.raw)


class Archive:
    def __init__(self, idmap, files):
        self.idmap = idmap  # bytes X+0 .. table start, kept as is
        self.files = files

    def build(self):
        head = len(self.idmap) + 8 * len(self.files)
        table = bytearray()
        body = bytearray()
        for f in self.files:
            table += struct.pack("<II", head + len(body), len(f.raw))
            body += f.packed()
        return bytes(self.idmap) + bytes(table) + bytes(body)


def read(rom, base=BASE):
    """base: where the archive sits (BASE in the original, engine.NEW_ARCHIVE in a built ROM)."""
    end = END if base == BASE else len(rom)
    count = struct.unpack_from("<H", rom, base)[0]
    table = base + 2 + 2 * count
    ents = [struct.unpack_from("<II", rom, table + 8 * i) for i in range(NFILES)]
    files = []
    for i, (off, size) in enumerate(ents):
        start = base + off
        stop = base + ents[i + 1][0] if i + 1 < NFILES else end
        raw, used = lh5.decode(rom, start, size)
        last = i + 1 == NFILES  # a rebuilt archive may end before END (zero padding follows)
        if used > stop - start or (used != stop - start and not last):
            raise ValueError("file %d: stream is %d bytes, slot %d" % (i, used, stop - start))
        files.append(File(raw, bytes(rom[start:start + used])))
    return Archive(bytes(rom[base:table]), files)


def split_file(raw):
    """-> list of NSLOTS entries: bytes of that slot (up to the next used slot or the file end) or None if empty."""
    offs = struct.unpack_from("<%dI" % NSLOTS, raw, 0)
    used = sorted((o, j) for j, o in enumerate(offs) if o)
    slots = [None] * NSLOTS
    for k, (o, j) in enumerate(used):
        stop = used[k + 1][0] if k + 1 < len(used) else len(raw)
        slots[j] = bytes(raw[o:stop])
    return slots


def join_file(slots):
    """Inverse of split_file: messages laid out in slot order after the offset table."""
    offs = []
    body = bytearray()
    pos = 4 * NSLOTS
    for s in slots:
        if s is None:
            offs.append(0)
            continue
        offs.append(pos + len(body))
        body += s
    return struct.pack("<%dI" % NSLOTS, *offs) + bytes(body)
