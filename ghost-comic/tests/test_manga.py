"""Offline tests: no ComfyUI, no GPU. From ghost-comic/: py -X utf8 -m unittest tests.test_manga"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

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
        _figure_sheet().save(manga.OUT / "sheets" / "me_2.png")
        manga.cmd_refs(ns())
        ref = Image.open(manga.OUT / "refs" / "me.png")
        self.assertEqual(ref.size, (768, 1024))  # one view only
        ch = manga.load_choices()
        self.assertEqual(ch["refs"]["me:head"], "refs/me_head.png")
        head = Image.open(manga.OUT / "refs" / "me_head.png")
        self.assertLess(head.height, 400)
        self.assertEqual(manga.ref_path("me:head", ch), manga.OUT / "refs" / "me_head.png")
        self.assertEqual(manga.ref_path("me:full", ch), manga.OUT / "refs" / "me.png")
        with self.assertRaises(SystemExit):
            manga.ref_path("fang:head", ch)  # never cropped
        r, g, b = ref.getpixel((10, 10))
        self.assertTrue(r == g == b)  # grayscale
        self.assertEqual(Image.open(manga.OUT / "refs" / "scene_room.png").size, (1536, 1024))  # scenes are not cropped
        self.assertEqual(manga.ref_path("scene:room", manga.load_choices()), manga.OUT / "refs" / "scene_room.png")

    def test_fill_panel_and_voice_bubble(self):
        b = json.loads((self.td / "board.json").read_text(encoding="utf-8"))
        cell = b["pages"][0]["rows"][2]["cells"][1]  # p4
        cell["fill"] = "black"
        cell["text"] = [{"kind": "voice", "text": "……林志偉。", "pos": "mc"}]
        (self.td / "board.json").write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8")
        ns = lambda **k: type("A", (), k)  # noqa: E731
        manga.cmd_pages(ns(pages=[1]))
        im = Image.open(manga.OUT / "pages" / "page_01.png").convert("L")
        box = dict((c["id"], bx) for c, bx in manga.page_cells(b, b["pages"][0]))["p4"]
        self.assertLess(im.getpixel((box[0] + 20, box[3] - 20)), 20)  # the fill is black, not a placeholder
        center = im.crop(box).resize((40, 40)).getpixel((20, 20))
        self.assertIsInstance(center, int)
        passes = [c["id"] for _, c, _ in manga.all_panels(b) if c.get("fill")]
        self.assertEqual(passes, ["p4"])

    def test_plan_and_partial_pages_render(self):
        ns = lambda **k: type("A", (), k)  # noqa: E731
        manga.cmd_plan(ns())
        self.assertTrue((manga.OUT / "plan.png").exists())
        manga.cmd_pages(ns(pages=[2]))  # unpicked panels become labelled placeholders
        self.assertEqual(Image.open(manga.OUT / "pages" / "page_02.png").size, tuple(BOARD["page"]))


def _figure_sheet() -> Image.Image:
    """A two-view sheet: on the left, a head (circle) over a body (rectangle) on white."""
    im = Image.new("RGB", (1536, 1024), "white")
    d = ImageDraw.Draw(im)
    d.ellipse([324, 100, 444, 220], fill="black")
    d.rectangle([300, 230, 468, 950], fill="black")
    d.rectangle([1000, 100, 1100, 950], fill="black")  # the second view, which `refs` drops
    return im


class CropTest(unittest.TestCase):
    def test_figure_crops_frame_the_head_and_bust(self):
        single = _figure_sheet().crop((0, 0, 768, 1024))
        boxes = manga.figure_crops(single)
        hx0, hy0, hx1, hy1 = boxes["head"]
        self.assertTrue(hx0 <= 324 and hx1 >= 444 and hy0 <= 100 and hy1 >= 220, boxes["head"])  # the whole head
        self.assertLess(hy1, 400)  # and not the legs
        bx0, by0, bx1, by1 = boxes["bust"]
        self.assertGreater(by1 - by0, hy1 - hy0)
        self.assertLess(by1, 700)
        self.assertEqual(manga.figure_crops(single, {"head": [0, 0, 0.5, 0.5]})["head"], (0, 0, 384, 512))

    def test_char_ref_and_cast(self):
        self.assertEqual(manga.char_ref(BOARD, "me:head"), ("me", "head"))
        self.assertEqual(manga.char_ref(BOARD, "me"), ("me", "full"))
        self.assertIsNone(manga.char_ref(BOARD, "scene:room"))
        with self.assertRaises(SystemExit):
            manga.char_ref(BOARD, "me:feet")
        p25 = manga.find_panel(BOARD, "p25")  # me and the dog
        self.assertEqual(manga.cast(BOARD, p25), ["me", "dog"])
        self.assertEqual(manga.people(BOARD, p25), ["me"])  # animals are not head-counted
        self.assertEqual(manga.cast(BOARD, manga.find_panel(BOARD, "p30")), [])  # explicit cast wins


class PromptCompositionTest(unittest.TestCase):
    def _board(self, **cell):
        b = json.loads(json.dumps(BOARD))
        c = b["pages"][0]["rows"][1]["cells"][0]  # p2
        c.update(cell)
        return b, c

    def test_explicit_scene_beats_inference(self):
        b, c = self._board(scene="hall")
        self.assertIn("hallway never changes", manga.consistency(b, c))
        self.assertNotIn("living room never changes", manga.consistency(b, c))
        c.pop("scene")
        self.assertNotIn("never changes", manga.consistency(b, c))  # other panels set scene, so no guessing here

    def test_legacy_inference_when_no_panel_sets_scene(self):
        b = json.loads(json.dumps(BOARD))
        for _, c, _ in manga.all_panels(b):
            c.pop("scene", None)
        b["consistency"]["scene_refs"] = {"room": ["scene:room"]}
        self.assertIn("living room never changes", manga.consistency(b, manga.find_panel(b, "p6")))
        self.assertTrue(any("inferred" in m for _, _, m in manga.lint(b)))

    def test_light_state_is_appended(self):
        b, c = self._board(light="morning")
        prompt = manga.compose_prompt(b, {"style": "A"}, c)
        self.assertTrue(prompt.startswith(b["style_options"]["A"]["panel"][:30]))
        self.assertIn("Bright morning", prompt)
        self.assertLess(prompt.index(c["prompt"][:30]), prompt.index("Bright morning"))
        c["light"] = "dusk"
        with self.assertRaises(SystemExit):
            manga.compose_prompt(b, {"style": "A"}, c)


class LintTest(unittest.TestCase):
    def test_example_board_has_no_errors(self):
        errors = [x for x in manga.lint(BOARD) if x[1] == "error"]
        self.assertEqual(errors, [])

    def test_each_rule_fires(self):
        b = json.loads(json.dumps(BOARD))
        c = b["pages"][0]["rows"][1]["cells"][0]  # p2, pass 1
        def msgs(**cell):
            c.clear()
            c.update({"id": "p2", "w": 1.0, "refs": [], "prompt": "", "text": []}, **cell)
            return [(lvl, m) for pid, lvl, m in manga.lint(b) if pid == "p2"]
        def has(found, lvl, needle):
            return any(l == lvl and needle in m for l, m in found)
        self.assertTrue(has(msgs(refs=["me"], prompt="Full body: the man from <image1> with his arms crossed."), "error", "extra hands"))
        self.assertFalse(has(msgs(refs=["me"], prompt="Waist-up: the man from <image1>, arms crossed. Only one person in the frame."), "error", "extra hands"))
        self.assertTrue(has(msgs(refs=["panel:p20"], prompt="As in <image1>."), "error", "later pass"))  # p20 is pass 2
        self.assertTrue(has(msgs(refs=["me"], prompt="As in <image2>."), "error", "<image2>"))
        self.assertTrue(has(msgs(refs=["me", "scene:room"], prompt="The man from <image1>."), "warn", "never mentioned"))
        self.assertTrue(has(msgs(refs=["me"], prompt="Close-up of the man from <image1>. Only one person in the frame."), "warn", "me:head"))
        self.assertTrue(has(msgs(refs=["me"], prompt="The man from <image1> stands by a wall of bamboo."), "warn", "one character"))
        found = msgs(refs=[], prompt="A wall of bamboo, a red sign, dim light, his reflection, about to sit.")
        for needle in ("wall of", "sign", "dim", "red", "about to", "reflection"):
            self.assertTrue(any(needle in m for _, m in found), needle)
        self.assertFalse(any("sign" in m for _, m in msgs(prompt="No signs, no menus, no writing anywhere.")))
        self.assertFalse(any("dim" in m for _, m in msgs(prompt="A dim room drawn in solid flat black.")))
        self.assertTrue(has(msgs(light="dusk", prompt="x"), "error", "dusk"))
        self.assertTrue(has(msgs(scene="attic", prompt="x"), "error", "attic"))
        self.assertTrue(has(msgs(refs=["me"], prompt="A man from <image1>. Only one person in the frame."), "warn", "features"))
        self.assertTrue(has(msgs(refs=["me:head", "scene:room"], prompt="Close-up of the man from <image1> in the room from <image2>. Only one person in the frame."), "warn", "scene reference"))


class RedrawNumberingTest(unittest.TestCase):
    """A redraw once overwrote p31_1..3, including the candidate already picked for page 6."""

    def test_redraw_numbers_after_existing_candidates(self):
        td = Path(tempfile.mkdtemp())
        try:
            for k in (1, 2, 3, 10):
                Image.new("RGB", (8, 8), "white").save(td / f"p31_{k}.png")
            Image.new("RGB", (8, 8), "white").save(td / "p3_1.png")  # another panel's prefix must not count
            self.assertEqual([f.name for f in manga.candidates(td, "p31")], ["p31_1.png", "p31_2.png", "p31_3.png", "p31_10.png"])
            saved = []
            orig = (manga.comfy.upload, manga.comfy.build_graph, manga.comfy.run, manga.comfy.fetch, manga.log)
            manga.comfy.upload = lambda p: p.name
            manga.comfy.build_graph = lambda *a, **k: {}
            manga.comfy.run = lambda g: ("pid", [{"filename": "x"}, {"filename": "y"}], 0.0, 0.0)
            manga.comfy.fetch = lambda img, dest: (saved.append(dest.name), Image.new("RGB", (8, 8)).save(dest))
            manga.log = lambda rec: None
            try:
                files = manga.job("panels", "p31", "x", [], 64, 64, 2, 1, td)
            finally:
                manga.comfy.upload, manga.comfy.build_graph, manga.comfy.run, manga.comfy.fetch, manga.log = orig
            self.assertEqual(files, ["p31_11.png", "p31_12.png"])
            self.assertEqual(saved, files)
        finally:
            shutil.rmtree(td, ignore_errors=True)


class ReviewTest(unittest.TestCase):
    def test_brief_lists_heads_features_and_candidates(self):
        td = Path(tempfile.mkdtemp())
        try:
            shutil.copy(SKILL / "assets" / "example_board.json", td / "board.json")
            manga.set_work(td)
            (manga.OUT / "panels").mkdir(parents=True)
            for k in (1, 2):
                Image.new("RGB", (64, 64), "white").save(manga.OUT / "panels" / f"p25_{k}.png")
            ns = lambda **k: type("A", (), k)  # noqa: E731
            manga.cmd_review(ns(ids=["p25"], page=None, unpicked=False, name="t"))
            md = (manga.OUT / "review" / "t.md").read_text(encoding="utf-8")
            self.assertIn("剛好 1 人", md)
            self.assertIn("動物：狗", md)
            self.assertIn("鳥窩頭", md)
            self.assertIn("p25_1.png", md)
            self.assertIn("p25_2.png", md)
            manga.cmd_review(ns(ids=[], page=4, unpicked=False, name=None))
            self.assertTrue((manga.OUT / "review" / "page4.md").exists())
        finally:
            manga.set_work(Path.cwd())
            shutil.rmtree(td, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
