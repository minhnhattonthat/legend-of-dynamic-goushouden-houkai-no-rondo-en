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


# ---------------------------------------------------------------- encoder
# Not byte-identical to the original packer (unknown settings); decode(encode(x)) == x is what the tests check.
# Unchanged files keep their original streams (tools/archive.py), so the identity build stays byte-exact.

MAXDIST = DICSIZ - 1  # stay one inside the game's 8 KiB ring (mask 0x1FFF)
MAXLEN = 16  # longest Huffman code the decoder (LHA make_table) accepts


class _BitWriter:
    def __init__(self):
        self.out = bytearray()
        self.acc = 0
        self.n = 0

    def put(self, n, v):
        if n == 0:
            return
        self.acc = (self.acc << n) | (v & ((1 << n) - 1))
        self.n += n
        while self.n >= 8:
            self.n -= 8
            self.out.append((self.acc >> self.n) & 0xFF)
        self.acc &= (1 << self.n) - 1

    def flush(self):
        if self.n:
            self.out.append((self.acc << (8 - self.n)) & 0xFF)
            self.acc = self.n = 0
        return bytes(self.out)


def _parse(raw, max_chain=256):
    """Greedy LZ parse with one-step lazy matching -> list of int (literal) or (length, dist)."""
    n = len(raw)
    head = {}
    prev = [-1] * n

    def insert(i):
        if i + 3 <= n:
            k = raw[i:i + 3]
            prev[i] = head.get(k, -1)
            head[k] = i

    def find(i):
        if i + 3 > n:
            return 0, 0
        limit = min(MAXMATCH, n - i)
        best, bd = 0, 0
        j = head.get(raw[i:i + 3], -1)
        chain = max_chain
        while j >= 0 and i - j <= MAXDIST and chain:
            if raw[j + best] == raw[i + best] if best < limit else False:
                ln = 3
                while ln < limit and raw[j + ln] == raw[i + ln]:
                    ln += 1
                if ln > best:
                    best, bd = ln, i - j
                    if ln == limit:
                        break
            j = prev[j]
            chain -= 1
        return (best, bd) if best >= THRESHOLD else (0, 0)

    toks = []
    i = 0
    cur = find(0)
    while i < n:
        ln, d = cur
        if ln == 0:
            toks.append(raw[i])
            insert(i)
            i += 1
            cur = find(i)
            continue
        insert(i)
        nxt = find(i + 1) if ln < 32 else (0, 0)
        if nxt[0] > ln:
            toks.append(raw[i])
            i += 1
            cur = nxt
            continue
        toks.append((ln, d))
        for k in range(i + 1, i + ln):
            insert(k)
        i += ln
        cur = find(i)
    return toks


def _limited_lens(freq, limit=MAXLEN):
    """Package-merge: optimal code lengths <= limit for every symbol with freq > 0 (needs >= 2 such symbols)."""
    leaves = sorted(((f, (s,)) for s, f in enumerate(freq) if f), key=lambda x: x[0])
    lists = leaves
    for _ in range(limit - 1):
        packs = [(lists[i][0] + lists[i + 1][0], lists[i][1] + lists[i + 1][1]) for i in range(0, len(lists) - 1, 2)]
        lists = sorted(leaves + packs, key=lambda x: x[0])
    lens = [0] * len(freq)
    for _, syms in lists[:2 * len(leaves) - 2]:
        for s in syms:
            lens[s] += 1
    return lens


def _canon(lens):
    """Codes assigned like _make_codes (by length, then symbol)."""
    codes = [0] * len(lens)
    code = 0
    for L in range(1, 17):
        for s, l in enumerate(lens):
            if l == L:
                codes[s] = code
                code += 1
        code <<= 1
    return codes


def _write_pt_len(w, lens, nbit, i_special):
    n = len(lens)
    while n > 0 and lens[n - 1] == 0:
        n -= 1
    w.put(nbit, n)
    i = 0
    while i < n:
        k = lens[i]
        i += 1
        if k <= 6:
            w.put(3, k)
        else:
            w.put(k - 3, (1 << (k - 3)) - 2)
        if i == i_special:
            while i < 6 and lens[i] == 0:
                i += 1
            w.put(2, i - 3)


def _pcode(d):
    v = d - 1
    return v.bit_length(), v


def _write_block(w, toks):
    cfreq = [0] * NC
    pfreq = [0] * NP
    for t in toks:
        if isinstance(t, int):
            cfreq[t] += 1
        else:
            cfreq[t[0] + 256 - THRESHOLD] += 1
            pfreq[_pcode(t[1])[0]] += 1
    w.put(16, len(toks))
    cused = [s for s in range(NC) if cfreq[s]]
    if len(cused) == 1:
        w.put(TBIT, 0)
        w.put(TBIT, 0)
        w.put(CBIT, 0)
        w.put(CBIT, cused[0])
        clens = None
    else:
        clens = _limited_lens(cfreq)
        n = max(cused) + 1
        tseq = []  # (T symbol, extra bit count, extra value)
        i = 0
        while i < n:
            if clens[i]:
                tseq.append((clens[i] + 2, 0, 0))
                i += 1
                continue
            k = 0
            while i < n and clens[i] == 0:
                k += 1
                i += 1
            if k <= 2:
                tseq += [(0, 0, 0)] * k
            elif k <= 18:
                tseq.append((1, 4, k - 3))
            elif k == 19:
                tseq += [(0, 0, 0), (1, 4, 15)]
            else:
                tseq.append((2, CBIT, k - 20))
        tfreq = [0] * NT
        for s, _, _ in tseq:
            tfreq[s] += 1
        tused = [s for s in range(NT) if tfreq[s]]
        if len(tused) == 1:
            w.put(TBIT, 0)
            w.put(TBIT, tused[0])
            tl = None
        else:
            tl = _limited_lens(tfreq)
            _write_pt_len(w, tl, TBIT, 3)
            tc = _canon(tl)
        w.put(CBIT, n)
        for s, nb, v in tseq:
            if tl:
                w.put(tl[s], tc[s])
            w.put(nb, v)
        ccodes = _canon(clens)
    pused = [s for s in range(NP) if pfreq[s]]
    if len(pused) <= 1:
        w.put(PBIT, 0)
        w.put(PBIT, pused[0] if pused else 0)
        pl = None
    else:
        pl = _limited_lens(pfreq)
        _write_pt_len(w, pl, PBIT, -1)
        pcodes = _canon(pl)
    for t in toks:
        if isinstance(t, int):
            if clens:
                w.put(clens[t], ccodes[t])
            continue
        c = t[0] + 256 - THRESHOLD
        if clens:
            w.put(clens[c], ccodes[c])
        p, v = _pcode(t[1])
        if pl:
            w.put(pl[p], pcodes[p])
        if p > 1:
            w.put(p - 1, v - (1 << (p - 1)))


def encode(raw):
    """lh5 bit stream for raw (no header). decode(encode(raw), 0, len(raw)) == raw."""
    toks = _parse(bytes(raw))
    w = _BitWriter()
    for k in range(0, len(toks), BLOCK):
        _write_block(w, toks[k:k + BLOCK])
    return w.flush()


def pack(raw):
    """Type-2 packed file: u32 header (2 << 24 | size) + lh5 stream."""
    return (2 << 24 | len(raw)).to_bytes(4, "little") + encode(raw)
