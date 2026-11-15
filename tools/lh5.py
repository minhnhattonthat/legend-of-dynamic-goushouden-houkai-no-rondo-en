"""lh5.py: LHA -lh5- decoder/encoder as used by this game (decoder at 0x08006538, docs/re/compression.md).

The stream has no LHA archive header. In ROM a packed file is a u32 header `type << 24 | unpacked_size`
followed by the lh5 bit stream (type 2). decode(data, off, size) -> (bytes, bytes_consumed).
encode(raw) -> bytes (the bit stream only; prepend the header yourself).
"""

DICBIT = 13
DICSIZ = 1 << DICBIT
MAXMATCH = 256
THRESHOLD = 3
NC = 255 + MAXMATCH + 2 - THRESHOLD  # 510
NP = DICBIT + 1  # 14
NT = 16 + 3  # 19
CBIT = 9
PBIT = 4
TBIT = 5
BLOCK = 0x4000  # max symbols per block


class _Bits:
    def __init__(self, data, off):
        self.d = data
        self.pos = off
        self.buf = 0  # bit buffer
        self.n = 0

    def peek(self, k):
        while self.n < k:
            b = self.d[self.pos] if self.pos < len(self.d) else 0
            self.pos += 1
            self.buf = (self.buf << 8) | b
            self.n += 8
        return (self.buf >> (self.n - k)) & ((1 << k) - 1)

    def get(self, k):
        if k == 0:
            return 0
        v = self.peek(k)
        self.n -= k
        self.buf &= (1 << self.n) - 1
        return v


def _make_codes(lens):
    """Canonical codes as dict (length, code) -> symbol, built the way LHA's make_table orders them."""
    table = {}
    code = 0
    for L in range(1, 17):
        for sym, l in enumerate(lens):
            if l == L:
                table[(L, code)] = sym
                code += 1
        code <<= 1
    return table


def _read_sym(bits, table, maxlen=16):
    code = 0
    for L in range(1, maxlen + 1):
        code = (code << 1) | bits.get(1)
        s = table.get((L, code))
        if s is not None:
            return s
    raise ValueError("bad huffman code at byte %d" % bits.pos)


def _read_pt_len(bits, nn, nbit, i_special):
    n = bits.get(nbit)
    if n == 0:
        c = bits.get(nbit)
        return None, c
    lens = [0] * nn
    i = 0
    while i < n:
        c = bits.get(3)
        if c == 7:
            while bits.get(1):
                c += 1
        lens[i] = c
        i += 1
        if i == i_special:
            z = bits.get(2)
            for _ in range(z):
                lens[i] = 0
                i += 1
    return lens, None


def _read_c_len(bits, pt):
    n = bits.get(CBIT)
    if n == 0:
        return None, bits.get(CBIT)
    lens = [0] * NC
    i = 0
    while i < n:
        c = pt()
        if c <= 2:
            if c == 0:
                cnt = 1
            elif c == 1:
                cnt = bits.get(4) + 3
            else:
                cnt = bits.get(CBIT) + 20
            for _ in range(cnt):
                lens[i] = 0
                i += 1
        else:
            lens[i] = c - 2
            i += 1
    return lens, None


def _decoder(lens, const):
    if lens is None:
        return lambda: const
    t = _make_codes(lens)
    return t


def decode(data, off, size):
    bits = _Bits(data, off)
    out = bytearray()
    while len(out) < size:
        blocksize = bits.get(16)
        tl, tc = _read_pt_len(bits, NT, TBIT, 3)
        if tl is None:
            pt = lambda c=tc: c
        else:
            tt = _make_codes(tl)
            pt = lambda tt=tt: _read_sym(bits, tt)
        cl, cc = _read_c_len(bits, pt)
        if cl is None:
            dc = lambda c=cc: c
        else:
            ct = _make_codes(cl)
            dc = lambda ct=ct: _read_sym(bits, ct)
        pl, pc = _read_pt_len(bits, NP, PBIT, -1)
        if pl is None:
            dp = lambda c=pc: c
        else:
            ptab = _make_codes(pl)
            dp = lambda ptab=ptab: _read_sym(bits, ptab)
        for _ in range(blocksize):
            if len(out) >= size:
                break
            c = dc()
            if c < 256:
                out.append(c)
            else:
                length = c - (256 - THRESHOLD)
                p = dp()
                if p > 1:
                    p = (1 << (p - 1)) + bits.get(p - 1)
                dist = p + 1
                if dist > len(out):
                    raise ValueError("distance before start")
                for _ in range(length):
                    out.append(out[-dist])
    consumed = bits.pos - off
    return bytes(out[:size]), consumed


def unpack(data, off):
    """Decode the packed file at off (u32 header). Returns (type, bytes, total_len_including_header)."""
    hdr = int.from_bytes(data[off:off + 4], "little")
    typ, size = hdr >> 24, hdr & 0xFFFFFF
    if typ == 0x63:
        return typ, bytes(data[off + 4:off + 4 + size]), 4 + size
    if typ != 2:
        raise ValueError("type %d not lh5" % typ)
    raw, used = decode(data, off + 4, size)
    return typ, raw, 4 + used
