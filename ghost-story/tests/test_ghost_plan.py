"""Offline tests for ghost_plan.py. From ghost-story/: py -X utf8 -m unittest tests.test_ghost_plan"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ghost_plan  # noqa: E402

PARA = "我是護理師，在台南一間區域醫院的內科病房做第四年，固定上大夜。學姊說：「這層沒有鬼，只有家屬。」我很喜歡跟她搭班！"
STORY = "[經驗] 阿嬤說我後面跟了三個人\n" + "\n\n".join(f"{k}. {PARA}" for k in range(1, 31))


class PostTest(unittest.TestCase):
    def test_title_says_it_is_fiction(self):
        self.assertEqual(ghost_plan.post_title("[經驗] 半夜叫我全名的人"), "[創作] 半夜叫我全名的人")
        self.assertEqual(ghost_plan.post_title("沒有標籤"), "[創作] 沒有標籤")

    def test_attach_fits_and_keeps_the_whole_story(self):
        r = ghost_plan.make_posts(STORY, "attach")
        post = r["posts"][0]
        self.assertLessEqual(len(post), 500)
        self.assertTrue(post.startswith("[創作] 阿嬤說我後面跟了三個人\n" + ghost_plan.DISCLOSURE))
        self.assertTrue(post.endswith("（全文在附件）"))
        self.assertIn("30. " + PARA, r["attachment"])
        self.assertNotIn("[經驗]", r["attachment"])

    def test_chain_posts_fit_and_cut_between_sentences(self):
        posts = ghost_plan.make_posts(STORY, "chain")["posts"]
        self.assertGreater(len(posts), 2)
        n = len(posts)
        for i, p in enumerate(posts, 1):
            self.assertLessEqual(len(p), 500)
            self.assertTrue(p.endswith(f"({i}/{n})"))
        body = "\n".join(re.sub(r" \(\d+/\d+\)$", "", p) for p in posts)
        for k in range(1, 31):
            self.assertIn(f"{k}. {PARA}", body)  # every paragraph whole, none cut in half

    def test_a_paragraph_longer_than_a_post_is_cut_at_sentences(self):
        long = "[經驗] 長段落\n" + PARA * 12
        posts = ghost_plan.make_posts(long, "chain")["posts"]
        for p in posts:
            self.assertLessEqual(len(p), 500)
            text = re.sub(r" \(\d+/\d+\)$", "", p)
            self.assertRegex(text, r"[。！」]$")

    def test_ig_caption(self):
        cap = ghost_plan.make_posts(STORY, "ig")["posts"][0]
        self.assertLessEqual(len(cap), 2200)
        self.assertIn(ghost_plan.DISCLOSURE, cap)
        self.assertIn("#鬼故事", cap)


TIDY = "[經驗] 工整\n" + "\n\n".join(
    "我那天晚上十二點才下班，回到宿舍的時候整層樓都很安靜，學長說：「你回來啦。」我點點頭就進房間了。" for _ in range(12))
PTT = "[經驗] 亂\n那天大概凌晨3點吧\n" + """我剛下班回宿舍 整層樓安靜到很怪
平常這時間隔壁都還在打電動的
走廊的燈一盞一盞亮過去
我還想說是誰比我晚回來

學長從走廊那頭探頭出來說你回來啦
我說對啊
他就把門關了。

""" * 4 + "後來我才想起來...\n他不是上禮拜就搬走了嗎！\n"


class SurfaceTest(unittest.TestCase):
    def test_tidy_draft_is_flagged_and_ptt_layout_is_not(self):
        table = __import__("json").loads(ghost_plan.SURFACE.read_text(encoding="utf-8"))
        self.assertGreater(table["n"], 500)
        tidy, ptt = ghost_plan.surface(TIDY), ghost_plan.surface(PTT)
        self.assertGreater(tidy["line_chars"], 40)
        self.assertLess(ptt["line_chars"], 25)
        self.assertEqual(tidy["open_lines"], 0)
        self.assertGreater(ptt["open_lines"], 30)
        self.assertGreater(tidy["quotes"], ptt["quotes"])
        self.assertGreater(ptt["digits"], 0)
        self.assertGreater(ptt["ellipses"], 0)
        must = lambda t: [m for m in ghost_plan.surface_report(t, table) if m.startswith("必改")]  # noqa: E731
        self.assertGreaterEqual(len(must(TIDY)), 2)
        self.assertLessEqual(len(must(PTT)), 1)
        self.assertTrue(any("手動斷行" in m for m in must(TIDY)))

    def test_habits_real_posts_rarely_have(self):
        draft = "[經驗] 宿舍那張空床\n手機排版，飄點很弱\n那天\n我回宿舍\n室友說：\n「你床上是誰？」"
        self.assertEqual(ghost_plan.tells(draft), {"opening_disclaimer": True, "quote_ending": True, "title_na": True})
        plain = "[經驗] 麵攤的阿伯\n那天\n我回宿舍\n室友問我床上是誰\n我到現在還是不敢睡上鋪"
        self.assertEqual(ghost_plan.tells(plain), {"opening_disclaimer": False, "quote_ending": False, "title_na": False})
        table = __import__("json").loads(ghost_plan.SURFACE.read_text(encoding="utf-8"))
        self.assertLess(table["tells"]["quote_ending"], 0.2)
        self.assertTrue(any(m.startswith("必改 quote_ending") for m in ghost_plan.surface_report(draft, table)))


if __name__ == "__main__":
    unittest.main()
