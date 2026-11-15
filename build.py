"""build.py: original ROM -> build/goushouden_en.gba.

  python -X utf8 build.py            check the dump against rom.sha1, rebuild, write build/goushouden_en.gba
  python -X utf8 build.py --verify   also fail (exit 1) unless the output is byte-identical to the original
                                     (the identity build; only meaningful while no text is edited)
  python -X utf8 build.py --reencode --out build/reencode.gba   every archive file through our lh5 encoder

Steps: rom check -> script archive (tools/archive.py: unpack every file, repack; unchanged files keep their
original lh5 stream, edited ones are re-encoded by tools/lh5.py) -> write. Menu strings and packed graphics join
here as they get edited (phases 4-8).
"""
import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))

import archive  # noqa: E402
import check_rom  # noqa: E402

ROM = ROOT / "rom" / "Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba"
OUT = ROOT / "build" / "goushouden_en.gba"


def put_archive(rom, arc):
    data = arc.build()
    room = archive.END - archive.BASE
    if len(data) > room:
        raise SystemExit("script archive is %d bytes, %d over its slot: relocation not written yet" % (len(data), len(data) - room))
    rom[archive.BASE:archive.BASE + len(data)] = data
    rom[archive.BASE + len(data):archive.END] = bytes(room - len(data))


def build(orig, reencode=False):
    rom = bytearray(orig)
    arc = archive.read(orig)
    if reencode:  # test the encoder in game: every file goes through tools/lh5.py
        for f in arc.files:
            f.orig_raw = None
    put_archive(rom, arc)
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
