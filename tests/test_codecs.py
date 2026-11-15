"""Packed-file codecs (tools/packed.py) against output the game itself produced.

The sha1 values are of blocks dumped from the emulator at 0x08000FDA by tools/lua/unpacklog.lua (work/qa/tour2).
"""
import hashlib
import unittest
from pathlib import Path

import packed

ROOT = Path(__file__).resolve().parents[1]
ROM = Path(packed.ROM)

GAME_DECODED = [  # (ROM offset, type, sha1 of the game's decoded output)
    (0x2F4F28, 1, "de8a847bff8c343d69b853a215e6ee775ef2ef96"),
    (0x56384C, 1, "1711bf60fe4c96cd3f68537e08fbaa88b5cb9f99"),
    (0x5639F0, 1, "14392a728b7518e48f31995a141d5f246cbb2cdf"),
    (0x201D64, 2, "f7c17d42d416d1231f8a206a443f6fc56b24effa"),
    (0x29DBA4, 2, "f1eef53c078e976ca575b998a8dcf10ff0b8e056"),
    (0x29DD9C, 2, "4dbf296645489e1f594770383e624ee9c0009705"),
    (0x2F8860, 3, "505314032f50d6759a4393cc95912f5d6560dada"),
    (0x2F889C, 3, "be3306b695eff5d08796466650cea8d76c656393"),
    (0x2F8AD0, 3, "b45258fffe8884c926e3593a57f9c81ff457f050"),
]


@unittest.skipUnless(ROM.is_file(), "no ROM dump in rom/")
class CodecTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.read_bytes()

    def test_decoders_match_game_output(self):
        for off, typ, sha in GAME_DECODED:
            with self.subTest(off=hex(off)):
                t, out, _ = packed.unpack(self.rom, off)
                self.assertEqual(t, typ)
                self.assertEqual(hashlib.sha1(out).hexdigest(), sha)


if __name__ == "__main__":
    unittest.main()
