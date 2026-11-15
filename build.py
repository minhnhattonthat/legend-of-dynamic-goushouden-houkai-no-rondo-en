"""build.py: original ROM -> build/goushouden_en.gba.

  python -X utf8 build.py            check the dump against rom.sha1, build build/goushouden_en.gba (+ .writes.txt)
  python -X utf8 build.py --marker   every line -> its id + filler: build/goushouden_marker.gba (tools/marker.py)
  python -X utf8 build.py --verify   identity build (no engine changes); exit 1 unless byte-identical to the original
  python -X utf8 build.py --reencode --out build/reencode.gba   identity build, every archive file through our lh5

Steps: rom check -> engine patches (tools/engine.py: 16 MiB, archive pointers, VWF hook and font) -> script
archive (tools/archive.py: unpack every file, rebuild each from script/archive/*.json via tools/extract.py +
tools/sjis.py, repack; unchanged files keep their original lh5 stream, edited ones are re-encoded by tools/lh5.py)
at engine.NEW_ARCHIVE -> translated plain ROM strings from script/rom/*.json, in place -> write. Every write goes
through Writer.put and is logged to <out>.writes.txt for romdiff.py --writes.
Packed graphics join here as they get edited (phase 8).
"""
import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))

import archive  # noqa: E402
import check_rom  # noqa: E402
import engine  # noqa: E402
import extract  # noqa: E402
import marker as marker_mod  # noqa: E402
import sjis  # noqa: E402

ROM = ROOT / "rom" / "Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba"
OUT = ROOT / "build" / "goushouden_en.gba"
MARKER = ROOT / "build" / "goushouden_marker.gba"


class Writer:
    """Every byte the build changes goes through put(), logged with the original bytes it replaces
    (build/writes.txt, checked by romdiff.py --writes)."""

    def __init__(self, rom, orig):
        self.rom, self.orig, self.log = rom, orig, []

    def put(self, off, data, by):
        old = self.orig[off:off + len(data)].ljust(len(data), b"\xff")
        self.log.append("%X %s %s %s" % (off, old.hex(), bytes(data).hex(), by))
        self.rom[off:off + len(data)] = data


def put_archive(w, arc, at):
    data = arc.build()
    if at + len(data) > len(w.rom):
        raise SystemExit("script archive is %d bytes, too big for 0x%X.." % (len(data), at))
    w.put(at, data, "script archive")


def put_archive_inplace(rom, arc):
    data = arc.build()
    room = archive.END - archive.BASE
    if len(data) > room:
        raise SystemExit("script archive is %d bytes, %d over its slot" % (len(data), len(data) - room))
    rom[archive.BASE:archive.BASE + len(data)] = data
    rom[archive.BASE + len(data):archive.END] = bytes(room - len(data))


def insert_archive(arc, texts):
    """script/archive texts -> each file's raw bytes (slot = encode(text) + 00, slots in order)."""
    for fi, f in enumerate(arc.files):
        slots = archive.split_file(f.raw)
        got = texts.get(fi, {})
        if set(got) != {j for j, s in enumerate(slots) if s is not None}:
            raise SystemExit("script/archive/f%02d.json: slot list differs from the ROM's" % fi)
        f.raw = archive.join_file([None if s is None else sjis.encode(got[j]) + b"\0" for j, s in enumerate(slots)])


FULLWIDTH = extract.FULLWIDTH


def insert_rom_strings(rom, texts, put=None):
    """Translated plain strings and record names go in place (relocation comes in phase 7)."""
    for off, room, text, translated in texts:
        if not translated:
            continue
        data = sjis.encode(sjis.fullwidth(text) if off in FULLWIDTH else text)
        if len(data) > room:
            raise SystemExit("r%06X: %d bytes, room for %d: %r" % (off, len(data), room, text))
        data += bytes(room + 1 - len(data))
        if put:
            put(off, data, "string %06X" % off)
        else:
            rom[off:off + room + 1] = data


def identity(orig, reencode=False):
    """Unpack and repack with no engine changes, archive in its own slot: equals the original (phase 3 test)."""
    rom = bytearray(orig)
    arc = archive.read(orig)
    insert_archive(arc, extract.archive_texts(jp=True))
    if reencode:  # test the encoder in game: every file goes through tools/lh5.py
        for f in arc.files:
            f.orig_raw = None
    put_archive_inplace(rom, arc)
    insert_rom_strings(rom, extract.rom_texts(jp=True))
    return bytes(rom)


def build(orig, marker=False, writes=None, qa=()):
    """The English ROM: engine patches (tools/engine.py), archive at engine.NEW_ARCHIVE, strings in place.
    qa: ("FF.SS", text) overrides for single script messages (stress / torture lines)."""
    rom = bytearray(orig)
    w = Writer(rom, orig)
    engine.apply(rom, w.put, orig)
    arc = archive.read(orig)
    scope = marker if isinstance(marker, str) else "all"  # bisecting: "archive", "rom" or "rom:LO-HI" (hex offsets)
    texts = marker_mod.archive_markers() if marker and scope in ("all", "archive") else extract.archive_texts()
    for mid, text in qa:
        fi, slot = (int(x) for x in mid.split("."))
        if slot not in texts.get(fi, {}):
            raise SystemExit("--qa %s: no such message" % mid)
        texts[fi][slot] = text.replace("\\n", "\n")
    insert_archive(arc, texts)
    put_archive(w, arc, engine.NEW_ARCHIVE)
    texts = extract.rom_texts()
    if marker and scope != "archive":
        lo, hi = 0, len(orig)
        if scope.startswith("rom:"):
            lo, hi = (int(x, 16) for x in scope[4:].split("-"))
        marks = {t[0]: t for t in marker_mod.rom_markers() if lo <= t[0] < hi}
        texts = [marks.get(t[0], t) for t in texts]
    insert_rom_strings(rom, texts, w.put)
    if writes is not None:
        writes.extend(w.log)
    return bytes(rom)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true", help="identity build: no engine changes, must equal the original")
    ap.add_argument("--reencode", action="store_true", help="identity build with every archive file re-encoded")
    ap.add_argument("--marker", nargs="?", const=True, default=False, metavar="SCOPE",
                    help="every line replaced by its id + filler (phase 5); SCOPE archive | rom | rom:LO-HI to bisect")
    ap.add_argument("--qa", action="append", default=[], metavar="FF.SS=TEXT",
                    help="override one script message (text form, \\n = newline); repeatable")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    check_rom.check()
    orig = ROM.read_bytes()
    log = []
    if args.verify or args.reencode:
        out = identity(orig, args.reencode)
    else:
        out = build(orig, args.marker, log, [q.split("=", 1) for q in args.qa])
    dest = args.out or (MARKER if args.marker else OUT)
    dest.parent.mkdir(exist_ok=True)
    dest.write_bytes(out)
    if log:
        dest.with_suffix(".writes.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    same = out == orig
    print("%s  %s  %s" % (hashlib.sha1(out).hexdigest(), dest, "identical to the original" if same else "differs"))
    if args.verify and not same:
        sys.exit(1)


if __name__ == "__main__":
    main()
