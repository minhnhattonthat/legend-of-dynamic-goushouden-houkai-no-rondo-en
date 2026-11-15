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

    def test_stub_warning(self):
        _, w = self.errs("名前\nあ\nい", "Name\nThis is a long line\nso.")
        self.assertTrue(w)
