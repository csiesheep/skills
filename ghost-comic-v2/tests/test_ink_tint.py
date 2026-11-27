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

    def test_check_wants_a_floor_plan_and_a_camera_for_a_shared_scene(self):
        b = self.board()
        for c in ink_tint.cells(b):
            c["scene"] = "s1"
        b["pages"][0]["rows"][0]["cells"].append({"id": "p3", "prompt": "A third panel.", "scene": "s1"})
        Path("board.json").write_text(json.dumps(b), encoding="utf-8")
        ink_tint.apply()
        n_no_plan = ink_tint.check()
        b = self.board()
        b["plans"] = {"s1": "plan/s1.png"}
        Path("board.json").write_text(json.dumps(b), encoding="utf-8")
        n_no_camera = ink_tint.check()          # the plan is there, the three panels have no camera
        for c in ink_tint.cells(b):
            c["camera"] = "A"
        Path("board.json").write_text(json.dumps(b), encoding="utf-8")
        n_ok = ink_tint.check()
        self.assertEqual(n_no_plan, n_ok + 1)   # one line for the missing plan
        self.assertEqual(n_no_camera, n_ok + 3)  # one line per panel without a camera

    def plan(self):
        import building_plan
        spec = json.loads((Path(__file__).resolve().parents[1] / "assets" / "example_plan_building.json").read_text(encoding="utf-8"))
        return building_plan, spec

    def test_the_example_plan_draws_and_every_camera_checks(self):
        bp, spec = self.plan()
        self.assertEqual(bp.draw(spec).size, tuple(spec["size"]))
        self.assertEqual(bp.check_sides(spec), [])

    def test_a_mirrored_plan_is_caught(self):
        bp, spec = self.plan()
        for c in spec["cameras"]:          # the entrance moved to the bottom of the page: what v4 of this plan did
            c["at"][0], c["look"][0] = 4.2 - c["at"][0], 4.2 - c["look"][0]
        self.assertTrue(any("should be on the" in b for b in bp.check_sides(spec)))

    def test_a_thing_outside_the_view_is_caught(self):
        bp, spec = self.plan()
        cam = next(c for c in spec["cameras"] if c["id"] == "A")
        cam["fov"] = 40
        self.assertTrue(any("outside" in b for b in bp.check_sides(spec)))

    def test_masters_are_one_per_camera_with_the_bible_and_the_style_last(self):
        bp, spec = self.plan()
        jobs = bp.master_jobs(spec)["jobs"]
        self.assertIn("D", jobs)
        self.assertNotIn("監1", jobs)     # a security camera has no master of its own
        self.assertIn("NO glass doors", jobs["D"]["prompt"])
        self.assertTrue(jobs["D"]["prompt"].endswith(ink_tint.INK + ink_tint.TINT))

    def test_pick_mirrors_only_a_reverse_angle(self):
        from PIL import Image
        bp, spec = self.plan()
        Path("plan.json").write_text(json.dumps(spec), encoding="utf-8")
        im = Image.new("RGB", (2, 1), (0, 0, 0))
        im.putpixel((0, 0), (255, 255, 255))
        im.save("c.png")
        old = sys.argv
        try:
            for cam, want in (("D", (0, 0, 0)), ("A", (255, 255, 255))):
                sys.argv = ["building_plan.py", "pick", "plan.json", cam, "c.png", "m.png"]
                bp.main()
                self.assertEqual(Image.open("m.png").getpixel((0, 0)), want)
        finally:
            sys.argv = old


if __name__ == "__main__":
    unittest.main()
