"""Engine patches (tools/engine.py): the built ROM, its write log and the VWF tables."""
import importlib.util
import struct
import unittest
from pathlib import Path

import archive
import engine
import gfx
import sjis

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba"

# Where the build may write: archive pointer literals, the 12-px font, the free slot, ROM strings, new space.
ALLOWED = [(s, s + 4) for a in archive.ARCHIVES for s in a.sites] + [(site, site + 4) for site, _ in engine.ADV_SITES] + [
    (site, site + 4) for site, _ in engine.HALF_SITES] + [(engine.CURSOR_SITE, engine.CURSOR_SITE + 4)] + [
    (engine.PAD_SITE, engine.PAD_SITE + 4)] + [
    (engine.FONT12, engine.FONT12 + 1691 * 24), (engine.FONT6, engine.FONT6 + engine.FONT6_COUNT * 24),
    (engine.FONT8, engine.FONT8 + 1691 * 8), engine.FREE, (0x0CD95C, 0x0D5000), (0x0D9000, 0x0DF000),
    (engine.NEW_ARCHIVE, engine.ROM_SIZE)] + (gfx.ranges(ROM.read_bytes()) if ROM.exists() else [])


@unittest.skipUnless(ROM.exists(), "no ROM dump")
class EngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
        cls.build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.build)
        cls.orig = ROM.read_bytes()
        cls.log = []
        cls.out = cls.build.build(cls.orig, marker=True, writes=cls.log)

    def test_size_and_archive_pointers(self):
        self.assertEqual(len(self.out), engine.ROM_SIZE)
        for site in archive.POINTER_SITES:
            self.assertEqual(struct.unpack_from("<I", self.out, site)[0], 0x08000000 + engine.NEW_ARCHIVE)

    def test_archive_reads_back_from_new_home(self):
        arc = archive.read(self.out, engine.NEW_ARCHIVE)
        self.assertEqual(len(arc.files), archive.NFILES)
        slot = archive.split_file(arc.files[34].raw)[10]
        self.assertTrue(slot.startswith(b"\\p\r34.10 The quick"), slot[:30])

    def test_hidden_archives_moved_and_repointed(self):
        """book / desc / effect / place are rebuilt after the script archive; every literal pool points there."""
        for spec in archive.ARCHIVES[1:]:
            if not spec.sites:
                self.assertEqual(self.out[spec.base:spec.end], self.orig[spec.base:spec.end], spec.name)
                continue
            ptrs = {struct.unpack_from("<I", self.out, s)[0] for s in spec.sites}
            self.assertEqual(len(ptrs), 1, spec.name)
            at = ptrs.pop() - 0x08000000
            self.assertGreater(at, engine.NEW_ARCHIVE, spec.name)
            first = archive.split_file(archive.read(self.out, at).files[0].raw)
            text = next(s for s in first if s is not None)
            head = sjis.fullwidth(spec.prefix + "00.") if spec.wide else spec.prefix + "00."
            self.assertTrue(text.startswith(sjis.encode(head)), (spec.name, text[:20]))

    def test_every_change_is_logged_and_allowed(self):
        logged = bytearray(len(self.out))
        for line in self.log:
            off, old, new, _ = line.split(" ", 3)
            off, old, new = int(off, 16), bytes.fromhex(old), bytes.fromhex(new)
            orig = self.orig[off:off + len(old)].ljust(len(old), b"\xff")
            self.assertEqual(old, orig, "write at %X expects other bytes" % off)
            self.assertTrue(any(lo <= off and off + len(new) <= hi for lo, hi in ALLOWED), "write at %X" % off)
            self.assertFalse(any(logged[off:off + len(new)]), "overlapping write at %X" % off)
            logged[off:off + len(new)] = b"\1" * len(new)
        orig = self.orig.ljust(len(self.out), b"\xff")
        bad = [i for i in range(0, len(self.orig)) if self.out[i] != orig[i] and not logged[i]]
        self.assertEqual(bad[:5], [], "bytes changed without a write")

    def test_vwf_widths(self):
        w = engine.widths(self.orig)
        self.assertEqual(len(w), 94)  # 0x20..0x7E, '`' shares the space glyph
        self.assertEqual(w[sjis.encode("\u3000")], engine.SPACE_ADV)
        self.assertTrue(all(1 < a <= 12 for a in w.values()))
        self.assertLess(w[sjis.encode("ｉ")], w[sjis.encode("ｍ")])

    def test_half_widths(self):
        w = engine.half_widths(self.orig)
        self.assertEqual(w[sjis.encode("　")], engine.HALF_SPACE_ADV)
        self.assertTrue(all(1 < a <= engine.HALF_ADV for a in w.values()))
        self.assertEqual(len({w[sjis.encode(sjis.fullwidth(d))] for d in "0123456789"}), 1)  # tabular digits
        self.assertLess(w[sjis.encode("ｉ")], w[sjis.encode("ｍ")])
        w8 = engine.eight_widths(self.orig)
        self.assertTrue(all(1 < a <= engine.EIGHT_ADV for a in w8.values()))
        self.assertEqual(len({w8[sjis.encode(sjis.fullwidth(d))] for d in "0123456789"}), 1)
        self.assertLess(w8[sjis.encode("ｉ")], w8[sjis.encode("ｍ")])

    def test_half_sites_call_the_hook(self):
        for site, _ in engine.HALF_SITES:
            hi, lo = struct.unpack_from("<HH", self.out, site)
            self.assertEqual((hi & 0xF800, lo & 0xF800), (0xF000, 0xF800), "site %X is not a BL" % site)

    def test_hook_free_space(self):
        end = engine.apply(bytearray(self.orig), lambda *a: None, self.orig)
        self.assertLess(end, engine.FREE[1])
