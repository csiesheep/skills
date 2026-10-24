"""把錄好的畫面剪成 Reel：照 plan.json 一段一段取格、變速、定格、疊字卡、點擊光圈、肖像卡、右下角小肖像、大地圖，段間溶接，再混音樂與音效。

    py -X utf8 render.py <reel>/plan.json            # 寫 <reel>/out/reel.mp4、reel_contact.jpg
    py -X utf8 render.py <reel>/plan.json --preview  # 540x960、15 fps，快速看節奏
素材路徑（rec/、portraits/、music/、cards/）都相對於 plan.json 所在的資料夾。
段的種類：{"src": ...}（錄影）、{"image": ...}（靜圖）、{"portrait": ...}（全螢幕肖像卡）、{"cards": [...]}（分享卡牆）。
錄影段可加 "inset"（右下角小肖像，大小一律 INSET_SIZE）、"bigmap": {"cam_t": [[錄影秒數, 放大, cx, cy], ...]}（下半部大地圖，要錄影時帶 --mapshots）。
plan 頂層 "dissolve": 0.5 = 每段開頭從上一段最後一格淡入。

plan.json：
  {"fps": 30, "music": "music/x.flac", "music_gain_db": 0,
   "segments": [
     {"src": "life", "from": 3.2, "to": 9.0, "dur": 3.0,        # 錄影的 from–to 秒，壓成 dur 秒（變速）
      "ramp": [[0,1],[0.3,4]],                                  # 可選：輸出進度 → 相對速度（積分後再正規化到 from–to）
      "zoom": [[0, 1.0, 540, 960], [1, 1.6, 540, 700]],         # 輸出進度 0–1 → 放大倍數、畫面中心（1080x1920 座標）
      "caption": "一年一年活下去", "cap_at": [0.1, 0.95],
      "freeze": [[0.5, 0.4]],                                   # 輸出進度 0.5 處定格 0.4 秒（加在 dur 之外）
      "sfx": [["choose", 0.2]]},                                # 遊戲音效 assets/audio/<name>.m4a，在輸出進度 0.2 響
     {"cards": ["cards/a.png", ...], "each": 0.45, "grid": 1.2, "caption": "..."},
     {"image": "rec/life/end_card.png", "dur": 4, "zoom": [...]}
   ]}
src 是 rec/<src>/（frames/、frames.json、events.json）；時間從 rec_start 起算。點擊光圈自動取 events.json 的 tap。
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = Path.cwd()   # main() 換成 plan.json 所在的資料夾
INSET_SIZE = 0.62   # 右下角小肖像：全片同一大小（owner 2026-10-23），抉擇卡上也不擋選項
GAME_AUDIO = Path("C:/Users/sheep/code/china_life/assets/audio")
W, H = 1080, 1920
DPR = 1080 / 405
SERIF = "C:/Windows/Fonts/NotoSerifTC-VF.ttf"
KAI = "C:/Windows/Fonts/kaiu.ttf"


def font(size: int, path: str = SERIF, bold: bool = True) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(path, size)
    if path == SERIF:
        try:
            f.set_variation_by_name("Black" if bold else "Regular")
        except Exception:
            pass
    return f


# ---------------------------------------------------------------- 素材
class Rec:
    def __init__(self, name: str):
        d = ROOT / "rec" / name
        self.dir = d
        fr = json.loads((d / "frames.json").read_text(encoding="utf-8"))
        ev = json.loads((d / "events.json").read_text(encoding="utf-8"))
        start = next(e["t"] for e in ev if e["type"] == "rec_start")
        # 錄 life 時同時截地圖（clip 截圖）會讓 screencast 偶爾送出裁過的格子：只留 1080x1920 的格（結果存 good_frames.json）
        good = d / "good_frames.json"
        if good.exists():
            keep = set(json.loads(good.read_text(encoding="utf-8")))
        else:
            keep = {f["f"] for f in fr if Image.open(d / "frames" / f["f"]).size == (W, H)}
            good.write_text(json.dumps(sorted(keep)), encoding="utf-8")
        fr = [f for f in fr if f["f"] in keep]
        self.t = [f["t"] - start for f in fr]
        self.f = [d / "frames" / f["f"] for f in fr]
        self.taps = [(e["t"] - start, e["x"] * DPR, e["y"] * DPR) for e in ev if e["type"] == "tap"]
        self.ages = [(e["t"] - start, e["age"]) for e in ev if e["type"] == "age"]
        self.cache: dict[int, Image.Image] = {}

    def age_at(self, t: float) -> str | None:
        cur = None
        for tt, a in self.ages:
            if tt > t:
                break
            cur = a
        return cur

    def at(self, t: float) -> Image.Image:
        i = max(0, bisect.bisect_right(self.t, t) - 1)
        if i not in self.cache:
            if len(self.cache) > 40:
                self.cache.clear()
            self.cache[i] = Image.open(self.f[i]).convert("RGB")
        return self.cache[i]


def interp(keys: list, p: float) -> list[float]:
    """keys: [[p, v1, v2, ...], ...] 依輸出進度 p 做 smoothstep 內插。"""
    if not keys:
        return []
    if p <= keys[0][0]:
        return keys[0][1:]
    for a, b in zip(keys, keys[1:]):
        if a[0] <= p <= b[0]:
            u = (p - a[0]) / (b[0] - a[0] or 1)
            u = u * u * (3 - 2 * u)
            return [x + (y - x) * u for x, y in zip(a[1:], b[1:])]
    return keys[-1][1:]


def camera(img: Image.Image, zoom: float, cx: float, cy: float) -> tuple[Image.Image, tuple]:
    if zoom <= 1.001:
        return img, (0, 0, 1)
    cw, ch = W / zoom, H / zoom
    x0 = min(max(cx - cw / 2, 0), W - cw)
    y0 = min(max(cy - ch / 2, 0), H - ch)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch)), (x0, y0, zoom)


def ripple(draw: ImageDraw.ImageDraw, x: float, y: float, age: float):
    """點擊光圈：0–0.6 秒擴散淡出。"""
    if not (0 <= age <= 0.6):
        return
    k = age / 0.6
    r = 40 + 120 * k
    a = int(230 * (1 - k))
    draw.ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255, a), width=10)
    if age < 0.25:
        r2 = 46
        draw.ellipse([x - r2, y - r2, x + r2, y + r2], fill=(255, 255, 255, int(150 * (1 - age / 0.25))))


SCOREBOARD = None   # plan["scoreboard"]：{"y": 400, "marks": [[錄影秒數, 是否考中, "童"], ...]}


def scoreboard_layer(st: float) -> Image.Image:
    """科舉計分板：一排 10 格，放榜那一刻蓋上 ✘（灰）或 ✔（金），格子下寫那一場考的級別。最新一格會彈一下。"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    marks = SCOREBOARD["marks"]
    y0 = SCOREBOARD.get("y", 400)
    n, cell, gap = 10, 92, 8
    x0 = (W - (n * cell + (n - 1) * gap)) / 2
    d.rounded_rectangle([x0 - 22, y0 - 20, W - x0 + 22, y0 + cell + 74], 30, fill=(20, 14, 10, 205))
    lab = font(38)
    for i in range(n):
        cx, cy = x0 + i * (cell + gap) + cell / 2, y0 + cell / 2
        shown = i < len(marks) and marks[i][0] <= st
        age = st - marks[i][0] if shown else 99
        s = 1 + 0.35 * max(0.0, 1 - age / 0.35) if shown else 1   # 剛蓋上去：放大再縮回
        r = cell / 2 * s
        if not shown:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(230, 220, 200, 120), width=4)
            d.text((cx, cy), str(i + 1), font=font(32), anchor="mm", fill=(230, 220, 200, 120))
            continue
        ok, level = marks[i][1], marks[i][2]
        fill = (226, 176, 44, 255) if ok else (170, 54, 44, 245)      # 考中金、落榜朱紅
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=(250, 240, 220, 255), width=4)
        w = max(7, int(10 * s))
        if ok:   # 打勾
            d.line([(cx - r * 0.45, cy), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.5, cy - r * 0.38)], fill=(255, 255, 255, 255), width=w, joint="curve")
        else:    # 打叉
            k = r * 0.38
            d.line([(cx - k, cy - k), (cx + k, cy + k)], fill=(255, 255, 255, 255), width=w)
            d.line([(cx - k, cy + k), (cx + k, cy - k)], fill=(255, 255, 255, 255), width=w)
        d.text((cx, y0 + cell + 32), level, font=lab, anchor="mm", fill=(255, 226, 140, 255) if ok else (240, 228, 210, 255))
    # 剛放榜的那一場：畫面中央蓋一個大印章（定格時一直在）
    for i in range(min(n, len(marks))):
        age = st - marks[i][0]
        if 0 <= age <= SCOREBOARD.get("stamp_for", 0.9):
            layer = Image.alpha_composite(layer, stamp_layer(i, marks[i][1], marks[i][2], age))
    return layer


LEVEL_NAME = {"童": "童生試", "生": "生員試", "舉": "舉人試", "進": "進士試"}


def stamp_layer(i: int, ok: bool, level: str, age: float) -> Image.Image:
    """畫面中央的大印章：第 N 次・童生試／落榜（朱紅）或上榜（金）；進士寫「進士」。剛出現時從大縮到定位。"""
    sw, sh = 700, 330
    st = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    color = (176, 120, 10, 255) if ok else (190, 46, 36, 255)
    d.rounded_rectangle([8, 8, sw - 8, sh - 8], 34, fill=(250, 244, 230, 240), outline=color, width=14)
    d.rounded_rectangle([30, 30, sw - 30, sh - 30], 24, outline=color, width=4)
    d.text((sw / 2, 88), f"第 {i + 1} 次・{LEVEL_NAME.get(level, level)}", font=font(54), anchor="mm", fill=(60, 40, 30, 255))
    word = ("進士" if level == "進" else "上榜") if ok else "落榜"
    d.text((sw / 2, 212), word, font=font(150, KAI), anchor="mm", fill=color)
    k = 1 + 0.6 * max(0.0, 1 - age / 0.12)                     # 蓋章：0.12 秒內從 1.6 倍縮到 1 倍
    st = st.resize((round(sw * k), round(sh * k)), Image.BICUBIC).rotate(-5, resample=Image.BICUBIC, expand=True)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(st, (round((W - st.width) / 2), round(1120 - st.height / 2)))
    return layer


AGETAG = None   # plan["agetag"]：{"name": "高巧兒", "y": 58}；錄影段上方固定一條「姓名｜N 歲」，年紀取 events.json 的 age


def agetag_layer(name: str, age: str | None, y: int = 58) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if age is None:
        return layer
    d = ImageDraw.Draw(layer)
    text = f"{name}｜{age} 歲"
    f = font(44)
    w = d.textlength(text, font=f)
    d.rounded_rectangle([(W - w) / 2 - 30, y - 34, (W + w) / 2 + 30, y + 34], 34, fill=(150, 36, 28, 235))
    d.text((W / 2, y), text, font=f, anchor="mm", fill=(255, 246, 234, 255))
    return layer


def caption_layer(text: str, alpha: float, y: int = 250) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if not text or alpha <= 0:
        return layer
    lines = text.split("\n")
    d = ImageDraw.Draw(layer)
    sizes = [86 if i == 0 else 54 for i in range(len(lines))]
    yy = y
    for line, sz0 in zip(lines, sizes):
        sz = sz0
        f = font(sz, bold=sz0 > 60)
        while d.textlength(line, font=f) > W - 140 and sz > 30:   # 太長就縮字，不出框
            sz -= 4
            f = font(sz, bold=sz0 > 60)
        w = d.textlength(line, font=f)
        d.text(((W - w) / 2, yy), line, font=f, fill=(250, 240, 220, int(255 * alpha)),
               stroke_width=max(4, sz // 12), stroke_fill=(30, 18, 12, int(235 * alpha)))
        yy += int(sz * 1.35)
    # 字後面一層柔光的暗底，亮畫面也讀得到
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([60, y - 40, W - 60, yy + 20], 40, fill=(0, 0, 0, int(110 * alpha)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    return Image.alpha_composite(shadow, layer)


def cap_alpha(p: float, at: list[float], dur: float) -> float:
    a, b = at
    if p < a or p > b:
        return 0.0
    fade = 0.25 / max(dur, 0.1)
    return min(1.0, (p - a) / fade, (b - p) / fade)



# ---------------------------------------------------------------- 肖像（Reel 3：她隨年紀長大）
PAPER = (239, 230, 210)
_PCACHE: dict[str, Image.Image] = {}


def portrait(path: str) -> Image.Image:
    if path not in _PCACHE:
        _PCACHE[path] = Image.open(ROOT / path).convert("RGB")
    return _PCACHE[path]


def inset_layer(path: str, alpha: float = 1.0, size: float = 1.0) -> Image.Image:
    """遊戲畫面右下（地圖那一角）的小肖像，米色細框。size < 1 用在抉擇卡上，貼著右下角少擋選項。"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if alpha <= 0:
        return layer
    pw, ph = round(360 * size), round(450 * size)
    im = portrait(path).resize((pw, ph), Image.LANCZOS).convert("RGBA")
    frame = Image.new("RGBA", (pw + 24, ph + 24), (248, 241, 224, 255))
    frame.alpha_composite(im, (12, 12))
    d = ImageDraw.Draw(frame)
    d.rectangle([3, 3, pw + 20, ph + 20], outline=(140, 40, 30, 255), width=3)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x, y = (W - frame.width - 34, H - frame.height - 60) if size >= 1 else (W - frame.width - 16, H - frame.height - 24)
    ImageDraw.Draw(sh).rectangle([x + 10, y + 14, x + frame.width + 10, y + frame.height + 14], fill=(0, 0, 0, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(12))
    layer = Image.alpha_composite(layer, sh)
    layer.alpha_composite(frame, (x, y))
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    return layer


def render_portrait(seg: dict, fps: int, out_frames: list, sfx_out: list, t_now: float, scale: float):
    """全螢幕肖像卡：米紙底、肖像慢慢推近，下方大字「N 歲」與一行小字；可從上一張肖像交叉淡入。"""
    dur = seg["dur"]
    n = max(1, round(dur * fps))
    cur = portrait(seg["portrait"])
    prev = portrait(seg["from_portrait"]) if seg.get("from_portrait") else None
    pw = 900
    ph = round(pw * cur.height / cur.width)
    big, small = font(132, KAI), font(50, bold=False)
    for k in range(n):
        u = k / max(n - 1, 1)
        s = 1.0 + seg.get("push", 0.05) * u
        bg = Image.new("RGBA", (W, H), PAPER + (255,))
        def place(im):
            r = im.resize((round(pw * s), round(ph * s)), Image.BILINEAR)
            box = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            box.paste(r, ((W - r.width) // 2, 170 - (r.height - ph) // 2))
            return box
        layer = place(cur)
        xf = seg.get("xfade", 0.35)
        if prev is not None and u * dur < xf:
            a = u * dur / xf
            layer = Image.blend(place(prev), layer, a)
        img = Image.alpha_composite(bg, layer)
        d = ImageDraw.Draw(img)
        ta = min(1.0, max(0.0, (u * dur - 0.15) / 0.3))
        y = 170 + ph + 70
        d.text((W / 2, y + 60), seg.get("label", ""), font=big, anchor="mm", fill=(150, 36, 28, int(255 * ta)))
        if seg.get("sub"):
            d.text((W / 2, y + 175), seg["sub"], font=small, anchor="mm", fill=(70, 55, 42, int(255 * ta)))
        if seg.get("fade_in") and k < seg["fade_in"] * fps:
            img = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, k / (seg["fade_in"] * fps))
        if seg.get("caption"):   # 冷開場的閃卡：肖像上疊一行大字（第一格就要在，不淡入）
            img = Image.alpha_composite(img, caption_layer(seg["caption"], 1.0, seg.get("cap_y", 1500)))
        img = img.convert("RGB")
        out_frames.append(img.resize((round(W * scale), round(H * scale)), Image.BILINEAR) if scale != 1 else img)
    for name, p in seg.get("sfx", []):
        sfx_out.append((name, t_now + p * dur, seg.get("sfx_gain", 0)))
    return dur



# ---------------------------------------------------------------- 大地圖（Reel 4：一生走了多遠）
class MapRec:
    """rec/<name>/mapshots：錄影時每 0.2–0.4 秒用 2.5 倍截下的地圖 SVG。時間同樣從 rec_start 起算。"""
    def __init__(self, name: str):
        d = ROOT / "rec" / name
        ms = json.loads((d / "mapshots.json").read_text(encoding="utf-8"))
        ev = json.loads((d / "events.json").read_text(encoding="utf-8"))
        start = next(e["t"] for e in ev if e["type"] == "rec_start")
        self.t = [m["t"] - start for m in ms]
        self.f = [d / "mapshots" / m["f"] for m in ms]
        self.cache: dict[int, Image.Image] = {}

    def at(self, t: float) -> Image.Image:
        i = max(0, bisect.bisect_right(self.t, t) - 1)
        if i not in self.cache:
            if len(self.cache) > 20:
                self.cache.clear()
            self.cache[i] = Image.open(self.f[i]).convert("RGB")
        return self.cache[i]


MAPS: dict[str, MapRec] = {}


def bigmap_layer(src: str, st: float, z: float, cx: float, cy: float) -> Image.Image:
    """把遊戲地圖的高解析截圖放大成畫面下半部的大地圖：以 (cx, cy)（截圖像素）為中心、放大 z 倍裁切，寬 1080。"""
    if src not in MAPS:
        MAPS[src] = MapRec(src)
    shot = MAPS[src].at(st)
    sw, sh = shot.size
    cw, ch = sw / z, sh / z
    x0 = min(max(cx - cw / 2, 0), sw - cw)
    y0 = min(max(cy - ch / 2, 0), sh - ch)
    pw = W - 40
    ph = round(pw * ch / cw)
    panel = shot.resize((pw, ph), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch)).convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y = H - ph - 70
    sh_ = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh_).rectangle([20, y - 6, W - 20, y + ph + 6], fill=(0, 0, 0, 120))
    layer = Image.alpha_composite(layer, sh_.filter(ImageFilter.GaussianBlur(14)))
    layer.alpha_composite(panel, (20, y))
    ImageDraw.Draw(layer).rectangle([18, y - 2, W - 18, y + ph + 2], outline=(150, 36, 28, 255), width=4)
    return layer


# ---------------------------------------------------------------- 一段一段畫
def src_time(seg: dict, p: float) -> float:
    a, b = seg["from"], seg["to"]
    ramp = seg.get("ramp")
    if not ramp:
        return a + (b - a) * p
    # 速度曲線積分：把相對速度在 0–1 上積出來，正規化成 from–to
    xs = np.linspace(0, 1, 401)
    v = np.array([interp([[k[0], k[1]] for k in ramp], x)[0] for x in xs])
    cum = np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2 * np.diff(xs))])
    cum /= cum[-1]
    return a + (b - a) * float(np.interp(p, xs, cum))


def render_segment(seg: dict, fps: int, recs: dict, out_frames: list, sfx_out: list, t_now: float, scale: float):
    if "cards" in seg:
        return render_cards(seg, fps, out_frames, sfx_out, t_now, scale)
    if "portrait" in seg:
        return render_portrait(seg, fps, out_frames, sfx_out, t_now, scale)
    dur = seg["dur"]
    n = max(1, round(dur * fps))
    freezes = sorted(seg.get("freeze", []))
    # 輸出時間軸：先排 n 格，再在定格處插入重複的格
    plan = []
    for i in range(n):
        p = i / max(n - 1, 1)
        for fp, fd in freezes:
            if abs(p - fp) < 0.5 / n:
                plan += [("freeze", p)] * round(fd * fps)
        plan.append(("run", p))
    rec = recs.get(seg.get("src")) if "src" in seg else None
    still = Image.open(ROOT / seg["image"]).convert("RGB") if "image" in seg else None
    if still is not None and still.size != (W, H):
        bg = Image.new("RGB", (W, H), (24, 20, 18))
        s = min(W / still.width, H / still.height)
        im2 = still.resize((round(still.width * s), round(still.height * s)), Image.LANCZOS)
        bg.paste(im2, ((W - im2.width) // 2, (H - im2.height) // 2))
        still = bg
    total = len(plan) / fps
    for k, (kind, p) in enumerate(plan):
        st = src_time(seg, p) if rec else 0
        base = rec.at(st) if rec else still
        z = interp(seg.get("zoom", []), p) or [1, W / 2, H / 2]
        img, (x0, y0, zf) = camera(base, *z)
        if kind == "freeze":
            img = img.point(lambda v: min(255, int(v * 1.06)))
        img = img.convert("RGBA")
        over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        if rec:
            for tt, x, y in rec.taps:
                ripple(d, (x - x0) * zf, (y - y0) * zf, st - tt)
        img = Image.alpha_composite(img, over)
        if seg.get("caption"):
            img = Image.alpha_composite(img, caption_layer(seg["caption"], cap_alpha(k / max(len(plan) - 1, 1), seg.get("cap_at", [0.05, 0.97]), total), seg.get("cap_y", 250)))
        if AGETAG and rec and seg.get("src") == "life" and not seg.get("no_agetag"):
            img = Image.alpha_composite(img, agetag_layer(AGETAG["name"], rec.age_at(st), AGETAG.get("y", 58)))
        if seg.get("bigmap") and rec:
            bm = seg["bigmap"]
            zc = interp(bm["cam_t"], st)   # 鏡頭跟著錄影時間走（變速、定格都不影響）
            img = Image.alpha_composite(img, bigmap_layer(seg["src"], st, *zc))
        if seg.get("inset"):
            img = Image.alpha_composite(img, inset_layer(seg["inset"], min(1.0, k / (0.25 * fps)) if seg.get("inset_fade") else 1.0, seg.get("inset_size", INSET_SIZE)))
        if SCOREBOARD and seg.get("board") and rec:
            img = Image.alpha_composite(img, scoreboard_layer(st))
        if seg.get("fade_in") and k < seg["fade_in"] * fps:
            img = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, k / (seg["fade_in"] * fps))
        out_frames.append(img.convert("RGB").resize((round(W * scale), round(H * scale)), Image.BILINEAR) if scale != 1 else img.convert("RGB"))
    events = list(seg.get("sfx", []))
    if seg.get("sfx_src") and rec:
        ps = np.linspace(0, 1, 2001)
        sts = np.array([src_time(seg, q) for q in ps])
        events += [[n, float(ps[np.argmin(np.abs(sts - t))])] for n, t in seg["sfx_src"]]
    for name, p in events:
        sfx_out.append((name, t_now + p * dur + sum(fd for fp, fd in freezes if fp < p), seg.get("sfx_gain", 0)))
    return total


def render_cards(seg: dict, fps: int, out_frames: list, sfx_out: list, t_now: float, scale: float):
    cards = [Image.open(ROOT / c).convert("RGB") for c in seg["cards"]]
    bg = Image.new("RGB", (W, H), (22, 18, 16))
    each, grid = seg["each"], seg["grid"]
    t = 0.0
    total = each * len(cards) + grid
    count = 0
    for i, c in enumerate(cards):
        for k in range(round(each * fps)):
            u = k / (each * fps)
            s = 0.80 + 0.04 * u                       # 每張輕推近
            im = c.resize((round(W * s), round(H * s)), Image.BILINEAR)
            fr = bg.copy()
            fr.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
            out_frames.append(add_cap(fr, seg, count / (total * fps), total, scale))
            count += 1
        sfx_out.append((seg.get("card_sfx", "stamp"), t_now + i * each, seg.get("sfx_gain", -6)))
    # 2x4 的牆，從近到遠
    cols, rows, gap = 4, 2, 18
    tw = (W * 1.9 - gap * (cols + 1)) / cols
    th = tw * 16 / 9
    wall = Image.new("RGB", (round(tw * cols + gap * (cols + 1)), round(th * rows + gap * (rows + 1))), (22, 18, 16))
    for i, c in enumerate(cards[:8]):
        r, q = divmod(i, cols)
        wall.paste(c.resize((round(tw), round(th)), Image.LANCZOS), (round(gap + q * (tw + gap)), round(gap + r * (th + gap))))
    n = round(grid * fps)
    for k in range(n):
        u = k / max(n - 1, 1)
        u = u * u * (3 - 2 * u)
        s = (W * 0.98 / wall.width) * (1 + 0.9 * (1 - u))
        im = wall.resize((round(wall.width * s), round(wall.height * s)), Image.BILINEAR)
        fr = bg.copy()
        fr.paste(im, ((W - im.width) // 2, (H - im.height) // 2 + 120))
        out_frames.append(add_cap(fr, seg, count / (total * fps), total, scale))
        count += 1
    return total


def add_cap(fr: Image.Image, seg: dict, p: float, total: float, scale: float) -> Image.Image:
    img = fr.convert("RGBA")
    if seg.get("caption"):
        img = Image.alpha_composite(img, caption_layer(seg["caption"], cap_alpha(p, seg.get("cap_at", [0.03, 0.98]), total), seg.get("cap_y", 160)))
    img = img.convert("RGB")
    return img.resize((round(W * scale), round(H * scale)), Image.BILINEAR) if scale != 1 else img


# ---------------------------------------------------------------- 聲音
def read_audio(path: Path, sr: int = 48000) -> np.ndarray:
    raw = subprocess.run([FF, "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def mix(plan: dict, length: float, sfx: list, out_wav: Path, sr: int = 48000):
    n = int(length * sr)
    bus = np.zeros((n, 2), np.float32)
    if plan.get("music"):
        m = read_audio(ROOT / plan["music"])[int(plan.get("music_offset", 0) * sr):][:n]
        g = 10 ** (plan.get("music_gain_db", -4) / 20)
        env = np.ones(len(m), np.float32)
        fo = int(plan.get("music_fade_out", 2.0) * sr)
        env[-fo:] = np.linspace(1, 0, fo) if len(m) >= n else env[-fo:]
        fi = int(0.3 * sr)
        env[:fi] = np.linspace(0, 1, fi)
        bus[:len(m)] += m * env[:, None] * g
        # 音效響的地方把音樂壓低一點
        for name, t, gdb in sfx:
            a = int(t * sr)
            duck = np.ones(n, np.float32)
        # (簡化：不做 ducking；音效本身夠短)
    for name, t, gdb in sfx:
        p = GAME_AUDIO / f"{name}.m4a"
        if not p.exists():
            print("no sfx", name)
            continue
        s = read_audio(p) * 10 ** ((plan.get("sfx_gain_db", -3) + gdb) / 20)
        a = int(t * sr)
        if a >= n:
            continue
        s = s[: n - a]
        bus[a:a + len(s)] += s
    raw = out_wav.with_suffix(".raw.wav")
    pcm = np.clip(bus, -1, 1)
    subprocess.run([FF, "-y", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "2", "-i", "-", str(raw)],
                   input=pcm.tobytes(), check=True)
    subprocess.run([FF, "-y", "-v", "error", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-2:LRA=11,alimiter=limit=0.7:level=false", "-ar", str(sr), str(out_wav)], check=True)
    raw.unlink()


# ---------------------------------------------------------------- 主程式
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--name", default="reel", help="輸出檔名（out/<name>.mp4）；預覽一律叫 preview")
    a = ap.parse_args()
    global ROOT
    ROOT = Path(a.plan).resolve().parent
    plan = json.loads(Path(a.plan).resolve().read_text(encoding="utf-8"))
    global SCOREBOARD, AGETAG
    SCOREBOARD = plan.get("scoreboard")
    AGETAG = plan.get("agetag")
    fps = 15 if a.preview else plan.get("fps", 30)
    scale = 0.5 if a.preview else 1.0
    recs = {s["src"]: None for s in plan["segments"] if "src" in s}
    recs = {k: Rec(k) for k in recs}
    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    name = "preview" if a.preview else a.name
    silent = out / f"{name}_silent.mp4"
    proc = subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{round(W*scale)}x{round(H*scale)}",
                             "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18" if not a.preview else "26",
                             "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    sfx, t, starts, thumbs = [], 0.0, [], []
    last = None
    for i, seg in enumerate(plan["segments"]):
        frames: list[Image.Image] = []
        starts.append(t)
        d = render_segment(seg, fps, recs, frames, sfx, t, scale)
        # 段與段之間溶接：新一段的開頭從上一段最後一格淡入（不加長片長）
        xd = seg.get("dissolve", plan.get("dissolve", 0))
        if xd and i > 0 and last is not None:
            nx = min(len(frames), round(xd * fps))
            for k in range(nx):
                frames[k] = Image.blend(last, frames[k], (k + 1) / (nx + 1))
        last = frames[-1] if frames else last
        for f in frames:
            proc.stdin.write(f.tobytes())
        thumbs.append(frames[len(frames) // 2].resize((216, 384)))
        print(f"seg {i:2d} {t:6.2f}s +{d:5.2f}s {seg.get('caption', '') or seg.get('note', '')}".replace("\n", " "))
        t += d
    proc.stdin.close()
    proc.wait()
    wav = out / f"{name}.wav"
    mix(plan, t, sfx, wav)
    final = out / f"{name}.mp4"
    subprocess.run([FF, "-y", "-v", "error", "-i", str(silent), "-i", str(wav), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", str(final)], check=True)
    silent.unlink()
    cols = 6
    sheet = Image.new("RGB", (216 * cols, 384 * math.ceil(len(thumbs) / cols)), (0, 0, 0))
    for i, th in enumerate(thumbs):
        sheet.paste(th, (216 * (i % cols), 384 * (i // cols)))
    sheet.save(out / f"{name}_contact.jpg", quality=85)
    print(f"{final}  {t:.2f}s")


if __name__ == "__main__":
    main()
