"""romstr.py: the plain Shift-JIS strings in ROM outside the script archive (docs/re/text.md §2).

  pointers(rom)          -> {target offset: [offsets of 4-aligned u32 words 0x08xxxxxx pointing there]}
  text_at(rom, p)        -> (end offset of the 00 terminator, n non-ASCII chars) or None if not text
  scan(rom)              -> every string candidate in the ROM: [(start, end, nwide, ptr_sites)]
  sfx_records(rom)       -> the onomatopoeia record table: [(name offset, name bytes)]
  jp_runs(rom, lo, hi)   -> kana/kanji runs at any alignment (the coverage test's net for missed text)
  slot_room(rom, s, e)   -> bytes a string may take in place, 00 included

A candidate starts at a 00 boundary (or a pointer target), is valid text up to a 00 and holds at least one
double-byte char; pointed pure-ASCII strings of two or more chars count too (format strings, save magic).
"""
import re

import numpy as np

import sjis

ROM_BASE = 0x08000000
# the game's string sections (0x0CD000..0x0CD95C before the first string is code)
TEXT_RANGES = ((0x0CD95C, 0x0D5000), (0x0D9000, 0x0DF000))
# onomatopoeia records {u32 id, u32, u32, char name[20]}: base (pointer at 0x0C63B0), end, stride, name offset, size
SFX_TABLE = (0x0D9CF8, 0x0DAFB8, 0x20, 0x0C, 0x14)
# where pointer words live: code + literal pools + tables up to the script archive, and the record tables at the
# ROM's end (0x7B311A..0x7ED9E0, not packed; character/item records)
SITE_RANGES = ((0, 0x104DC0), (0x7B0000, 0x7F0000))
# pointed strings that are not text (extracted with status "data", never translated)
DATA_SPANS = (
    (0x0D9C58, 0x0D9CF8, "onomatopoeia glyph lookup: one kana per entry (table at 0x104D40), maps SFX name kana to sprites"),
    (0x0CE010, 0x0CE154, "ASCII/half-width kana -> fullwidth SJIS map rows (table at 0x0FA6A0, used by 0x0800FE5C): "
                         "English text depends on it (marker build blanked every box, phase 5)"),
    (0x0CD95C, 0x0CDA60, "ASCII -> fullwidth SJIS lookup, 2 bytes per ASCII code (read by 0x08003DE4 as table[c*2]); "
                         "translating it broke the table (phase 7 review I1)"),
)
MAXLEN = 600


def pointers(rom, ranges=SITE_RANGES):
    """{target: [sites]} for the 4-aligned u32 words 0x08xxxxxx inside `ranges`. Only code and tables count:
    words in packed assets hit string addresses by chance (48 such hits landed mid-string, 0x14C41C..0x60FC58)."""
    out = {}
    for lo, hi in ranges:
        lo = (lo + 3) & ~3
        words = np.frombuffer(bytes(rom[lo:min(hi, len(rom)) & ~3]), dtype="<u4")
        hit = np.nonzero((words >= ROM_BASE) & (words < ROM_BASE + len(rom)))[0]
        for i in hit.tolist():
            out.setdefault(int(words[i]) - ROM_BASE, []).append(lo + 4 * i)
    return out


def text_at(rom, p):
    i, wide, n = p, 0, len(rom)
    while i < n and i - p <= MAXLEN:
        b = rom[i]
        if b == 0:
            return i, wide
        if sjis.is_lead(b):
            try:
                ch = bytes(rom[i:i + 2]).decode("cp932")
            except UnicodeDecodeError:
                return None
            if ch.encode("cp932") != bytes(rom[i:i + 2]):
                return None
            wide += 1
            i += 2
        elif 0x20 <= b <= 0x7E or b in (0x0A, 0x0D, 0x1B):
            i += 1
        else:  # half-width kana (A1..DF) included: the game's text is all full-width, these are data bytes
            return None
    return None


def scan(rom, ptrs=None):
    ptrs = pointers(rom) if ptrs is None else ptrs
    out, p, n = [], 0, len(rom)
    while p < n:
        if rom[p] and (p == 0 or rom[p - 1] == 0 or p in ptrs):
            r = text_at(rom, p)
            if r:
                end, wide = r
                sites = ptrs.get(p, [])
                if wide or (sites and end - p >= 2):
                    out.append((p, end, wide, sites))
                    p = end + 1
                    continue
        p += 1
    return out


def sfx_records(rom):
    """-> [(name offset, name bytes without the 00)] for every record, empty names included."""
    start, end, stride, at, field = SFX_TABLE
    return [(o + at, bytes(rom[o + at:o + at + field]).split(b"\0")[0]) for o in range(start, end, stride)]


JP_CHAR = re.compile(r"[ぁ-ヿ一-鿿]")  # kana and kanji


def jp_runs(rom, lo, hi, skip=None, minrun=2):
    """[(offset, text)] for runs of minrun+ consecutive Shift-JIS kana/kanji in rom[lo:hi], at any alignment,
    ignoring bytes where skip[i] is set: text an extractor missed shows up here."""
    out, i = [], lo
    while i < hi - 1:
        if (skip and skip[i]) or not sjis.is_lead(rom[i]):
            i += 1
            continue
        j, n = i, 0
        while j < hi - 1 and not (skip and skip[j]) and sjis.is_lead(rom[j]):
            try:
                ch = bytes(rom[j:j + 2]).decode("cp932")
            except UnicodeDecodeError:
                break
            if not JP_CHAR.match(ch):
                break
            n, j = n + 1, j + 2
        if n >= minrun:
            out.append((i, bytes(rom[i:j]).decode("cp932")))
            i = j
        else:
            i += 1
    return out


def slot_room(rom, start, end):
    """Bytes a string at start..end (end = its 00) may use in place, terminator included: up to the next
    4-aligned boundary after the 00 padding that follows it (strings are 4-aligned by the compiler)."""
    q = end + 1
    while q < len(rom) and q % 4 and rom[q] == 0:
        q += 1
    return q - start
