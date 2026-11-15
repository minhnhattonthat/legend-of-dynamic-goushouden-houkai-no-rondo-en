"""The English build (phase 7 gate): romdiff with the write log, writes only where allowed, relocated strings."""
import importlib.util
import struct
import unittest
from pathlib import Path

import engine
import extract
import romdiff
import romstr
import sjis
from tests.test_engine import ALLOWED

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba"


@unittest.skipUnless(ROM.exists(), "no ROM dump")
class EnglishBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
        cls.build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.build)
        cls.orig = ROM.read_bytes()
        cls.log = []
        cls.out = cls.build.build(cls.orig, writes=cls.log)
        cls.ptrs = extract.rom_ptrs()

    def writes(self):
        for line in self.log:
            off, old, new, by = line.split(" ", 3)
            yield int(off, 16), bytes.fromhex(old), bytes.fromhex(new), by

    def test_romdiff_with_write_log(self):
        """romdiff.py --writes: original bytes as expected, no overlap, no overwrite, no unlogged change."""
        errs, _ = romdiff.check(self.orig, self.out, set(), list(self.writes()))
        self.assertEqual(errs[:5], [])

    def test_writes_land_only_where_allowed(self):
        """Engine sites, fonts, free space, string slots, the new space, and a relocated string's own pointers."""
        sites = {s for v in self.ptrs.values() for s in v}
        for off, _, new, by in self.writes():
            if by.endswith(" ptr") and by.startswith("string "):
                self.assertIn(off, self.ptrs[int(by.split()[1], 16)], by)
                continue
            self.assertTrue(any(lo <= off and off + len(new) <= hi for lo, hi in ALLOWED) or off in sites,
                            "write at %X (%s)" % (off, by))

    def test_relocated_strings_are_reached_by_every_pointer(self):
        moved = 0
        for off, room, text, translated in extract.rom_texts():
            data = sjis.encode(sjis.fullwidth(text) if off in extract.FULLWIDTH else text)
            if not translated or len(data) <= room:
                continue
            moved += 1
            for site in self.ptrs[off]:
                at = struct.unpack_from("<I", self.out, site)[0] - 0x08000000
                self.assertGreaterEqual(at, engine.NEW_ARCHIVE, "r%06X" % off)
                self.assertEqual(self.out[at:at + len(data) + 1], data + b"\0", "r%06X via %06X" % (off, site))
        print("relocated strings: %d" % moved)

    def test_data_spans_untouched(self):
        """Pointed "strings" that are really tables (romstr.DATA_SPANS) keep their original bytes (review I1)."""
        for lo, hi, why in romstr.DATA_SPANS:
            self.assertEqual(self.out[lo:hi], self.orig[lo:hi], "%06X-%06X changed: %s" % (lo, hi, why))

    def test_every_table_writes_all_its_entries(self):
        """Per script/rom file: the strings the build wrote are exactly the entries with English (review M5)."""
        wrote = {int(by.split()[1], 16) for _, _, _, by in self.writes()
                 if by.startswith("string ") and not by.endswith(" ptr")}
        for name in extract.script_files():
            if not name.startswith("rom/"):
                continue
            want = {int(e["id"][1:], 16) for e in extract.load(name) if extract.translated(e)}
            ids = {int(e["id"][1:], 16) for e in extract.load(name)}
            self.assertEqual(sorted(wrote & ids), sorted(want), name)

    def test_no_stale_reader_of_a_vacated_string(self):
        """No word in the original other than a relocated string's listed ptrs points at its old address (review M4).
        Flag bits masked: 0x08/0x09 region byte, any 4-aligned word in the ROM."""
        moved = set()
        for off, room, text, translated in extract.rom_texts():
            data = sjis.encode(sjis.fullwidth(text) if off in extract.FULLWIDTH else text)
            if translated and len(data) > room:
                moved.add(off)
        words = struct.unpack_from("<%dI" % (len(self.orig) // 4), self.orig)
        stale = []
        for i, w in enumerate(words):
            if (w >> 25) == 0x04 and (w & 0x01FFFFFF) in moved and i * 4 not in self.ptrs[w & 0x01FFFFFF]:
                stale.append("%06X -> r%06X" % (i * 4, w & 0x01FFFFFF))
        self.assertEqual(stale, [])
