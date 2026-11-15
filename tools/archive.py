"""archive.py: the script archive at ROM 0x104DC0 and the five archives after it (docs/re/text.md §1, §1b).

Layout (X = base, all offsets relative to X; the script archive's numbers shown):
  X+0       u16 count (0x429B), then count x u16: message id -> message number (0xFFFF = none)
  X+0x8538  54 x {u32 offset, u32 unpacked size}: one bare lh5 stream per file, back to back from X+0x86E8
  end       0x132E74 (the next archive starts there)
Each unpacked file: 100 x u32 slot offsets (0 = empty slot), then the message bytes in slot order.
The file count is not stored: it is (first file offset - table offset) / 8.

  ARCHIVES                     one Spec per archive: name, base, slot end, pointer sites, script/ dir, id prefix
  read(rom, base=BASE)         -> Archive (files = list of File(raw, stream))
  Archive.build()              -> archive bytes; unchanged files keep their original stream (byte-exact identity)
  split_file(raw) / join_file  -> 100 slots (bytes or None) and back
"""
import struct
from collections import namedtuple

import lh5

BASE = 0x104DC0
END = 0x132E74
NFILES = 54
NSLOTS = 100
POINTER_SITES = (0x7DDC, 0x80BC, 0x8348, 0x8600, 0x17E8C)  # literal pools holding 0x08104DC0

# end = where the next data starts (the gap after the last stream is 0xFF padding). sites = every literal pool
# holding 0x08000000 + base (a full-ROM sweep for any word into the archives found only these, phase 5).
# The "test" archive has no pointer: never read (guess), left in place and not translated.
# wide: insert as fullwidth Latin (sjis.fullwidth, 2 bytes per char). The book window draws plain ASCII through the
# half-width writer 0x0800C3A4 into BG tiles it never shows (verified phase 5: ink lands in VRAM, pen advances,
# nothing on screen; fullwidth draws through the 12-px writer, proportional by the VWF delta table).
# The book reads an entry into a 512-byte stack buffer (0x080ADC64: sub sp, 0x200): room 511 bytes.
Spec = namedtuple("Spec", "name base end sites dir prefix wide room")
ARCHIVES = (
    Spec("script", BASE, END, POINTER_SITES, "archive", "", False, None),
    Spec("book", 0x132E74, 0x1348F8, (0xADD8C,), "book", "B", True, 511),       # character book
    Spec("test", 0x1348F8, 0x134930, (), "test", "T", False, None),             # one unused test line
    Spec("desc", 0x134930, 0x135320, (0x8843C, 0x9A548, 0xADE00), "desc", "D", False, None),  # item/skill descriptions
    Spec("effect", 0x135320, 0x1355DC, (0x9CDF4, 0x9CE90, 0xA38EC), "effect", "E", False, None),  # equipment effects
    Spec("place", 0x1355DC, 0x135E6C, (0x96EEC, 0x96F98, 0x97328, 0x973D4), "place", "P", False, None),  # map names
)
BY_NAME = {s.name: s for s in ARCHIVES}
BY_DIR = {s.dir: s for s in ARCHIVES}


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


def message_ids(rom, base=BASE):
    """{message number (file * 100 + slot): [message ids]} from the archive's id map."""
    count = struct.unpack_from("<H", rom, base)[0]
    out = {}
    for mid, num in enumerate(struct.unpack_from("<%dH" % count, rom, base + 2)):
        if num != 0xFFFF:
            out.setdefault(num, []).append(mid)
    return out


def read(rom, base=BASE):
    """base: where the archive sits (a Spec base in the original, its new home in a built ROM)."""
    end = next((s.end for s in ARCHIVES if s.base == base), len(rom))
    count = struct.unpack_from("<H", rom, base)[0]
    table = base + 2 + 2 * count
    first = struct.unpack_from("<I", rom, table)[0]
    if (first - (table - base)) % 8:
        raise ValueError("archive %X: file table is not whole entries" % base)
    nfiles = (first - (table - base)) // 8
    ents = [struct.unpack_from("<II", rom, table + 8 * i) for i in range(nfiles)]
    files = []
    for i, (off, size) in enumerate(ents):
        start = base + off
        stop = base + ents[i + 1][0] if i + 1 < nfiles else end
        raw, used = lh5.decode(rom, start, size)
        last = i + 1 == nfiles  # the last stream may end before the slot end (padding follows)
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
