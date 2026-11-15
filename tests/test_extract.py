"""Extraction (phase 4): every string re-encodes to its original bytes, script/ matches the ROM, the text ranges
are fully covered, and translated text reaches the built ROM."""
import random
import re
import unittest
from pathlib import Path

import archive
import extract
import romstr
import sjis

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba"
KANA = re.compile(r"[ぁ-ヿ]")

# SJIS-looking runs outside the text ranges that are not text, with the reason
OUTSIDE_WAIVE = {
    0x1F0CD8: "font charset list (docs/re/font.md), read by the glyph renderer, not drawn as a string",
    0x520422: "bytes inside packed graphics",
}


class CodecTest(unittest.TestCase):
    def test_random_bytes_roundtrip(self):
        rnd = random.Random(4)
        for _ in range(2000):
            b = bytes(rnd.choice(b"\x0d\x21\x52\x57\x5c\x70\x73\x67\x5b\x7b\x82\xa0\x83\x88\x9f\xe0\xfc\x40\x00\x80\xff")
                      for _ in range(rnd.randrange(1, 12)))
            self.assertEqual(sjis.encode(sjis.decode(b)), b, b.hex())

    def test_forms(self):
        self.assertEqual(sjis.decode(b"\x82\xa0\\p!R\r[A]"), "あ{p}{!R}\n[5B]A[5D]")
        self.assertEqual(sjis.encode("Hi {s}!\nOK"), b"Hi \\s!\rOK")
        self.assertRaises(ValueError, sjis.encode, "a[b")
        self.assertRaises(ValueError, sjis.encode, "\u00e9")  # no Shift-JIS code: caught at build time


@unittest.skipUnless(ROM.is_file(), "no ROM dump in rom/")
class ExtractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.read_bytes()
        cls.entries = extract.all_entries(cls.rom)

    def test_archive_slots_roundtrip(self):
        n = 0
        for f in archive.read(self.rom).files:
            for s in archive.split_file(f.raw):
                if s is not None:
                    self.assertEqual(sjis.encode(sjis.decode(s[:-1])) + b"\0", s)
                    n += 1
        self.assertEqual(n, 5363)

    def test_every_message_id_lands_on_a_slot(self):
        ids = [m for name, es in self.entries.items() if name.startswith("archive/") for e in es for m in e["msg"]]
        self.assertEqual(len(ids), 5363)
        self.assertEqual(len(set(ids)), 5363)

    def test_rom_strings_roundtrip(self):
        for name, es in self.entries.items():
            if not name.startswith("rom/"):
                continue
            for e in es:
                off, b = int(e["id"][1:], 16), sjis.encode(e["jp"])
                self.assertEqual(self.rom[off:off + len(b) + 1], b + b"\0", e["id"])
                self.assertLessEqual(len(b), e["max"], e["id"])
                self.assertFalse(any(self.rom[off + len(b):off + e["max"] + 1]), e["id"] + ": room not zero")

    def test_script_dir_matches_rom(self):
        files = set(extract.script_files())
        self.assertEqual(files, set(self.entries), "run tools/extract.py dump")
        for name, es in self.entries.items():
            got = extract.load(name)
            self.assertEqual([(e["id"], e["jp"]) for e in got], [(e["id"], e["jp"]) for e in es], name)
            for e, g in zip(es, got):
                if e["status"] == "data":
                    self.assertEqual(g["status"], "data", e["id"] + ": non-text, run extract.py dump --force")
                self.assertEqual({k: g[k] for k in ("msg", "ptrs", "rec", "max") if k in e},
                                 {k: e[k] for k in ("msg", "ptrs", "rec", "max") if k in e}, e["id"])

    def covered(self):
        cov = bytearray(len(self.rom))
        for name, es in self.entries.items():
            for e in es:
                if name.startswith("rom/"):
                    off = int(e["id"][1:], 16)
                    cov[off:off + e["max"] + 1] = b"\1" * (e["max"] + 1)
        return cov

    def test_text_ranges_fully_covered(self):
        """Inside the string sections: no kana/kanji run (any alignment) outside an extracted string, and every
        pointed string candidate is extracted."""
        cov = self.covered()
        for lo, hi in romstr.TEXT_RANGES:
            self.assertEqual(romstr.jp_runs(self.rom, lo, hi, cov), [], "text left out of script/rom")
        ids = {e["id"] for name, es in self.entries.items() for e in es}
        ptrs = romstr.pointers(self.rom)
        for s, e, wide, sites in romstr.scan(self.rom, ptrs):
            if any(lo <= s < hi for lo, hi in romstr.TEXT_RANGES) and sites:
                self.assertIn("r%06X" % s, ids)

    def test_no_text_outside_the_ranges(self):
        """Outside the string sections and the archive: no pointed string with 2+ kana and no unpointed one with
        4+, except the waived non-text hits. (Kana only: random bytes form kanji pairs far more often.)"""
        hits = []
        for s, e, wide, sites in romstr.scan(self.rom, romstr.pointers(self.rom)):
            if any(lo <= s < hi for lo, hi in romstr.TEXT_RANGES) or archive.BASE <= s < archive.END:
                continue
            k = len(KANA.findall(sjis.decode(self.rom[s:e])))
            if k >= 2 and (sites or k >= 4) and s not in OUTSIDE_WAIVE:
                hits.append("%06X" % s)
        self.assertEqual(hits, [])


@unittest.skipUnless(ROM.is_file(), "no ROM dump in rom/")
class InsertTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
        cls.build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.build)
        cls.rom = ROM.read_bytes()

    def test_english_reaches_the_rom(self):
        arc = archive.read(self.rom)
        texts = {fi: {j: sjis.decode(s[:-1]) for j, s in enumerate(archive.split_file(f.raw)) if s is not None}
                 for fi, f in enumerate(arc.files)}
        texts[0][1] = "\nYou got {g}!"
        self.build.insert_archive(arc, texts)
        for f in arc.files:  # the original archive has no slack; our encoder frees 121 bytes over all files
            f.orig_raw = None
        out = bytearray(self.rom)
        self.build.put_archive_inplace(out, arc)
        self.build.insert_rom_strings(out, [(0x0DAFFC, 15, "Shaft's son", True), (0x0D9D44, 19, "Whoosh", True)])
        back = archive.split_file(archive.read(bytes(out)).files[0].raw)
        self.assertEqual(back[1], b"\rYou got \\g!\0")
        self.assertEqual(out[0x0DAFFC:0x0DAFFC + 16], b"Shaft's son" + bytes(5))
        self.assertEqual(out[0x0D9D44:0x0D9D44 + 20], b"Whoosh" + bytes(14))
        self.assertRaises(SystemExit, self.build.insert_rom_strings, out, [(0x0DAFFC, 15, "x" * 16, True)])
