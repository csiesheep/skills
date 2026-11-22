"""Offline tests for scripts/from_screenplay.py. From ghost-comic/: py -X utf8 -m unittest tests.test_from_screenplay"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import from_screenplay as fs  # noqa: E402
import manga  # noqa: E402

SP = fs.parse((SKILL / "assets" / "example_v3_screenplay.md").read_text(encoding="utf-8"))


class ParseTest(unittest.TestCase):
    def test_header_cast_and_jokes(self):
        self.assertEqual(SP["head"]["最大畫面"], "1:55")
        self.assertEqual(len(SP["jokes"]), 4)
        names = {c["name"]: c for c in SP["cast"]}
        self.assertTrue(names["工作人員"]["voice_only"])
        self.assertTrue(names["她"]["ghost"])
        self.assertFalse(names["阿哲"]["ghost"])
        self.assertEqual(len(SP["scenes"]), 9)
        self.assertEqual(len(SP["rules"]), 3)


class SpeakerTest(unittest.TestCase):
    """vet_night_xray (2026-11-22): an intercom line was lettered as speech, and ids c2/c3/c5 were hard to keep apart."""

    def test_id_who_and_device_lines(self):
        text = (SKILL / "assets" / "example_v3_screenplay.md").read_text(encoding="utf-8")
        text = text.replace("- **阿哲**", "- **阿哲（zhe）**", 1)
        sp = fs.parse(text)
        self.assertIn("zhe", [c["id"] for c in sp["cast"]])
        self.assertIn("阿哲", [c["name"] for c in sp["cast"]])
        board, _ = fs.build(sp, "../story.md", 3, 5)
        self.assertIn("zhe", board["characters"])
        lines = [e for pg in board["pages"] for r in pg["rows"] for c in r["cells"] for e in c["text"]]
        said = [e for e in lines if e["kind"] in ("speech", "voice")]
        self.assertTrue(said and all(e.get("who") in board["characters"] for e in said if e.get("who")))
        self.assertTrue(any(e.get("who") == "zhe" for e in said))
        self.assertTrue(fs.DEVICE.search("對講機") and fs.DEVICE.search("電話裡") and not fs.DEVICE.search("小聲"))


class BoardTest(unittest.TestCase):
    def setUp(self):
        self.board, self.brief = fs.build(SP, "../story.md", 3, 5)
        self.cells = [c for pg in self.board["pages"] for r in pg["rows"] for c in r["cells"]]

    def test_characters_and_reveal(self):
        self.assertEqual(set(self.board["characters"]), {"me", "c2", "c3", "ghost"})  # the voice-only staff has no sheet
        self.assertTrue(self.board["characters"]["ghost"]["ghost"])
        rev = [c for c in self.cells if c.get("reveal")]
        self.assertEqual(len(rev), 1)
        self.assertIn("下巴", rev[0]["label"])
        first_of_page = [r["cells"][0]["id"] for pg in self.board["pages"][:1] for r in pg["rows"][:1]]
        self.assertTrue(first_of_page)
        self.assertEqual(self.brief["reveal_panel"], rev[0]["id"])

    def test_every_panel_is_unfinished_and_unique(self):
        ids = [c["id"] for c in self.cells]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(c["todo"] and c["prompt"] == "" for c in self.cells))

    def test_no_page_of_one_row_of_columns(self):
        for pg in self.board["pages"]:
            if len(pg["rows"]) == 1:
                self.assertEqual(len(pg["rows"][0]["cells"]), 1)
            self.assertAlmostEqual(sum(r["h"] for r in pg["rows"]), 1.0, places=2)
            for r in pg["rows"]:
                self.assertAlmostEqual(sum(c["w"] for c in r["cells"]), 1.0, places=2)

    def test_jokes_land_in_panels_and_overlays_are_not_panels(self):
        ids = {c["id"] for c in self.cells}
        for j in self.brief["jokes"]:
            self.assertIn(j["panel"], ids)
        self.assertEqual(self.brief["hook_line"], "我開的是單人卡丁車")
        self.assertTrue(self.brief["overlays"])
        self.assertFalse(any(c["label"].startswith("疊字") for c in self.cells))

    def test_lint_refuses_a_skeleton(self):
        errors = [m for _, lvl, m in manga.lint(self.board) if lvl == "error"]
        self.assertTrue(any("TODO" in m for m in errors))
        self.assertTrue(any("todo" in m for m in errors))


class CliTest(unittest.TestCase):
    def test_writes_files_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "film").mkdir()
            shutil.copy(SKILL / "assets" / "example_v3_screenplay.md", d / "film" / "screenplay.md")
            argv = sys.argv
            try:
                sys.argv = ["from_screenplay.py", str(d)]
                fs.main()
                self.assertTrue((d / "comic" / "board.json").exists())
                self.assertTrue((d / "comic" / "brief.md").exists())
                json.loads((d / "comic" / "brief.json").read_text(encoding="utf-8"))
                with self.assertRaises(SystemExit):
                    fs.main()
            finally:
                sys.argv = argv


if __name__ == "__main__":
    unittest.main()
