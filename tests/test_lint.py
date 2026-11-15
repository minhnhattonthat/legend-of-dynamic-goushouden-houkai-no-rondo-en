"""tools/lint.py on synthetic entries: each rule fires, a clean line passes."""
import unittest

import lint


def entry(jp, en, eid="01.02"):
    return {"id": eid, "jp": jp, "en": en, "status": "", "notes": ""}


class LintTest(unittest.TestCase):
    def errs(self, jp, en):
        errs, warns = [], []
        lint.common(entry(jp, en), errs)
        lint.lint_archive(entry(jp, en), lint.char_widths(), errs, warns)
        return errs, warns

    def test_clean(self):
        self.assertEqual(self.errs("{p}\nこんにちは\n元気？", "{p}\nHello there.\nHow are you doing?"), ([], []))

    def test_codes_and_chars(self):
        e, _ = self.errs("{p}\nあ{s}", "{p}\nHi\\ there`")
        self.assertTrue(any("control codes" in m for m in e), e)
        self.assertTrue(any("can't draw" in m for m in e), e)
        e, _ = self.errs("{p}\nあ", "{p}\nSTOP!Run")
        self.assertTrue(any("!R" in m for m in e), e)

    def test_speaker_kept(self):
        e, _ = self.errs("{p}\nあ", "Hero\nHi")
        self.assertTrue(any("speaker" in m for m in e), e)

    @unittest.skipIf(lint.char_widths() is None, "no ROM dump")
    def test_width(self):
        e, _ = self.errs("名前\nあ", "Name\n" + "W" * 40)
        self.assertTrue(any("px" in m for m in e), e)
        line = "a" * 50
        self.assertGreater(lint.line_px(line, lint.char_widths()), 184)

    @unittest.skipIf(lint.char_widths12() is None, "no ROM dump")
    def test_book_box(self):
        jp = "豪翔伝\n\n\nこの物語の主人公\n不可解なメールを"
        errs = []
        lint.lint_box(entry(jp, "Goushouden\n\n\nOur hero.\nGot an e-mail", "B00.00"), "book", errs)
        self.assertEqual(errs, [])
        errs = []
        lint.lint_box(entry(jp, "Goushouden\n\nThe hero of this tale, who got a strange e-mail\n1\n2\n3\n4\n5",
                            "B00.00"), "book", errs)
        self.assertTrue(any("blank lines" in m for m in errs), errs)
        self.assertTrue(any("px" in m for m in errs), errs)
        self.assertTrue(any("lines, the book box" in m for m in errs), errs)
        errs = []
        lint.lint_box(entry("回復", "Restores about 30 HP to one ally", "D00.00"), "desc", errs)
        self.assertEqual(errs, [])

    @unittest.skipIf(lint.char_widths8() is None, "no ROM dump")
    def test_rom_field(self):
        # a battler short name (char_short table, 0x7B31CC + 0xF0 * k) checked against the battle_name field
        e = {"id": "r0DB820", "jp": "ハニー", "max": 19, "ptrs": ["7B32BC"], "status": "", "notes": ""}
        self.assertIn("battle_name", lint.rom_boxes(e))
        errs = []
        lint.lint_rom(dict(e, en="Honey"), errs)
        self.assertEqual(errs, [])
        lint.lint_rom(dict(e, en="Tomahawk Panther"), errs)
        self.assertTrue(any("battle_name field" in m for m in errs), errs)

    def test_stub_last_line_fails(self):
        e, _ = self.errs("名前\nあ\nい", "Name\nThis is a long line\nso.")
        self.assertTrue(any("stub last line" in m for m in e), e)
        e, _ = self.errs("名前\nあ\nい", "Name\nWe will wait for\n{p}!")
        self.assertFalse(any("stub last line" in m for m in e), e)

    def test_untranslated_needs_keep_list(self):
        self.assertIn("x0D9D44", lint.keep("keep_jp.txt"))
        self.assertNotIn("r0DB820", lint.keep("keep_jp.txt"))
