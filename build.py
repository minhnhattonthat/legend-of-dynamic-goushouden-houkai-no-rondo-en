"""build.py: original ROM -> build/goushouden_en.gba.

  python -X utf8 build.py            check the dump against rom.sha1, build build/goushouden_en.gba (+ .writes.txt)
  python -X utf8 build.py --marker   every line -> its id + filler: build/goushouden_marker.gba (tools/marker.py)
  python -X utf8 build.py --verify   identity build (no engine changes); exit 1 unless byte-identical to the original
  python -X utf8 build.py --reencode --out build/reencode.gba   identity build, every archive file through our lh5

Steps: rom check -> engine patches (tools/engine.py: 16 MiB, archive pointers, VWF hook and font) -> script
archive (tools/archive.py: unpack every file, rebuild each from script/archive/*.json via tools/extract.py +
tools/sjis.py, repack; unchanged files keep their original lh5 stream, edited ones are re-encoded by tools/lh5.py)
at engine.NEW_ARCHIVE, then the five archives after it (book, desc, effect, place; archive.ARCHIVES) from
script/<dir>/*.json, their literal pools repointed -> translated plain ROM strings from script/rom/*.json, in place, or
after the archives with every pointer rewritten when longer than the slot (phase 7) -> write. Every write goes
through Writer.put and is logged to <out>.writes.txt for romdiff.py --writes.
Packed graphics join here as they get edited (phase 8).
"""
import argparse
import hashlib
import struct
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


def put_archive(w, arc, at, name="script"):
    """Write the archive at `at`; returns the 4-aligned end."""
    data = arc.build()
    if at + len(data) > len(w.rom):
        raise SystemExit("%s archive is %d bytes, too big for 0x%X.." % (name, len(data), at))
    w.put(at, data, "%s archive" % name)
    return (at + len(data) + 3) & ~3


def put_archive_inplace(rom, arc, spec=archive.ARCHIVES[0]):
    """The identity build: the archive back in its own slot (the script archive's slack zero-filled, the others'
    left as they were: their unchanged files keep their original streams)."""
    data = arc.build()
    room = spec.end - spec.base
    if len(data) > room:
        raise SystemExit("%s archive is %d bytes, %d over its slot" % (spec.name, len(data), len(data) - room))
    rom[spec.base:spec.base + len(data)] = data
    if spec.base == archive.BASE:
        rom[spec.base + len(data):spec.end] = bytes(room - len(data))


def encode_slot(text, spec, wide=False):
    """One message's bytes: encode(text) + 00; fullwidth Latin for a `wide` archive (archive.Spec) when wide=True
    (the English build; the identity build keeps the original bytes); checked against the archive's buffer room."""
    data = sjis.encode(sjis.fullwidth(text) if wide and spec.wide else text)
    if spec.room is not None and len(data) > spec.room:
        raise SystemExit("%s archive: %d bytes, the buffer holds %d: %r" % (spec.name, len(data), spec.room, text))
    return data + b"\0"


def insert_archive(arc, texts, spec=archive.ARCHIVES[0], wide=False):
    """script/<dir> texts -> each file's raw bytes (slot = encode(text) + 00, slots in order)."""
    for fi, f in enumerate(arc.files):
        slots = archive.split_file(f.raw)
        got = texts.get(fi, {})
        if set(got) != {j for j, s in enumerate(slots) if s is not None}:
            raise SystemExit("script/%s/f%02d.json: slot list differs from the ROM's" % (spec.dir, fi))
        f.raw = archive.join_file([None if s is None else encode_slot(got[j], spec, wide) for j, s in enumerate(slots)])


FULLWIDTH = extract.FULLWIDTH
SCRIPT_FILE_MAX = 0x8000  # bytes per unpacked script file (heap-allocated; see build()); the marker build's
                          # largest file, 28,566 bytes, ran the whole marker tour


def insert_rom_strings(rom, texts, put=None, reloc=None):
    """Translated plain strings and record names go in place; one longer than its slot is relocated when reloc =
    (orig, at, ptrs): written at `at` (free space after the archives) and every pointer word in ptrs[off] (the
    extracted sites, each asserted to hold 0x08000000 + off in the original) repointed. Returns the new cursor."""
    for off, room, text, translated in texts:
        if not translated:
            continue
        data = sjis.encode(sjis.fullwidth(text) if off in FULLWIDTH else text)
        if len(data) > room and reloc is not None:
            orig, at, ptrs = reloc
            sites = ptrs.get(off)
            if not sites:
                raise SystemExit("r%06X: %d bytes, room for %d and no pointer to move it: %r" % (off, len(data), room, text))
            if at + len(data) + 1 > engine.ROM_SIZE:
                raise SystemExit("relocated strings run past the end of the ROM at r%06X" % off)
            put(at, data + b"\0", "string %06X relocated" % off)
            for site in sites:
                if struct.unpack_from("<I", orig, site)[0] != 0x08000000 + off:
                    raise SystemExit("r%06X: pointer at %06X does not hold its address in the original" % (off, site))
                put(site, struct.pack("<I", 0x08000000 + at), "string %06X ptr" % off)
            at = (at + len(data) + 1 + 3) & ~3
            reloc = (orig, at, ptrs)
            continue
        if len(data) > room:
            raise SystemExit("r%06X: %d bytes, room for %d: %r" % (off, len(data), room, text))
        data += bytes(room + 1 - len(data))
        if put:
            put(off, data, "string %06X" % off)
        else:
            rom[off:off + room + 1] = data
    return reloc[1] if reloc else None


def identity(orig, reencode=False):
    """Unpack and repack with no engine changes, archive in its own slot: equals the original (phase 3 test)."""
    rom = bytearray(orig)
    for spec in archive.ARCHIVES:
        arc = archive.read(orig, spec.base)
        insert_archive(arc, extract.archive_texts(jp=True, name=spec.name), spec)
        if reencode and spec.base == archive.BASE:  # test the encoder in game: every file goes through tools/lh5.py
            for f in arc.files:
                f.orig_raw = None
        put_archive_inplace(rom, arc, spec)
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
    # each script file is malloc'd at its unpacked size when a scene opens it (0x08017E65; docs/re/memory.md §Heap):
    # ~148 KB is free on a field map, the largest JP file is 7,343 bytes; keep every file well inside the heap
    for fi, f in enumerate(arc.files):
        if len(f.raw) > SCRIPT_FILE_MAX:
            raise SystemExit("script file %02d: %d bytes unpacked, the limit is %d" % (fi, len(f.raw), SCRIPT_FILE_MAX))
    cur = put_archive(w, arc, engine.NEW_ARCHIVE)
    # the five archives after it (docs/re/text.md §1b): rebuilt after the script archive, their literal pools
    # repointed; one with no pointer (the unused test line) stays where it is, untouched
    for spec in archive.ARCHIVES[1:]:
        if not spec.sites:
            continue
        arc = archive.read(orig, spec.base)
        use = marker and scope in ("all", "archive")
        insert_archive(arc, marker_mod.archive_markers(spec.name) if use else extract.archive_texts(name=spec.name),
                       spec, wide=True)
        at = cur
        cur = put_archive(w, arc, at, spec.name)
        for site in spec.sites:
            if struct.unpack_from("<I", orig, site)[0] != 0x08000000 + spec.base:
                raise SystemExit("%s archive pointer at %X: unexpected value" % (spec.name, site))
            w.put(site, struct.pack("<I", 0x08000000 + at), "%s archive ptr" % spec.name)
    texts = extract.rom_texts()
    if marker and scope != "archive":
        lo, hi = 0, len(orig)
        if scope.startswith("rom:"):
            lo, hi = (int(x, 16) for x in scope[4:].split("-"))
        marks = {t[0]: t for t in marker_mod.rom_markers() if lo <= t[0] < hi}
        texts = [marks.get(t[0], t) for t in texts]
    insert_rom_strings(rom, texts, w.put, (orig, cur, extract.rom_ptrs()))
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
