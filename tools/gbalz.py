"""gbalz.py: GBA BIOS LZ77 (type 0x10) decompress/compress, and a ROM scanner for LZ77 blocks.

decompress(data, off) -> (bytes, end_offset)   raises ValueError on a malformed stream.
compress(raw) -> bytes                          BIOS-compatible (VRAM-safe: no disp 0 / 1-byte back-refs).
scan(rom) -> [(off, size, end)]                 4-aligned headers 0x10 that decode cleanly.
"""


def decompress(d, off, limit=0x40000):
    if d[off] != 0x10:
        raise ValueError("not LZ77")
    size = d[off + 1] | d[off + 2] << 8 | d[off + 3] << 16
    if size == 0 or size > limit:
        raise ValueError("bad size")
    out = bytearray()
    i = off + 4
    n = len(d)
    while len(out) < size:
        if i >= n:
            raise ValueError("eof")
        flags = d[i]
        i += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                if i + 1 >= n:
                    raise ValueError("eof")
                b1, b2 = d[i], d[i + 1]
                i += 2
                length = (b1 >> 4) + 3
                disp = ((b1 & 0xF) << 8 | b2) + 1
                if disp > len(out):
                    raise ValueError("disp before start")
                for _ in range(length):
                    out.append(out[-disp])
            else:
                if i >= n:
                    raise ValueError("eof")
                out.append(d[i])
                i += 1
    return bytes(out[:size]), i


def compress(raw):
    out = bytearray([0x10, len(raw) & 0xFF, len(raw) >> 8 & 0xFF, len(raw) >> 16 & 0xFF])
    i = 0
    n = len(raw)
    while i < n:
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= n:
                break
            best_len, best_disp = 0, 0
            for disp in range(2, min(i, 0x1000) + 1):
                l = 0
                while l < 18 and i + l < n and raw[i + l] == raw[i + l - disp]:
                    l += 1
                if l > best_len:
                    best_len, best_disp = l, disp
                    if l == 18:
                        break
            if best_len >= 3:
                flags |= 0x80 >> bit
                v = (best_len - 3) << 12 | (best_disp - 1)
                out += bytes([v >> 8, v & 0xFF])
                i += best_len
            else:
                out.append(raw[i])
                i += 1
        out[flag_pos] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)


def scan(d, step=4, min_size=32):
    found = []
    for off in range(0, len(d) - 4, step):
        if d[off] != 0x10:
            continue
        size = d[off + 1] | d[off + 2] << 8 | d[off + 3] << 16
        if size < min_size or size > 0x40000:
            continue
        try:
            _, end = decompress(d, off)
        except ValueError:
            continue
        found.append((off, size, end))
    return found
