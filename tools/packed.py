"""packed.py: the game's packed-file formats (docs/re/compression.md), dispatched by unpack() like 0x08000F58.

Header u32 `type << 24 | unpacked_size`, then:
  type 1: u32 `bits` (0..4), then a 16-bit-unit LZSS stream (decoder 0x08002E64), see decode1()
  type 2: lh5 bit stream (tools/lh5.py)
  type 3: bit-level LZ (decoder 0x08001D70), see decode3()
  type 0x63: stored

  python -X utf8 tools/packed.py OFFSET [OUT.bin]     decode one block from the ROM
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lh5  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM = os.path.join(ROOT, "rom", "Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba")


class DecodeError(Exception):
    pass


def decode1(data, off, size, bits):
    """Type 1: LZSS over u16 words. Ring of N = 0x1000 >> bits words, write position starts at N - F where
    F = (8 << bits) + 2; the first N - F ring words are zero.
    Control byte c: c == 0 -> no-op; c < 0x80 -> c literal words follow (2 bytes each, little-endian);
    c >= 0x80 -> one more byte d: ring position = (c & 0x7F) | (d >> (3 + bits)) << 7,
    length = (d & ((8 << bits) - 1)) + 3 words copied from the ring (absolute position).
    Returns (bytes, bytes consumed incl. nothing before off)."""
    if not 0 <= bits <= 4:
        raise DecodeError("bits %d" % bits)
    n = 0x1000 >> bits
    f = (8 << bits) + 2
    ring = [0] * n
    r = (n - f) & (n - 1)
    out = bytearray()
    p = off
    lmask = (8 << bits) - 1
    end = len(data)
    while len(out) < size:
        if p >= end:
            raise DecodeError("ran off the end")
        c = data[p]
        p += 1
        if c < 0x80:
            for _ in range(c):
                if len(out) >= size:
                    break
                if p + 2 > end:
                    raise DecodeError("ran off the end")
                w = data[p] | data[p + 1] << 8
                p += 2
                out += bytes((w & 0xFF, w >> 8))
                ring[r] = w
                r = (r + 1) & (n - 1)
        else:
            if p >= end:
                raise DecodeError("ran off the end")
            d = data[p]
            p += 1
            pos = (c & 0x7F) | (d >> (3 + bits)) << 7
            ln = (d & lmask) + 3
            for i in range(ln):
                w = ring[(pos + i) & (n - 1)]
                out += bytes((w & 0xFF, w >> 8))
                ring[r] = w
                r = (r + 1) & (n - 1)
    return bytes(out[:size]), p - off


def unpack(data, off):
    """Decode the packed file at `off` -> (type, bytes, packed length incl. header)."""
    hdr = struct.unpack_from("<I", data, off)[0]
    typ, size = hdr >> 24, hdr & 0xFFFFFF
    if typ == 1:
        bits = struct.unpack_from("<I", data, off + 4)[0]
        out, used = decode1(data, off + 8, size, bits)
        return typ, out, 8 + used
    if typ == 2:
        out, used = lh5.decode(data, off + 4, size)
        return typ, bytes(out), 4 + used
    if typ == 3:
        out, used = decode3(data, off + 4, size)
        return typ, out, 4 + used
    if typ == 0x63:
        return typ, bytes(data[off + 4:off + 4 + size]), 4 + size
    raise DecodeError("type %X" % typ)


class _MsbBits:
    def __init__(self, data, off):
        self.d, self.p, self.n = data, off, 8  # n = unread bits left in data[p]

    def get(self, k):
        v = 0
        for _ in range(k):
            if self.p >= len(self.d):
                raise DecodeError("ran off the end")
            self.n -= 1
            v = v << 1 | (self.d[self.p] >> self.n & 1)
            if self.n == 0:
                self.p += 1
                self.n = 8
        return v

    def used(self, off):
        return self.p - off + (self.n != 8)


def decode3(data, off, size):
    """Type 3: MSB-first bit stream LZ77 (0x08001D70). Per item:
    1 -> literal byte (8 bits);
    00 -> copy 1 byte from distance getbits(5) + 1;
    01 -> k = getbits(2): k < 3: len k + 2, dist getbits(8) + 1;
          k == 3: m = getbits(4): m < 15: len m + 5, dist getbits(9) + 1;
                  m == 15: m = getbits(8): m < 255: len m + 20, dist getbits(10) + 1;
                           m == 255: len getbits(12) + 0x113, dist getbits(11) + 1.
    Copies run forward byte by byte (overlap repeats)."""
    bs = _MsbBits(data, off)
    out = bytearray(PRE3)
    size += PRE3
    while len(out) < size:
        if bs.get(1):
            out.append(bs.get(8))
            continue
        if not bs.get(1):
            ln, dist = 1, bs.get(5)
        else:
            k = bs.get(2)
            if k < 3:
                ln, dist = k + 2, bs.get(8)
            else:
                m = bs.get(4)
                if m < 15:
                    ln, dist = m + 5, bs.get(9)
                else:
                    m = bs.get(8)
                    if m < 255:
                        ln, dist = m + 20, bs.get(10)
                    else:
                        ln = bs.get(12) + 0x113
                        dist = bs.get(11)
        s = len(out) - dist - 1
        if s < 0:
            raise DecodeError("distance before start")
        for i in range(ln):
            out.append(out[s + i])
    return bytes(out[PRE3:size]), bs.used(off)


PRE3 = 0x800  # zero history before the output: the encoder lets copies reach back before the start


def main():
    rom = open(ROM, "rb").read()
    off = int(sys.argv[1], 16) & 0x1FFFFFF
    typ, out, used = unpack(rom, off)
    print("type %d size %X packed %X" % (typ, len(out), used))
    if len(sys.argv) > 2:
        open(sys.argv[2], "wb").write(out)


if __name__ == "__main__":
    main()
