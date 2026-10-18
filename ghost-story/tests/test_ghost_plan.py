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


if __name__ == "__main__":
    unittest.main()
