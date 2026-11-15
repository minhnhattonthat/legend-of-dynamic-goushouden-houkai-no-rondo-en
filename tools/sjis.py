"""sjis.py: the game's text codec (Shift-JIS / cp932 plus control codes), byte-exact both ways.

    decode(b"...") -> str      encode(str) -> bytes      encode(decode(b)) == b for any bytes

Text form (docs/re/text.md):
  0D           -> a real newline "\\n" (line break; in the script the first line is the speaker)
  5C 70 / 73 / 67 (`\\p` `\\s` `\\g`)  -> {p} {s} {g}   (hero name / heroine name / obtained item name or amount)
  21 52 / 21 57   (`!R` `!W`)       -> {!R} {!W}   (printer style [w+0xC8] = 2 / 4: {!R} opens and {!W} closes
                                                    transceiver / remote speech, e.g. 00.66, 01.21; keep both in place)
  a double-byte char that cp932 maps back to the same two bytes -> that char
  printable ASCII 20..7E and half-width kana A1..DF -> the char, except [ ] { } which are escaped
  anything else (control bytes, invalid pairs, duplicate cp932 codes) -> [XX] per byte
The terminating 00 is not part of the text. Tags encode to the same bytes the decoder read, so English text
may use them freely; a literal "!R" in English would encode to the code, so the lint must flag it (phase 7).
"""
import re

TAGS = {b"\\p": "{p}", b"\\s": "{s}", b"\\g": "{g}", b"!R": "{!R}", b"!W": "{!W}"}
TAG_BYTES = {v: k for k, v in TAGS.items()}
ESCAPE = set(b"[]{}")
TOKEN = re.compile(r"\{(p|s|g|!R|!W)\}|\[([0-9A-F]{2})\]")


def is_lead(b):
    return 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC


def decode(data):
    out, i, n = [], 0, len(data)
    while i < n:
        b = data[i]
        two = bytes(data[i:i + 2])
        if two in TAGS:
            out.append(TAGS[two])
            i += 2
            continue
        if b == 0x0D:
            out.append("\n")
            i += 1
            continue
        if is_lead(b) and i + 1 < n:
            try:
                ch = two.decode("cp932")
            except UnicodeDecodeError:
                ch = None
            if ch is not None and len(ch) == 1 and ch.encode("cp932") == two:
                out.append(ch)
                i += 2
                continue
        if (0x20 <= b <= 0x7E and b not in ESCAPE) or 0xA1 <= b <= 0xDF:
            out.append(bytes([b]).decode("cp932"))
        else:
            out.append("[%02X]" % b)
        i += 1
    return "".join(out)


def encode(text):
    out, i = bytearray(), 0
    while i < len(text):
        m = TOKEN.match(text, i)
        if m:
            out += TAG_BYTES["{%s}" % m[1]] if m[1] else bytes([int(m[2], 16)])
            i = m.end()
            continue
        ch = text[i]
        if ch == "\n":
            out.append(0x0D)
        elif ch in "[]{}":
            raise ValueError("unescaped %r at %d in %r (write [5B] [5D] [7B] [7D])" % (ch, i, text))
        else:
            try:
                out += ch.encode("cp932")
            except UnicodeEncodeError:
                raise ValueError("no Shift-JIS code for %r (U+%04X) in %r" % (ch, ord(ch), text)) from None
        i += 1
    return bytes(out)


def fullwidth(text):
    """ASCII -> the fullwidth chars the game's own ASCII map uses (0x080FA6A0: ' -> ’, " -> ”, space -> U+3000),
    for fields read two bytes per char (player names). Tags and [XX] escapes stay as they are."""
    special = {" ": "　", "'": "’", '"': "”", "-": "－", "~": "～"}
    out, i = [], 0
    while i < len(text):
        m = TOKEN.match(text, i)
        if m:
            out.append(m[0])
            i = m.end()
            continue
        c = text[i]
        out.append(special.get(c) or (chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else c))
        i += 1
    return "".join(out)


def is_japanese(text):
    """True if the text has any non-ASCII char (double-byte or half-width kana) outside tags and escapes."""
    return any(ord(c) > 0x7F for c in TOKEN.sub("", text))
