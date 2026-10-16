"""Offline tests: no ComfyUI, no GPU. From ghost-comic/: py -X utf8 -m unittest tests.test_manga"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import manga  # noqa: E402

BOARD = json.loads((SKILL / "assets" / "example_board.json").read_text(encoding="utf-8"))


def texts(board):
    for _, cell, _ in manga.all_panels(board):
        for e in cell.get("text", []):
            yield cell["id"], e


class ColumnsTest(unittest.TestCase):
    def test_every_line_on_the_example_board(self):
        for pid, e in texts(BOARD):
            cols = manga.columns(e["text"], e.get("per_col", manga.PER_COL[e["kind"]]))
            for c in cols:
                self.assertFalse(c[0] in manga.NO_START, f"{pid}: column starts with punctuation: {cols}")
                self.assertFalse(c[-1] in manga.NO_END, f"{pid}: column ends with an opening bracket: {cols}")
                if len(cols) > 1:
                    self.assertGreater(len(c), 1, f"{pid}: one-character column: {cols}")

    def test_phrase_breaks_and_forced_break(self):
        join = lambda cols: " | ".join("".join(c) for c in cols)  # noqa: E731
        self.assertEqual(join(manga.columns("沒有啊……你看到什麼？", 8)), "沒有啊︙︙ | 你看到什麼︖")
        self.assertEqual(join(manga.columns("我們家電視很會反光。", 8)), "我們家電視 | 很會反光︒")  # balanced, no orphan 光
        self.assertEqual(join(manga.columns("一個人在家\n開視訊", 5)), "一個人在家 | 開視訊")
        self.assertNotIn("「", "".join(sum(manga.columns("她「看得到」", 8), [])))  # vertical forms substituted


class GeometryTest(unittest.TestCase):
    def test_cells_fit_reading_order_and_do_not_overlap(self):
        W, H = BOARD["page"]
        for page in BOARD["pages"]:
            cells = manga.page_cells(BOARD, page)
            boxes = [b for c, b in cells if "box" not in c]
            for x0, y0, x1, y1 in (b for _, b in cells):
                self.assertTrue(0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H)
            for i, a in enumerate(boxes):
                for b in boxes[i + 1:]:
                    overlap = min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])
                    self.assertFalse(overlap, f"{a} overlaps {b}")
        # rtl: page 1 row 3 reads p3 (right) then p4 (left)
        cells = dict((c["id"], b) for c, b in manga.page_cells(BOARD, BOARD["pages"][0]))
        self.assertGreater(cells["p3"][0], cells["p4"][0])
        # a stack is read top to bottom before the next cell: page 2 is p5 p6 | p7 p9 (stack) | p8
        order = [c["id"] for c, _ in manga.page_cells(BOARD, BOARD["pages"][1])]
        self.assertEqual(order, ["p5", "p6", "p7", "p9", "p8"])

    def test_gen_size(self):
        for _, _, box in manga.all_panels(BOARD):
            w, h = manga.gen_size(box)
            self.assertEqual((w % 32, h % 32), (0, 0))
            self.assertTrue(512 <= min(w, h) and max(w, h) <= 1280)


class PromptTest(unittest.TestCase):
    def test_consistency_only_where_it_applies(self):
        p = lambda pid: manga.find_panel(BOARD, pid)  # noqa: E731
        self.assertIn("living room never changes", manga.consistency(BOARD, p("p21")))  # refs panel:p19, a room panel
        self.assertIn("a head and a half shorter", manga.consistency(BOARD, p("p21")))  # the old woman is in it
        self.assertNotIn("living room", manga.consistency(BOARD, p("p11")))  # hand on a switch, no refs
        self.assertIn("hallway never changes", manga.consistency(BOARD, p("p8")))

    def test_text_only_drops_image_mentions(self):
        t = manga.text_only(BOARD, manga.find_panel(BOARD, "p6"))
        self.assertNotIn("<image", t)
        self.assertIn("bird's-nest", t)

    def test_pass_two_depends_only_on_pass_one(self):
        passes = {c["id"]: c.get("pass", 1) for _, c, _ in manga.all_panels(BOARD)}
        for _, c, _ in manga.all_panels(BOARD):
            for r in c.get("refs", []):
                if r.startswith("panel:"):
                    self.assertEqual(c.get("pass", 1), 2, f"{c['id']} uses {r} but runs in pass 1")
                    self.assertEqual(passes[r.split(":", 1)[1]], 1, f"{c['id']} depends on another pass-2 panel")
            if c.get("pip"):
                self.assertIn(c["pip"], passes)

    def test_style_options(self):
        self.assertEqual(set(BOARD["style_options"]), {"A", "B", "C"})
        self.assertIn("shonen", manga.style_text(BOARD, {"style": "A"}))
        self.assertIn("Character design reference sheet", manga.style_text(BOARD, {"style": "C"}, "sheet"))


class WorkFolderTest(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp())
        shutil.copy(SKILL / "assets" / "example_board.json", self.td / "board.json")
        manga.set_work(self.td)
        (manga.OUT / "sheets").mkdir(parents=True)
        (manga.OUT / "panels").mkdir(parents=True)
        two_views = Image.new("RGB", (1536, 1024), "white")
        two_views.paste((255, 0, 0), (0, 0, 768, 1024))  # left half red, right half white
        two_views.save(manga.OUT / "sheets" / "me_2.png")
        Image.new("RGB", (1536, 1024), (0, 0, 255)).save(manga.OUT / "sheets" / "scene_room_1.png")
        Image.new("RGB", (640, 480), "white").save(manga.OUT / "panels" / "p5_2.png")

    def tearDown(self):
        manga.set_work(Path.cwd())
        shutil.rmtree(self.td, ignore_errors=True)

    def test_choose_and_refs(self):
        ns = lambda **k: type("A", (), k)  # noqa: E731
        manga.cmd_choose(ns(picks=["style=A", "me=2", "room=1", "p5=2"]))
        ch = manga.load_choices()
        self.assertEqual(ch["style"], "A")
        self.assertEqual(ch["sheets"], {"me": "sheets/me_2.png", "scene_room": "sheets/scene_room_1.png"})
        self.assertEqual(ch["panels"]["p5"], "p5_2.png")
        with self.assertRaises(SystemExit):
            manga.cmd_choose(ns(picks=["fang=3"]))  # no such file
        manga.cmd_refs(ns())
        ref = Image.open(manga.OUT / "refs" / "me.png")
        self.assertEqual(ref.size, (768, 1024))  # one view only
        r, g, b = ref.getpixel((10, 10))
        self.assertTrue(r == g == b)  # grayscale
        self.assertEqual(Image.open(manga.OUT / "refs" / "scene_room.png").size, (1536, 1024))  # scenes are not cropped
        self.assertEqual(manga.ref_path("scene:room", manga.load_choices()), manga.OUT / "refs" / "scene_room.png")

    def test_plan_and_partial_pages_render(self):
        ns = lambda **k: type("A", (), k)  # noqa: E731
        manga.cmd_plan(ns())
        self.assertTrue((manga.OUT / "plan.png").exists())
        manga.cmd_pages(ns(pages=[2]))  # unpicked panels become labelled placeholders
        self.assertEqual(Image.open(manga.OUT / "pages" / "page_02.png").size, tuple(BOARD["page"]))


if __name__ == "__main__":
    unittest.main()
