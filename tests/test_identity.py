"""Identity build (phase 3): unpack + repack with no edits gives the original ROM byte for byte, and the lh5
encoder round-trips every script-archive file (so an edited file can be repacked)."""
import struct
import unittest
from pathlib import Path

import archive
import lh5

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba"


@unittest.skipUnless(ROM.is_file(), "no ROM dump in rom/")
class IdentityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
        cls.build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.build)
        cls.rom = ROM.read_bytes()
        cls.arc = archive.read(cls.rom)

    def test_build_is_byte_identical(self):
        self.assertTrue(self.build.identity(self.rom) == self.rom)

    def test_reencoded_build_reads_back(self):
        out = self.build.identity(self.rom, reencode=True)
        self.assertNotEqual(out, self.rom)
        back = archive.read(out)
        self.assertEqual([f.raw for f in back.files], [f.raw for f in self.arc.files])

    def test_archive_rebuild_is_identical(self):
        self.assertEqual(self.arc.build(), self.rom[archive.BASE:archive.END])

    def test_archive_pointer_sites(self):
        for site in archive.POINTER_SITES:
            self.assertEqual(struct.unpack_from("<I", self.rom, site)[0], 0x08000000 | archive.BASE, hex(site))

    def test_slots_roundtrip(self):
        for i, f in enumerate(self.arc.files):
            with self.subTest(file=i):
                self.assertEqual(archive.join_file(archive.split_file(f.raw)), f.raw)

    def test_lh5_encoder_roundtrip(self):
        """Every file re-encoded, decoded back; also an edited archive (all files re-encoded) still reads back."""
        total_new = total_old = 0
        for i, f in enumerate(self.arc.files):
            with self.subTest(file=i):
                enc = lh5.encode(f.raw)
                out, used = lh5.decode(enc, 0, len(f.raw))
                self.assertEqual(out, f.raw)
                self.assertEqual(used, len(enc))
                total_new += len(enc)
                total_old += len(f.stream)
        self.assertLess(total_new, total_old * 1.10, "encoder ratio far worse than the original packer")

    def test_graphics_repack_as_lh5(self):
        """Edited graphics get repacked as type 2 (unpack() at 0x08000F58 dispatches on the header type)."""
        import packed
        from tests.test_codecs import GAME_DECODED
        for off, typ, _ in GAME_DECODED:
            with self.subTest(off=hex(off)):
                _, raw, _ = packed.unpack(self.rom, off)
                blob = lh5.pack(raw)
                t, back, used = packed.unpack(blob, 0)
                self.assertEqual((t, back, used), (2, raw, len(blob)))

    def test_lh5_edge_cases(self):
        for raw in (b"", b"A", b"AB", b"\0" * 5000, bytes(range(256)) * 3, b"ab" * 40000):
            with self.subTest(n=len(raw)):
                self.assertEqual(lh5.decode(lh5.encode(raw), 0, len(raw))[0], raw)


if __name__ == "__main__":
    unittest.main()
