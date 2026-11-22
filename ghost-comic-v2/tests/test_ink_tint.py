"""ink_tint.py apply/check, no GPU. Run: py -X utf8 -m unittest discover -s tests"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ink_tint  # noqa: E402

BOARD = {
    "style": "A", "mono": True,
    "style_options": {"A": {"name": "manga", "panel": "Black and white manga.", "sheet": "Manga sheet."}},
    "lights": {"night": "Night, clean white line art.", "dark": "Dark ink wash."},
    "scenes": {"s1": "A room with screentone walls."},
    "pages": [{"rows": [{"cells": [{"id": "p1", "prompt": "A girl at a window."},
                                   {"id": "p2", "prompt": "The ghost behind her."}]}]}],
}


class InkTint(unittest.TestCase):
    def setUp(self):
        self.old = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        Path("board.json").write_text(json.dumps(BOARD), encoding="utf-8")

    def tearDown(self):
        os.chdir(self.old)
        self.tmp.cleanup()

    def board(self):
        return json.loads(Path("board.json").read_text(encoding="utf-8"))

    def test_apply_sets_style_colour_and_end_sentence(self):
        ink_tint.apply()
        b = self.board()
        self.assertEqual(b["style"], ink_tint.KEY)
        self.assertTrue(b["colour"])
        self.assertFalse(b["mono"])
        self.assertIn("A", b["style_options"])  # the old options stay
        for c in ink_tint.cells(b):
            self.assertTrue(c["prompt"].endswith(ink_tint.INK + ink_tint.TINT))
        self.assertEqual(json.loads(Path("choices.json").read_text(encoding="utf-8"))["style"], ink_tint.KEY)

    def test_apply_twice_adds_the_sentence_once(self):
        ink_tint.apply()
        ink_tint.apply()
        for c in ink_tint.cells(self.board()):
            self.assertEqual(c["prompt"].count(ink_tint.END), 1)

    def test_check_finds_line_art_words_but_not_ink(self):
        n_before = ink_tint.check()
        ink_tint.apply()
        n_after = ink_tint.check()
        self.assertEqual(n_before, n_after + 2)  # style and colour fixed; lights.night and scenes.s1 remain
        self.assertEqual(n_after, 2)

    def test_style_sentence_names_no_specific_colour(self):
        # a colour example in the style sentence put red shoes on the wrong design (2026-11-21)
        for word in ("red", "gold", "pink", "blue"):
            self.assertNotIn(word, (ink_tint.INK + ink_tint.TINT).lower())


if __name__ == "__main__":
    unittest.main()
