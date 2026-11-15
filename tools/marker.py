"""marker.py: marker text for the phase 5 marker build (`build.py --marker`).

Every script message keeps its line and tag structure ({p} {s} {g} {!R} {!W} [XX] stay where they were); the
speaker line becomes the message id (`02.00`), every other non-empty line becomes `02.00 ` plus a pangram long
enough to run past any box, so the shot shows the id and where the box clips. ROM strings (menus, items, names)
become their offset plus filler up to their in-place byte budget (`max`), e.g. `D0000:abcdefghijklm`.
Entries with status `data` are left alone.

  python -X utf8 tools/marker.py ID     print the marker for one id (debug)
"""
import re
import sys

import archive
import extract
import sjis

FILL = "The quick brown fox jumps over the lazy dog 0123456789 THE QUICK BROWN FOX JUMPS OVER"
TAG = re.compile(r"(\{(?:p|s|g|!R|!W)\}|\[[0-9A-F]{2}\])")


def message_marker(mid, jp):
    lines = jp.split("\n")
    out = []
    for k, line in enumerate(lines):
        parts = TAG.split(line)
        tags_lead, rest = [], parts
        while len(rest) > 1 and rest[0] == "" and TAG.fullmatch(rest[1]):  # tags at the line start stay in front
            tags_lead.append(rest[1])
            rest = rest[2:]
        body = "".join(p for p in rest if not TAG.fullmatch(p))
        tail = [p for p in rest if TAG.fullmatch(p)]
        if not body.strip():
            out.append("".join(tags_lead + tail))
            continue
        text = mid if k == 0 and len(lines) > 1 else "%s %s" % (mid, FILL)
        out.append("".join(tags_lead) + text + "".join(tail))
    return "\n".join(out)


def rom_marker(sid, jp, room):
    tail = "".join(TAG.findall(jp))
    head = sid[1:].lstrip("0") or "0"
    budget = room - len(sjis.encode(tail))
    text = (head + ":" + "abcdefghijklmnopqrstuvwxyz0123456789" * 3)[:max(budget, 0)]
    return text + tail


def archive_markers(arc="script"):
    """-> {file index: {slot: marker}} for archive `arc` (archive.ARCHIVES name). An archive read into a fixed
    buffer (Spec.room) gets lines cut to WIDE_LINE chars, still past any box (the book box holds ~20)."""
    spec = archive.BY_NAME[arc]
    out = {}
    for name in extract.script_files():
        m = re.fullmatch(r"%s/f(\d+)\.json" % spec.dir, name)
        if m:
            msgs = {}
            for e in extract.load(name):
                t = message_marker(e["id"], e["jp"])
                if spec.room:
                    t = "\n".join(line[:WIDE_LINE] for line in t.split("\n"))
                msgs[int(e["id"].split(".")[1])] = t
            out[int(m[1])] = msgs
    return out


WIDE_LINE = 40


def rom_markers():
    out = []
    for name in extract.script_files():
        if name.startswith("rom/"):
            for e in extract.load(name):
                if e.get("status") == "data":
                    continue
                off = int(e["id"][1:], 16)
                room = e["max"] // 2 if off in extract.FULLWIDTH else e["max"]
                out.append((off, e["max"], rom_marker(e["id"], e["jp"], room), True))
    return out


if __name__ == "__main__":
    want = sys.argv[1]
    for fi, msgs in archive_markers().items():
        for j, t in msgs.items():
            if "%02d.%02d" % (fi, j) == want:
                print(t)
    for off, room, t, _ in rom_markers():
        if "%06X" % off == want.lstrip("rx").upper().rjust(6, "0"):
            print(room, t)
