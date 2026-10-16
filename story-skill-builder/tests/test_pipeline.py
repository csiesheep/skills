"""不打網路、不花錢的管線測試：py -m unittest tests.test_pipeline"""
from __future__ import annotations

import json
import os
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
os.environ["STORYPIPE_LLM_BACKEND"] = "fake"

from storypipe import stats  # noqa: E402
from storypipe.annotate import annotate_file  # noqa: E402
from storypipe.collect_ptt import parse_article, parse_nrec  # noqa: E402
from storypipe.generate import generate, make_plan, render_plan  # noqa: E402
from storypipe.llm import FakeBackend  # noqa: E402
from storypipe.taxonomy import BEATS, Plan  # noqa: E402

FAKE_HTML = """<html><body><div id="main-content" class="bbs-screen bbs-content">
<div class="article-metaline"><span class="article-meta-tag">作者</span><span class="article-meta-value">tester (T)</span></div>
<div class="article-metaline-right"><span class="article-meta-tag">看板</span><span class="article-meta-value">marvel</span></div>
<div class="article-metaline"><span class="article-meta-tag">標題</span><span class="article-meta-value">[經驗] 測試文</span></div>
<div class="article-metaline"><span class="article-meta-tag">時間</span><span class="article-meta-value">Mon Jan 1 00:00:00 2026</span></div>
第一段本文。
第二段本文，有<span class="f3">顏色</span>字。
<span class="f2">※ 發信站: 批踢踢實業坊(ptt.cc), 來自: 1.2.3.4 (臺灣)</span>
<span class="f2">※ 文章網址: </span><a href="https://www.ptt.cc/bbs/marvel/M.1.A.1.html">https://www.ptt.cc/bbs/marvel/M.1.A.1.html</a>
<div class="push"><span class="hl push-tag">推 </span><span class="f3 hl push-userid">a</span><span class="f3 push-content">: 好可怕</span><span class="push-ipdatetime">01/01 00:01</span></div>
<div class="push"><span class="f1 hl push-tag">噓 </span><span class="f3 hl push-userid">b</span><span class="f3 push-content">: 虛</span><span class="push-ipdatetime">01/01 00:02</span></div>
<div class="push"><span class="f1 hl push-tag">→ </span><span class="f3 hl push-userid">c</span><span class="f3 push-content">: 補充</span><span class="push-ipdatetime">01/01 00:03</span></div>
</div></body></html>"""


class ParserTest(unittest.TestCase):
    def test_parse_article(self):
        a = parse_article(FAKE_HTML, "https://www.ptt.cc/bbs/marvel/M.1.A.1.html")
        self.assertEqual(a["id"], "M.1.A.1")
        self.assertEqual(a["title"], "[經驗] 測試文")
        self.assertEqual(a["author"], "tester (T)")
        self.assertIn("第一段本文", a["body"])
        self.assertIn("顏色字", a["body"])
        self.assertNotIn("發信站", a["body"])
        self.assertNotIn("好可怕", a["body"])
        self.assertEqual((a["push"], a["boo"], a["neutral"]), (1, 1, 1))
        self.assertEqual(a["pushes"][0], {"tag": "推", "user": "a", "text": "好可怕"})

    def test_parse_nrec(self):
        self.assertEqual(parse_nrec("爆"), 100)
        self.assertEqual(parse_nrec("33"), 33)
        self.assertEqual(parse_nrec("X2"), -20)
        self.assertEqual(parse_nrec(""), 0)


def _fake_raw(n: int) -> list[dict]:
    rng = random.Random(1)
    rows = []
    for i in range(n):
        rows.append(
            {
                "id": f"M.{i}.A.1",
                "url": f"https://www.ptt.cc/bbs/marvel/M.{i}.A.1.html",
                "board": "marvel",
                "title": f"[經驗] 假故事 {i}",
                "author": "x",
                "date": "",
                "nrec": rng.randint(30, 100),
                "push": 10,
                "boo": 0,
                "neutral": 0,
                "body": ("這是第 %d 篇假故事的本文。" % i) * rng.randint(40, 120),
                "pushes": [{"tag": "推", "user": "u", "text": "雞皮疙瘩了"}],
            }
        )
    return rows


class CliParseTest(unittest.TestCase):
    def test_warning_line_then_json(self):
        from storypipe.llm import parse_cli_output, served_model

        out = (
            '[claude-code:unrecognized_model] {"model":"claude-haiku-5-5","query_source":"sdk"}\n'
            '{"is_error":false,"result":"ok","total_cost_usd":0.01,'
            '"modelUsage":{"claude-haiku-5-5":{"outputTokens":40},"claude-x":{"outputTokens":2}}}\n'
        )
        data, warns = parse_cli_output(out)
        self.assertEqual(data["result"], "ok")
        self.assertEqual(len(warns), 1)
        self.assertEqual(served_model(data), "claude-haiku-5-5")

    def test_model_mismatch(self):
        from storypipe.llm import ModelMismatchError, check_served_model

        check_served_model("haiku", "claude-haiku-4-5-20251001")  # 別名不檢查
        check_served_model("claude-haiku-5-5", "claude-haiku-5-5")
        with self.assertRaises(ModelMismatchError):
            check_served_model("claude-haiku-5-5", "claude-haiku-4-5-20251001")


class CorpusTest(unittest.TestCase):
    def test_series_key(self):
        from storypipe.corpus import series_key

        k = series_key("[經驗] 亡母來電（一）")
        for t in ("亡母來電（二）", "[經驗] 亡母來電(十二)", "Re: [經驗] 亡母來電（三）", "[經驗] 亡母來電 完結篇", "[經驗] 亡母來電之四"):
            self.assertEqual(series_key(t), k, t)
        self.assertNotEqual(series_key("[經驗] 宿舍"), series_key("[經驗] 老家"))

    def test_merge_and_dedupe(self):
        from storypipe.corpus import dedupe, merge_series

        body = "".join(chr(0x4E00 + (i * 7919) % 20000) for i in range(1500))  # 不重複的長文本
        arts = [
            {"id": "M.100.A.1", "title": "[經驗] 長篇（一）", "author": "abc (A)", "nrec": 40, "ts": 100, "body": "第一章" * 200},
            {"id": "M.200.A.1", "title": "[經驗] 長篇（二）", "author": "abc", "nrec": 90, "ts": 200, "body": "第二章" * 200},
            {"id": "M.300.A.1", "title": "Re: [經驗] 長篇（一）", "author": "other", "nrec": 5, "ts": 300, "body": "回文" * 200},
            {"id": "M.400.A.1", "title": "[經驗] 宿舍", "author": "x", "nrec": 50, "ts": 400, "body": body},
            {"id": "D.M.999.A.1", "title": "[經驗] 宿舍", "author": "x", "nrec": 3, "ts": 999, "body": body + "（精華區收錄）", "sample": "digest", "curated": True},
        ]
        units = merge_series(arts[:4]) + merge_series(arts[4:])
        series = [u for u in units if u["series_key"]]
        self.assertEqual(len(series), 1)
        self.assertEqual([p["id"] for p in series[0]["parts"]], ["M.100.A.1", "M.200.A.1"])
        self.assertEqual(series[0]["nrec"], 90)
        self.assertEqual(len(units), 4)  # 系列 1 + 別人的 Re: 1 + 宿舍 2
        keep, dropped = dedupe(units, log=lambda *_: None)
        self.assertEqual(len(keep), 3)
        dorm = next(u for u in keep if "宿舍" in u["title"])
        self.assertEqual(dorm["id"], "M.400.A.1")  # 看板勝過精華區
        self.assertTrue(dorm["curated"])  # 精華區旗標轉給保留的那篇
        self.assertEqual(dropped[0]["dup_of"], "M.400.A.1")


class OptionsTest(unittest.TestCase):
    def test_resolve(self):
        from storypipe.options import OptionError, resolve, resolve_ghost, resolve_length, resolve_list, resolve_style

        self.assertEqual(resolve("setting", "校園"), "school")
        self.assertEqual(resolve("setting", "dorm"), "dorm")
        self.assertEqual(resolve("ending", "開放結局"), "open")
        self.assertEqual(resolve("mechanism", "附身"), "possession")
        self.assertEqual(resolve_list("setting", "校園,宿舍、醫院"), ["school", "dorm", "hospital"])
        with self.assertRaises(OptionError):
            resolve("setting", "家")  # 模糊
        with self.assertRaises(OptionError):
            resolve("setting", "月球")
        self.assertEqual(resolve_length("短"), (800, 1200))
        self.assertEqual(resolve_length("1800字"), (1800, 1800))
        self.assertEqual(resolve_length("1500-2500"), (1500, 2500))
        with self.assertRaises(OptionError):
            resolve_length("50")
        self.assertEqual(resolve_ghost("不露面"), 0)
        self.assertEqual(resolve_style("幽默").key, "humor")
        self.assertEqual(resolve_style(None).key, "ptt")
        for s in ("簡約", "口述", "文學", "紀錄", "長輩講古"):
            self.assertTrue(resolve_style(s).prompt())

    def test_plan_respects_options(self):
        import random as _r

        from storypipe.generate import make_plan, render_plan, writer_system

        w = {
            "settings": {"home": {"n": 5, "mean_score": 80, "weight": 140.0}, "school": {"n": 1, "mean_score": 50, "weight": 30.0}},
            "mechanisms_primary": {"possession": {"n": 3, "mean_score": 90, "weight": 120.0}},
            "mechanisms_any": {"possession": {"n": 3, "mean_score": 90, "weight": 120.0}, "presence": {"n": 2, "mean_score": 40, "weight": 40.0}},
            "endings": {"explained": {"n": 4, "mean_score": 80, "weight": 130.0}, "open": {"n": 2, "mean_score": 70, "weight": 70.0}},
            "pairs": {},
            "beats_top": {b: 1 / 6 for b in BEATS},
            "ghost_explicitness": {"dist_top": {"0": 0, "1": 1, "2": 1, "3": 1}},
            "length_top": {"p25": 1500, "p50": 2000, "p75": 2500},
            "examples": [],
        }
        for seed in range(20):
            p = make_plan(w, _r.Random(seed), setting=["school", "dorm"], ending=["open"], length_range=(800, 1200),
                          style="humor", notes=["主角是護理師"])
            self.assertIn(p.setting, ("school", "dorm"))  # dorm 不在資料裡也抽得到
            self.assertEqual(p.ending, "open")
            self.assertTrue(800 <= p.target_chars <= 1200)
        txt = render_plan(p)
        self.assertIn("風格：幽默", txt)
        self.assertIn("主角是護理師", txt)
        self.assertIn("使用者指定的欄位：場景、結尾、長度、風格、額外要求", txt)
        self.assertIn("這篇的風格是「幽默」", writer_system(p))
        p2 = make_plan(w, _r.Random(1), target_chars=99999)
        self.assertEqual(p2.target_chars, 12000)

    def test_tastes(self):
        import random as _r

        from storypipe.generate import make_plan, rules_prompt, writer_system
        from storypipe.options import OptionError, resolve_taste

        self.assertEqual(resolve_taste(None), ("直接", "v2"))
        self.assertEqual(resolve_taste("留白"), ("留白", "restrained"))
        self.assertEqual(resolve_taste("克制")[1], "restrained")
        with self.assertRaises(OptionError):
            resolve_taste("恐怖")
        w = json.loads(Path("data/weights.json").read_text(encoding="utf-8")) if Path("data/weights.json").exists() else None
        if w is None:
            self.skipTest("沒有 weights.json")
        direct = writer_system(make_plan(w, _r.Random(1), rules="v2", style="minimal"))
        quiet = writer_system(make_plan(w, _r.Random(1), rules="restrained", style="minimal"))
        for s in (direct, quiet):
            self.assertIn("要有對話", s)  # 兩種口味都保留資料支持的改進
        self.assertIn("上限也是目標", direct)
        self.assertNotIn("我沒有回頭", direct)
        self.assertIn("我沒有回頭", quiet)
        self.assertIn("最可怕的那一幕尤其要省", quiet)  # 留白用舊版的簡約說明
        self.assertIn("沒回頭看撐住的，是 4 或 5", rules_prompt("judge.md", "restrained"))
        self.assertIn("最可怕那一幕寫得具體", rules_prompt("judge.md", "v2"))


class PipelineTest(unittest.TestCase):
    def test_annotate_stats_generate(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            raw = td / "raw.jsonl"
            raw.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in _fake_raw(24)), encoding="utf-8")
            ann = td / "ann.jsonl"
            backend = FakeBackend()

            # 只標指定篇目、平行 4 路
            only = {f"M.{i}.A.1" for i in range(10)}
            n = annotate_file(raw, ann, backend, model="fake", only_ids=only, workers=4, log=lambda *_: None)
            self.assertEqual(n, 10)
            recs = [json.loads(l) for l in ann.read_text(encoding="utf-8").splitlines()]
            self.assertEqual({r["id"] for r in recs}, only)
            self.assertTrue(all(r["model"] == "fake/fake" and r["model_requested"] == "fake" for r in recs))
            self.assertTrue(all("usage" in r and "elapsed_s" in r for r in recs))

            n = annotate_file(raw, ann, backend, model="fake", log=lambda *_: None)
            self.assertEqual(n, 14)
            # 續跑不重複
            self.assertEqual(annotate_file(raw, ann, backend, model="fake", log=lambda *_: None), 0)

            w = stats.run(ann, td / "weights.json", td / "report.md")
            self.assertGreater(w["n_stories"], 0)
            self.assertLessEqual(w["n_stories"], 24)  # is_story=False 的被排除
            self.assertAlmostEqual(sum(w["beats_top"][b] for b in BEATS), 1.0, places=2)
            self.assertTrue((td / "report.md").read_text(encoding="utf-8").startswith("# 故事 DNA 統計"))

            plan = make_plan(w, random.Random(7), setting="dorm", ending="open")
            self.assertIsInstance(plan, Plan)
            self.assertEqual(plan.setting, "dorm")
            self.assertIn("場景：學校宿舍", render_plan(plan))

            res = generate(backend, w, seed=3, max_rounds=3, log=lambda *_: None)
            self.assertEqual(res["final_round"], 2)  # fake 評審第一輪不過、第二輪過
            self.assertTrue(res["final_verdict"]["passes"])
            self.assertTrue(res["final"].startswith("[經驗]"))
            kinds = [k for k, _ in backend.calls]
            self.assertEqual(kinds[-4:], ["text", "structured", "text", "structured"])


if __name__ == "__main__":
    unittest.main()
