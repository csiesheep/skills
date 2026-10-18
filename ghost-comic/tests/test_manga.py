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


def _tiny(cells_by_page, **chars):
    """A board of one row per page, for rules that need control over who appears where."""
    return {"page": [1200, 1700], "margin": 56, "gutter": [18, 24], "direction": "rtl",
            "characters": {k: dict({"keywords": []}, **v) for k, v in chars.items()},
            "scenes": {"room": "A living room. Nobody in it."},
            "consistency": {"scene": {"room": "Scene consistency: the living room never changes."}}, "lights": {},
            "pages": [{"rows": [{"h": 1.0, "cells": [dict({"w": 1 / len(cs), "refs": [], "prompt": "x", "text": []}, **c) for c in cs]}]}
                      for cs in cells_by_page]}


class LintThirdComicTest(unittest.TestCase):
    """Rules from 〈跟外甥玩捉迷藏〉."""

    def _hits(self, board, needle, pid=None):
        return [(p, lvl) for p, lvl, m in manga.lint(board) if needle in m and (pid is None or p == pid)]

    def test_head_crop_with_a_frightened_face(self):
        b = _tiny([[{"id": "p1", "refs": ["er:head"], "prompt": "The boy from <image1>, faces gone pale, staring. Only one person in the frame."}]],
                  er={"name": "老二"})
        self.assertEqual(self._hits(b, "head crop"), [("p1", "warn")])
        b["pages"][0]["rows"][0]["cells"][0]["refs"] = ["er:bust"]
        self.assertEqual(self._hits(b, "head crop"), [])
        b["pages"][0]["rows"][0]["cells"][0].update(refs=["er:head"], prompt="The boy from <image1> grins. Only one person in the frame.")
        self.assertEqual(self._hits(b, "head crop"), [])

    def test_seated_with_a_scene_reference(self):
        b = _tiny([[{"id": "p1", "refs": ["me:bust", "scene:room"], "prompt": "In the room from <image2>: the man from <image1> sits on the sofa. Only one person in the frame."}]],
                  me={"name": "我"})
        self.assertEqual(self._hits(b, "seated on furniture"), [("p1", "warn")])
        c = b["pages"][0]["rows"][0]["cells"][0]
        c.update(refs=["me:bust"], prompt="The man from <image1> sits deep on a long wooden sofa, its backrest behind him. Only one person in the frame.")
        self.assertEqual(self._hits(b, "seated on furniture"), [])

    def test_first_appearance_must_be_named(self):
        ama = {"id": "p2", "refs": ["ama:bust"], "prompt": "The grandmother from <image1>. Only one person in the frame.",
               "text": [{"kind": "speech", "text": "那應該是恁細姑……", "pos": "tr"}]}
        later = {"id": "p3", "refs": [], "prompt": "x", "text": [{"kind": "narration", "text": "隔天我媽跟我講了阿嬤沒講的部分。", "pos": "tr"}]}
        b = _tiny([[{"id": "p1"}], [ama, later]], ama={"name": "阿嬤"})
        self.assertEqual(self._hits(b, "first drawn"), [("p2", "warn")])  # named later on the same page is not enough
        ama["text"].insert(0, {"kind": "narration", "text": "阿嬤聽完愣了很久，說：", "pos": "tr"})
        self.assertEqual(self._hits(b, "first drawn"), [])
        ama["text"].pop(0)
        b["characters"]["ama"]["intro"] = "p3"  # a panel on the same page that names her
        self.assertEqual(self._hits(b, "first drawn"), [])
        b["characters"]["ama"]["intro"] = "p1"  # on another page: still unnamed where she is drawn
        self.assertEqual(self._hits(b, "first drawn"), [("p2", "warn")])
        b["characters"]["ama"]["intro"] = "p9"
        self.assertEqual(self._hits(b, "intro panel"), [("p2", "error")])
        b["characters"]["ama"] = {"name": "阿嬤", "keywords": [], "ghost": True}  # the ghost stays unnamed on purpose
        self.assertEqual(self._hits(b, "first drawn"), [])
        b["characters"]["ama"] = {"name": "外婆", "aliases": ["阿嬤"], "keywords": []}
        b["characters"]["ama"]["intro"] = "p3"
        self.assertEqual(self._hits(b, "first drawn"), [])
        self.assertEqual(manga.character_names({"characters": {"me": {"name": "我（舅舅）"}}}, "me"), ["我", "舅舅"])

    def test_zoom_range(self):
        b = _tiny([[{"id": "p1", "zoom": 1.5}]])
        self.assertEqual(self._hits(b, "zoom"), [("p1", "error")])


class LayoutToolsTest(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp())
        manga.set_work(self.td)
        (manga.OUT / "panels").mkdir(parents=True)

    def tearDown(self):
        manga.set_work(Path.cwd())
        shutil.rmtree(self.td, ignore_errors=True)

    def test_mirror_and_zoom(self):
        im = Image.new("RGB", (100, 80), "black")
        ImageDraw.Draw(im).rectangle([50, 0, 99, 79], fill="white")  # right half white
        im.save(manga.OUT / "panels" / "p1_1.png")
        ch = {"panels": {"p1": "p1_1.png"}}
        self.assertEqual(manga.panel_source({"id": "p1"}, ch).getpixel((90, 40)), (255, 255, 255))
        self.assertEqual(manga.panel_source({"id": "p1", "mirror": True}, ch).getpixel((90, 40)), (0, 0, 0))
        z = manga.panel_source({"id": "p1", "zoom": 0.5, "zoom_at": [1, 1]}, ch)
        self.assertEqual(z.size, (100, 80))
        self.assertEqual(z.getpixel((10, 10)), (0, 0, 0))  # the freed corner takes the background colour
        self.assertEqual(z.getpixel((95, 75)), (255, 255, 255))  # the picture, shrunk into the bottom-right corner
        self.assertEqual(Image.open(manga.OUT / "panels" / "p1_1.png").getpixel((90, 40)), (255, 255, 255))  # file untouched

    def test_lettering_that_covers_lettering_is_reported(self):
        b = _tiny([[{"id": "p1", "text": [{"kind": "speech", "text": "……九十九、一百！", "pos": "tl"},
                                           {"kind": "narration", "text": "老二數到五十就偷看。", "pos": "tl"}]}]])
        issues = []
        manga.render_page(b, b["pages"][0], 1, {"panels": {}}, wireframe=True, issues=issues)
        self.assertEqual(len(issues), 1)
        self.assertIn("p1", issues[0])
        b["pages"][0]["rows"][0]["cells"][0]["text"][0]["pos"] = "tr"
        issues = []
        manga.render_page(b, b["pages"][0], 1, {"panels": {}}, wireframe=True, issues=issues)
        self.assertEqual(issues, [])
        issues = []
        for pi, page in enumerate(BOARD["pages"], 1):  # the example board letters cleanly
            manga.render_page(BOARD, page, pi, {"panels": {}}, wireframe=True, issues=issues)
        self.assertEqual(issues, [])


class ReviewThirdComicTest(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp())
        shutil.copy(SKILL / "assets" / "example_board.json", self.td / "board.json")
        manga.set_work(self.td)
        (manga.OUT / "panels").mkdir(parents=True)
        self.ns = lambda **k: type("A", (), dict({"ids": [], "page": None, "unpicked": False, "name": None, "new": False, "read": False}, **k))  # noqa: E731

    def tearDown(self):
        manga.set_work(Path.cwd())
        shutil.rmtree(self.td, ignore_errors=True)

    def _png(self, name):
        Image.new("RGB", (64, 64), "white").save(manga.OUT / "panels" / name)

    def test_new_lists_only_unreviewed_candidates(self):
        self._png("p25_1.png")
        self._png("p25_2.png")
        manga.cmd_review(self.ns(ids=["p25"], name="first"))
        self._png("p25_3.png")
        manga.cmd_review(self.ns(ids=["p25"], name="redraw", new=True))
        md = (manga.OUT / "review" / "redraw.md").read_text(encoding="utf-8")
        self.assertIn("p25_3.png", md)
        self.assertNotIn("p25_1.png", md)
        with self.assertRaises(SystemExit):  # nothing newer than the two briefs
            manga.cmd_review(self.ns(ids=["p25"], name="again", new=True))

    def test_brief_shows_picked_panels_to_match(self):
        self._png("p6_1.png")
        self._png("p7_1.png")
        manga.save_choices({"panels": {"p6": "p6_1.png"}})
        manga.cmd_review(self.ns(ids=["p7"], name="t"))  # p6 and p7 are both in the room
        md = (manga.OUT / "review" / "t.md").read_text(encoding="utf-8")
        self.assertIn("要跟這些已選定的格子接得上", md)
        self.assertIn("p6_1.png", md)
        b = manga.load_board()
        self.assertEqual([c["id"] for c in manga.continuity_panels(b, manga.load_choices(), manga.find_panel(b, "p8"))], [])  # the hall

    def test_reader_brief_has_pages_and_no_story(self):
        with self.assertRaises(SystemExit):
            manga.cmd_review(self.ns(read=True))  # no pages yet
        (manga.OUT / "pages").mkdir()
        for k in (1, 2):
            Image.new("RGB", (60, 85), "white").save(manga.OUT / "pages" / f"page_0{k}.png")
        manga.cmd_review(self.ns(read=True))
        read = (manga.OUT / "review" / "read.md").read_text(encoding="utf-8")
        self.assertIn("page_01.png", read)
        self.assertIn("page_02.png", read)
        self.assertIn("由右往左", read)
        self.assertNotIn("小芳", read)  # the reader gets no names, no story
        key = (manga.OUT / "review" / "read_key.md").read_text(encoding="utf-8")
        self.assertIn("小芳", key)
        self.assertIn("一個人在家", key)  # the title's lettering, in reading order

    def test_status(self):
        import contextlib
        import io
        self._png("p25_1.png")
        manga.save_choices({"panels": {"p1": "p1_1.png"}, "style": "A"})
        manga.log({"kind": "panels", "id": "p1", "wall_s": 90, "files": ["p1_1.png", "p1_2.png"]})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            manga.cmd_status(self.ns())
        out = buf.getvalue()
        self.assertIn("page 1: 1/", out)
        self.assertIn("p25(1)", out)
        self.assertIn("panels 1.5 min", out)
        self.assertIn("2 images", out)
        manga.log({"kind": "panels", "id": "p2", "wall_s": 300, "exec_s": 60, "files": ["p2_1.png"]})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            manga.cmd_status(self.ns())
        out = buf.getvalue()
        self.assertIn("panels 2.5 min", out)  # 1.5 (no exec_s logged) + 1.0 exec, not the 5 min spent in the queue
        self.assertIn("6.5 min with queue waits", out)


class FifthComicTest(unittest.TestCase):
    """Tools from 〈阿嬤說我後面跟了三個人〉."""

    def setUp(self):
        self.td = Path(tempfile.mkdtemp())
        manga.set_work(self.td)
        (manga.OUT / "panels").mkdir(parents=True)
        (manga.OUT / "refs").mkdir(parents=True)
        self.ns = lambda **k: type("A", (), dict({"ids": [], "page": None, "unpicked": False, "name": None, "new": False,  # noqa: E731
                                                  "read": False, "cast": None}, **k))

    def tearDown(self):
        manga.set_work(Path.cwd())
        shutil.rmtree(self.td, ignore_errors=True)

    def _board(self, cells_by_page, **chars):
        b = _tiny(cells_by_page, **chars)
        b["style"] = "Clean black and white line art."
        (self.td / "board.json").write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8")
        return b

    def _png(self, name, colour="white", size=(64, 64)):
        Image.new("RGB", size, colour).save(manga.OUT / "panels" / name)

    def test_cast_brief_lines_up_every_picked_panel(self):
        self._board([[{"id": "p1", "cast": ["ama"], "label": "阿嬤進來"}, {"id": "p2", "cast": ["ama", "boy"], "mirror": True}],
                     [{"id": "p3", "cast": ["boy"]}, {"id": "p4", "cast": ["ama"]}]],
                    ama={"name": "阿嬤", "features": "花襯衫、玉鐲戴左手"}, boy={"name": "弟弟", "features": "白頭髮"})
        for name in ("p1_1.png", "p2_3.png", "p3_1.png", "p4_1.png"):
            self._png(name)
        Image.new("RGB", (40, 40), "white").save(manga.OUT / "refs" / "ama_head.png")
        manga.save_choices({"panels": {"p1": "p1_1.png", "p2": "p2_3.png", "p3": "p3_1.png"},
                            "refs": {"ama:head": "refs/ama_head.png"}})
        manga.cmd_review(self.ns(cast=["ama"]))
        md = (manga.OUT / "review" / "cast_ama.md").read_text(encoding="utf-8")
        self.assertIn("花襯衫、玉鐲戴左手", md)
        self.assertIn("p1_1.png", md)
        self.assertIn("p2_3.png", md)
        self.assertNotIn("p3_1.png", md)  # 弟弟 only
        self.assertIn("還沒選定、這次不比：p4", md)
        self.assertIn("ama_head.png", md)
        self.assertLess(md.index("p1_1.png"), md.index("p2_3.png"))  # reading order
        self.assertIn("p2（頁面上左右翻轉（mirror））", md)  # which wrist the bangle is on depends on it
        self.assertTrue((manga.OUT / "review" / "cast_ama.png").exists())
        self.assertEqual(manga.reviewed_paths(), set())  # its lines never count as reviewed candidates for --new
        manga.cmd_review(self.ns(cast=["all"]))  # 弟弟 has two picked panels too
        self.assertTrue((manga.OUT / "review" / "cast_boy.md").exists())
        with self.assertRaises(SystemExit):
            manga.cmd_review(self.ns(cast=["nobody"]))

    def test_heads_counts_people_who_are_no_character(self):
        b = self._board([[{"id": "p1", "cast": ["me"], "heads": 4, "prompt": "Four nurses at the station."},
                          {"id": "p2", "cast": ["me"], "heads": "走廊上一群看不清的病人，不用數", "prompt": "x"}]],
                        me={"name": "我"})
        self._png("p1_1.png")
        self._png("p2_1.png")
        manga.cmd_review(self.ns(ids=["p1", "p2"], name="t"))
        md = (manga.OUT / "review" / "t.md").read_text(encoding="utf-8")
        self.assertIn("剛好 4 人（其中有名字的：我）", md)
        self.assertIn("人數：走廊上一群看不清的病人，不用數（有名字的：我）", md)
        self.assertIn(str(manga.OUT / "review" / "work" / "t"), md)  # where the checker may put its own scripts
        lint = [(p, lvl, m) for p, lvl, m in manga.lint(b)]
        self.assertFalse(any(p == "p1" and "one character" in m for p, _, m in lint))  # four people, not one
        b["pages"][0]["rows"][0]["cells"][0]["heads"] = 0
        self.assertTrue(any(p == "p1" and lvl == "error" and "fewer" in m for p, lvl, m in manga.lint(b)))

    def test_new_skips_candidates_of_a_rewritten_prompt(self):
        b = self._board([[{"id": "p1", "prompt": "The old corridor, nobody in it."}]])
        for k in (1, 2, 3):
            self._png(f"p1_{k}.png")
        ch = manga.load_choices()
        now = manga.current_key(b, ch, manga.find_panel(b, "p1"))
        manga.log({"kind": "panels", "id": "p1", "prompt_key": "0ld0ld0ld0", "files": ["p1_1.png", "p1_2.png"]})
        manga.log({"kind": "panels", "id": "p1", "prompt_key": now, "files": ["p1_3.png"]})
        manga.cmd_review(self.ns(ids=["p1"], name="all"))
        md = (manga.OUT / "review" / "all.md").read_text(encoding="utf-8")
        self.assertIn("p1_1.png", md)  # listed, but marked
        self.assertIn("其中 p1_1、p1_2 是舊版 prompt 畫的", md)
        shutil.rmtree(manga.OUT / "review")
        manga.cmd_review(self.ns(ids=["p1"], name="redraw", new=True))
        md = (manga.OUT / "review" / "redraw.md").read_text(encoding="utf-8")
        self.assertIn("p1_3.png", md)
        self.assertNotIn("p1_1.png", md)
        manga.log({"kind": "repaint", "id": "p1", "base": "p1_3.png", "files": ["p1_4.png"]})
        self.assertEqual(manga.logged_keys()["p1_4.png"], now)  # a repaint keeps its base's prompt

    def test_repaint_changes_only_the_box(self):
        self._board([[{"id": "p1"}]])
        src = Image.new("RGB", (200, 160), "black")
        src.save(manga.OUT / "panels" / "p1_1.png")
        self._png("p1_3.png")
        sent = {}
        orig = (manga.comfy.upload, manga.comfy.build_graph, manga.comfy.run, manga.comfy.fetch)
        manga.comfy.upload = lambda p: (sent.setdefault("crop", Image.open(p).size), p.name)[1]
        manga.comfy.build_graph = lambda prompt, names, w, h, *a: sent.update(prompt=prompt, size=(w, h)) or {}
        manga.comfy.run = lambda g: ("pid", [{"filename": "x"}, {"filename": "y"}], 9.0, 4.0)
        manga.comfy.fetch = lambda img, dest: Image.new("RGB", (512, 512), "white").save(dest)
        try:
            manga.cmd_repaint(type("A", (), {"candidate": "p1_1", "box": "40,40,160,120", "prompt": "his hair is white",
                                             "n": 2, "seed": 5}))
        finally:
            manga.comfy.upload, manga.comfy.build_graph, manga.comfy.run, manga.comfy.fetch = orig
        self.assertEqual([f.name for f in manga.candidates(manga.OUT / "panels", "p1")], ["p1_1.png", "p1_3.png", "p1_4.png", "p1_5.png"])
        out = Image.open(manga.OUT / "panels" / "p1_4.png")
        self.assertEqual(out.getpixel((100, 80)), (255, 255, 255))  # inside the box: the new patch
        self.assertEqual(out.getpixel((10, 10)), (0, 0, 0))  # outside: untouched
        self.assertLess(sum(out.getpixel((41, 41))), 30)  # the box's own edge fades into the old picture
        self.assertTrue(0 < sum(out.getpixel((50, 50))) < 3 * 255)  # with no hard seam
        self.assertEqual(Image.open(manga.OUT / "panels" / "p1_1.png").getpixel((100, 80)), (0, 0, 0))  # base unchanged
        self.assertEqual(sent["crop"][0] % 32, 0)
        self.assertGreaterEqual(min(sent["crop"]), 512)  # enlarged so the detail fills the frame
        self.assertIn("Keep this picture exactly the same as <image1>. Change only this: his hair is white", sent["prompt"])
        self.assertTrue(sent["prompt"].startswith("Clean black and white line art."))
        rec = json.loads((manga.OUT / "log.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual((rec["kind"], rec["base"], rec["box"], rec["exec_s"]), ("repaint", "p1_1.png", [40, 40, 160, 120], 4.0))
        self.assertEqual(manga.parse_box("0.2,0.25,0.8,0.75", (200, 160)), (40, 40, 160, 120))
        with self.assertRaises(SystemExit):
            manga.parse_box("40,40,260,120", (200, 160))  # outside the picture

    def test_instagram_export(self):
        b = self._board([[{"id": "p1", "text": [{"kind": "title", "text": "阿嬤說\n後面", "pos": "tr"}]}]])
        ns = lambda **k: type("A", (), dict({"ratio": "3:4", "cover": None, "handle": "@x", "tags": "#鬼故事,#創作"}, **k))  # noqa: E731
        with self.assertRaises(SystemExit):
            manga.cmd_export(ns())  # no pages yet
        (manga.OUT / "pages").mkdir()
        for k in range(1, 4):
            Image.new("RGB", (1200, 1700), "black").save(manga.OUT / "pages" / f"page_{k:02d}.png")
        manga.cmd_export(ns())
        dest = manga.OUT / "export" / "ig"
        slides = sorted(dest.glob("*.jpg"))
        self.assertEqual([f.name for f in slides], ["01.jpg", "02.jpg", "03.jpg", "04.jpg", "05.jpg"])  # cover, 3 pages, end
        self.assertTrue(all(Image.open(f).size == (1080, 1440) for f in slides))
        page = Image.open(slides[1]).convert("L")
        self.assertGreater(page.getpixel((5, 720)), 240)  # the page is whole, with white at the sides
        self.assertLess(page.getpixel((540, 720)), 20)
        cap = (dest / "caption.txt").read_text(encoding="utf-8")
        self.assertIn("[創作] 阿嬤說後面", cap)
        self.assertIn(manga.DISCLOSURE, cap)
        self._png("p1_1.png", "white", (300, 200))
        manga.save_choices({"panels": {"p1": "p1_1.png"}})
        manga.cmd_export(ns(ratio="4:5", cover="p1"))
        self.assertEqual(Image.open(dest / "01.jpg").size, (1080, 1350))
        self.assertEqual(len(list(dest.glob("*.jpg"))), 5)  # old slides cleared
        for k in range(4, 21):
            Image.new("RGB", (1200, 1700), "black").save(manga.OUT / "pages" / f"page_{k:02d}.png")
        manga.cmd_export(ns())  # 20 pages: more than one post holds
        self.assertEqual(len(list(dest.glob("part1_*.jpg"))), 19)  # cover and 18 pages
        self.assertEqual(len(list(dest.glob("part2_*.jpg"))), 4)  # cover, 2 pages, end card

    def test_sound_effects_keep_every_character(self):
        def ink_width(text):
            page = Image.new("RGB", (1200, 800), "white")
            manga.draw_sfx(page, {"text": text, "at": [0.5, 0.5], "size": 0.2, "angle": 0}, (0, 0, 1200, 800))
            bbox = page.convert("L").point(lambda v: 255 if v < 128 else 0).getbbox()
            return bbox[2] - bbox[0]
        one, three = ink_width("叩"), ink_width("叩叩叩")
        self.assertGreater(three, 2.6 * one)  # a fixed two-character tile cut the third 叩 off

    def test_scene_sheet_in_a_panel_with_people(self):
        b = self._board([[{"id": "p1", "refs": ["me:bust", "scene:room"],
                           "prompt": "In the room from <image2>, the nurse from <image1> walks to the bed. Only one person in the frame."}]],
                        me={"name": "我"})
        hits = lambda: [m for p, lvl, m in manga.lint(b) if "scene sheet in a panel with people" in m]  # noqa: E731
        self.assertEqual(len(hits()), 1)
        b["pages"][0]["rows"][0]["cells"][0]["prompt"] = "Wide shot of the room from <image2>; the nurse from <image1> walks to the bed. Only one person in the frame."
        self.assertEqual(hits(), [])
        b["pages"][0]["rows"][0]["cells"][0].update(refs=["scene:room"], prompt="The room from <image1>, nobody in it.")
        self.assertEqual(hits(), [])


class SixthComicTest(unittest.TestCase):
    """Tools and rules from 〈阿嬤住院那個禮拜〉."""

    def setUp(self):
        self.td = Path(tempfile.mkdtemp())
        manga.set_work(self.td)
        (manga.OUT / "panels").mkdir(parents=True)

    def tearDown(self):
        manga.set_work(Path.cwd())
        shutil.rmtree(self.td, ignore_errors=True)

    def test_fill_turns_a_black_pane_white_and_keeps_its_frame(self):
        im = Image.new("RGB", (200, 160), "white")
        d = ImageDraw.Draw(im)
        d.rectangle([100, 10, 190, 90], fill="black")          # the pane
        d.rectangle([96, 6, 194, 94], outline="black", width=3)  # its frame, a line
        d.line([(10, 150), (90, 150)], fill="black", width=2)     # a line outside the box
        im.save(manga.OUT / "panels" / "p1_1.png")
        manga.cmd_fill(type("A", (), {"candidate": "p1_1", "box": "90,0,200,100"}))
        out = Image.open(manga.OUT / "panels" / "p1_2.png")
        self.assertEqual(out.getpixel((145, 50)), (255, 255, 255))
        self.assertEqual(out.getpixel((96, 50)), (0, 0, 0))  # the frame stays
        self.assertEqual(out.getpixel((50, 150)), (0, 0, 0))
        rec = json.loads((manga.OUT / "log.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual((rec["kind"], rec["base"]), ("fill", "p1_1.png"))
        with self.assertRaises(SystemExit):
            manga.cmd_fill(type("A", (), {"candidate": "p1_1", "box": "0,0,80,80"}))  # nothing black there

    def test_tone_darkens_paper_inside_the_polygon_only(self):
        im = Image.new("RGB", (200, 200), "white")
        ImageDraw.Draw(im).line([(0, 100), (200, 100)], fill="black", width=3)
        im.save(manga.OUT / "panels" / "p2_1.png")
        for mode in ("dots", "strokes"):
            manga.cmd_tone(type("A", (), {"candidate": "p2_1", "poly": "20,20 180,20 180,180 20,180", "mode": mode}))
        dots, strokes = (Image.open(manga.OUT / "panels" / f"p2_{k}.png").convert("L") for k in (2, 3))
        for out in (dots, strokes):
            inside = sum(out.crop((40, 40, 160, 90)).getdata()) / (120 * 50)
            self.assertLess(inside, 235)  # textured
            self.assertEqual(out.getpixel((5, 5)), 255)  # outside the polygon: untouched
            self.assertEqual(out.getpixel((100, 100)), 0)  # the line stays black
        with self.assertRaises(SystemExit):
            manga.cmd_tone(type("A", (), {"candidate": "p2_1", "poly": "1,1 5,5", "mode": "dots"}))

    def test_crop_keeps_the_shape_and_enlarges(self):
        im = Image.new("RGB", (100, 200), "white")
        ImageDraw.Draw(im).rectangle([20, 20, 60, 60], fill="black")
        im.save(manga.OUT / "panels" / "p3_1.png")
        manga.cmd_crop(type("A", (), {"candidate": "p3_1", "box": "20,20,70,120"}))
        out = Image.open(manga.OUT / "panels" / "p3_2.png")
        self.assertEqual(out.size, (100, 200))
        self.assertLess(sum(out.getpixel((30, 30))), 60)  # the square, now twice as big, fills the top left
        rec = json.loads((manga.OUT / "log.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(rec["box"], [20, 20, 70, 120])  # height follows the shape: 50 wide, 100 tall
        with self.assertRaises(SystemExit):
            manga.cmd_crop(type("A", (), {"candidate": "p3_1", "box": "0,150,100,160"}))  # runs off the bottom

    def test_lint_gaze_wide_close_up_and_seen_by(self):
        b = _tiny([[{"id": "p1", "cast": ["a", "b"], "prompt": "A father and his son sit by a bed. Exactly two people in the frame."}]],
                  a={"name": "我爸"}, b={"name": "我"})
        hits = lambda needle: [m for p, lvl, m in manga.lint(b) if needle in m]  # noqa: E731
        self.assertEqual(len(hits("nothing says where they look")), 1)
        b["pages"][0]["rows"][0]["cells"][0]["prompt"] += " He is in profile, his head turned toward his son. Nobody looks at the viewer."
        self.assertEqual(hits("nothing says where they look"), [])
        c = b["pages"][0]["rows"][0]["cells"][0]
        c.update(cast=["b"], prompt="Close-up of the young man's face. Only one person in the frame.")
        self.assertEqual(hits("close-up in a wide cell"), [])  # a full-page cell is tall
        b["pages"][0]["rows"][0]["h"] = 0.2
        self.assertEqual(len(hits("close-up in a wide cell")), 1)
        c.update(cast=[], prompt="A window high on a wall, as seen by someone lying on his back. Nobody in the picture.")
        self.assertEqual(len(hits("as seen by someone")), 1)


if __name__ == "__main__":
    unittest.main()
