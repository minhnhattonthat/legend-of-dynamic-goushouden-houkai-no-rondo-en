"""build.py: original ROM -> build/goushouden_en.gba.

  python -X utf8 build.py            check the dump against rom.sha1, rebuild, write build/goushouden_en.gba
  python -X utf8 build.py --verify   also fail (exit 1) unless the output is byte-identical to the original
                                     (the identity build; only meaningful while no text is edited)
  python -X utf8 build.py --reencode --out build/reencode.gba   every archive file through our lh5 encoder

Steps: rom check -> script archive (tools/archive.py: unpack every file, rebuild each from script/archive/*.json
via tools/extract.py + tools/sjis.py, repack; unchanged files keep their original lh5 stream, edited ones are
re-encoded by tools/lh5.py) -> translated plain ROM strings from script/rom/*.json, in place -> write.
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
import extract  # noqa: E402
import sjis  # noqa: E402

ROM = ROOT / "rom" / "Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba"
OUT = ROOT / "build" / "goushouden_en.gba"


def put_archive(rom, arc):
    data = arc.build()
    room = archive.END - archive.BASE
    if len(data) > room:
        raise SystemExit("script archive is %d bytes, %d over its slot: relocation not written yet" % (len(data), len(data) - room))
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


def insert_rom_strings(rom, texts):
    """Translated plain strings and record names go in place (relocation comes in phase 7)."""
    for off, room, text, translated in texts:
        if not translated:
            continue
        data = sjis.encode(text)
        if len(data) > room:
            raise SystemExit("r%06X: %d bytes, room for %d: %r" % (off, len(data), room, text))
        rom[off:off + room + 1] = data + bytes(room + 1 - len(data))


def build(orig, reencode=False):
    rom = bytearray(orig)
    arc = archive.read(orig)
    insert_archive(arc, extract.archive_texts())
    if reencode:  # test the encoder in game: every file goes through tools/lh5.py
        for f in arc.files:
            f.orig_raw = None
    put_archive(rom, arc)
    insert_rom_strings(rom, extract.rom_texts())
    return bytes(rom)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--reencode", action="store_true", help="re-encode every archive file (encoder test build)")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    check_rom.check()
    orig = ROM.read_bytes()
    out = build(orig, args.reencode)
    args.out.parent.mkdir(exist_ok=True)
    args.out.write_bytes(out)
    same = out == orig
    print("%s  %s  %s" % (hashlib.sha1(out).hexdigest(), args.out, "identical to the original" if same else "differs"))
    if args.verify and not same:
        sys.exit(1)


if __name__ == "__main__":
    main()
