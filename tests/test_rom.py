import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba"


@unittest.skipUnless(ROM.is_file(), "no ROM dump in rom/")
class RomTest(unittest.TestCase):
    def test_dump_matches_rom_sha1(self):
        want = (ROOT / "rom.sha1").read_text(encoding="utf-8").split("\n")[1].split()[0]
        self.assertEqual(hashlib.sha1(ROM.read_bytes()).hexdigest(), want)


if __name__ == "__main__":
    unittest.main()
