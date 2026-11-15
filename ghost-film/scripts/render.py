"""ghost-film reel: a 9:16 video with voiceover, subtitles timed to the voice, H3 clips, music and sound.

    cd <story>/film/reel && py -X utf8 <skill>/scripts/render.py [shots.json] [--reuse]

shots.json: {"out": name, "music": file in brand/music, "music_gain", "amb_gain", "vo_picks": file, "shots": [...]}
A shot: {"id", "clip": path | "still": path | "clip0": path (the clip's first frame as a still),
         "offset" (clip start s), "speed" (forced clip speed), "max_t" (last usable clip second),
         "lines": ["N01", {"clip_speech": [a, b], "text": "「…」"}],   played in order
         "dur" (fixed length) | "min", "lead", "gap", "tail", "motion", "focus", "amt", "fx": [...], "lift" (gamma < 1
         brightens), "sfx": [[name, at, gain]], "amb" (this clip's own sound gain), "xfade" (frames), "title": true,
         "big": true (subtitles large in the middle), "end": true (the end card), "black" (s of black before),
         "music_cut": [a, b] (silence the music over these shot seconds, negative = from the shot's end)}
Voice lines come from vo/picks.json {"N01": "path.flac"}; their text from vo/script.json.
Engine helpers (fx, clip frames, end card, contact sheet, mux) are ghost-reel's reel.py and sfx.py.
"""
import json, math, os, random, re, subprocess, sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "ghost-reel" / "scripts"))
import reel as R  # noqa: E402
import sfx as SFX  # noqa: E402

HERE = Path.cwd()          # <story>/film/reel: shots.json, clips/, src/, music/, out/
FILM = HERE.parent         # <story>/film: vo/ (script.json, picks.json, spans.json)
SKILL = Path(__file__).resolve().parent
BRAND = Path("C:/Users/sheep/Pictures/gui_chang_shi/brand")
FF = "C:/Users/sheep/ffbin/ffmpeg.exe"
W, H, FPS, SR = R.W, R.H, R.FPS, SFX.SR
SUB_FONT = "C:/Windows/Fonts/msjhbd.ttc"
TITLE_FONT = "C:/Windows/Fonts/msjhl.ttc"

args = [a for a in sys.argv[1:] if not a.startswith("--")]
REUSE = "--reuse" in sys.argv
SPEC = json.loads((HERE / (args[0] if args else "shots.json")).read_text(encoding="utf-8"))
OUT = HERE / "out" / SPEC.get("out", "reel_v1")
OUT.mkdir(parents=True, exist_ok=True)
SCRIPT = json.loads((FILM / "vo" / "script.json").read_text(encoding="utf-8"))
PICKS = json.loads((FILM / "vo" / SPEC.get("vo_picks", "picks.json")).read_text(encoding="utf-8"))
brand = json.loads((BRAND / "brand.json").read_text(encoding="utf-8"))
R.STORY = SimpleNamespace(TITLE=SPEC.get("title", "靠門的下鋪"), NUMBER=None, END=SPEC.get("end_lines"),
                          SEAL=str(BRAND / brand["seal"]), HANDLE=brand["handle"], DISCLOSURE=brand["disclosure"])
random.seed(7); np.random.seed(7)


def p(path):
    q = Path(path)
    return q if q.is_absolute() else (HERE / q)


# ---------------------------------------------------------------- audio helpers
_aud = {}


def audio(path):
    path = str(p(path))
    if path not in _aud:
        _aud[path] = SFX.read_raw(Path(path), FF).astype(np.float64)
    return _aud[path]


def speech_span(a, thr_db=-32):
    """First and last sample above the threshold (a voice take with its silence trimmed)."""
    m = np.abs(a).max(axis=1)
    win = int(SR * 0.02)
    env = np.convolve(m, np.ones(win) / win, mode="same")
    on = np.where(env > 10 ** (thr_db / 20) * env.max())[0] if env.max() > 0 else []
    if len(on) == 0:
        return 0, len(a)
    return max(0, on[0] - int(SR * 0.03)), min(len(a), on[-1] + int(SR * 0.12))


def sped(path, speed):
    """The take played faster at the same pitch (ffmpeg atempo), cached next to the render."""
    if abs(speed - 1) < 1e-3:
        return path
    out = OUT / "_vo" / f"{Path(path).stem}_x{speed:.2f}.wav"
    if not out.exists():
        out.parent.mkdir(exist_ok=True)
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(path), "-af", f"atempo={speed}", str(out)], check=True)
    return out


SPANS = json.loads((FILM / "vo" / "spans.json").read_text(encoding="utf-8")) if (FILM / "vo" / "spans.json").exists() else {}


def vo_take(name):
    sp = SPEC.get("vo_speed", 1.0)
    a = audio(sped(PICKS[name], sp))
    if SPANS.get(name):   # word timings from ASR (vo/spans.py): the energy of a generated take has a noise floor
        s = max(0, int((SPANS[name][0] / sp - 0.12) * SR)); e = min(len(a), int((SPANS[name][1] / sp + 0.35) * SR))
    else:
        s, e = speech_span(a)
    a = a[s:e].copy()
    rms = np.sqrt((a ** 2).mean()) + 1e-9
    a *= 0.09 / rms
    f = int(SR * 0.01)
    a[:f] *= np.linspace(0, 1, f)[:, None]; a[-f * 4:] *= np.linspace(1, 0, f * 4)[:, None]
    return a


# ---------------------------------------------------------------- text
_fonts = {}


def tfont(size, path=SUB_FONT):
    k = (size, path)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(path, size)
    return _fonts[k]


def chunks(text, limit=15):
    """Subtitle pieces: sentences, then commas, each at most `limit` characters (no trailing comma or full stop)."""
    out = []
    for sent in re.split(r"(?<=[。？！])", text):
        sent = sent.strip()
        if not sent:
            continue
        while len(sent) > limit:
            # the comma that leaves the most even pieces (「對啊，…」 no longer leaves 「裡面」 alone on a line)
            ps = [i + 1 for i, ch in enumerate(sent[:limit + 1]) if ch in "，、；：…"]
            cut = min(ps, key=lambda c: max(c, min(len(sent) - c, limit + 1))) if ps else limit
            out.append(sent[:cut]); sent = sent[cut:]
        if sent:
            out.append(sent)
    return [re.sub(r"[，。、；]+$", "", c) for c in out if c.strip("，。")]


def sub_tile(text, size=64, color=(250, 250, 248)):
    """Commas inside a subtitle become a wide space; a line too long for the frame breaks at the space or comma
    nearest its middle."""
    f = tfont(size)
    text = text.replace("，", "　").replace("、", "　")
    if f.getlength(text) < W - 90:
        lines = [text]
    else:
        mid = len(text) / 2
        cands = [k for k, c in enumerate(text) if c in "　…"]
        k = min(cands, key=lambda k: abs(k - mid)) if cands and abs(min(cands, key=lambda k: abs(k - mid)) - mid) < len(text) * 0.3 else int(mid)
        lines = [text[:k].strip("　"), text[k:].strip("　…") if text[k] != "…" else text[k:]]
    lh = round(size * 1.42)
    wid = [f.getlength(t) for t in lines]
    tile = Image.new("RGBA", (int(max(wid)) + 64, lh * len(lines) + 34), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle([0, 0, tile.width - 1, tile.height - 1], radius=18, fill=(0, 0, 0, 120))
    for k, t in enumerate(lines):
        d.text(((tile.width - wid[k]) / 2, 14 + k * lh), t, font=f, fill=color, stroke_width=5, stroke_fill=(0, 0, 0))
    return tile


def headline_tile(text, alpha=1.0):
    """The hook's big words, top third: lines split by 「／」, the last line red."""
    lines = text.split("／")
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = tfont(96)
    y = round(H * SPEC.get("headline_y", 0.17))
    for k, t in enumerate(lines):
        col = (235, 70, 58) if k == len(lines) - 1 and len(lines) > 1 else (250, 248, 242)
        d.text(((W - f.getlength(t)) / 2, y), t, font=f, fill=col + (int(255 * alpha),), stroke_width=9, stroke_fill=(0, 0, 0, int(255 * alpha)))
        y += 136
    return im


def end_card_film(bg=None):
    im = Image.new("RGBA", (W, H), (6, 6, 8, 255))
    if bg is not None:
        b = np.asarray(bg.convert("RGB").resize((W, H))).astype(np.float32) * 0.28
        im = Image.fromarray(b.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im)
    seal = Image.open(R.STORY.SEAL).convert("RGBA").resize((200, 200), Image.LANCZOS)
    im.alpha_composite(seal, ((W - 200) // 2, 470))
    # end_title: 「上集完」 for a two-part cut
    rows = [(SPEC.get("end_title", "本首完"), tfont(104), (245, 243, 238)), ("追蹤 " + brand["handle"], tfont(80), (255, 92, 76)),
            (SPEC.get("end_question", "下一首，更毛。"), tfont(62), (225, 222, 215)), (brand["disclosure"], tfont(34, TITLE_FONT), (130, 130, 130))]
    y = 760
    for t, f, c in rows:
        d.text(((W - f.getlength(t)) / 2, y), t, font=f, fill=c, stroke_width=4 if f.size >= 60 else 0, stroke_fill=(0, 0, 0))
        y += round(f.size * 1.75)
    return im


def tag_tile(name):
    """Who is speaking, the first time we see them: a small red-ruled name in the upper left."""
    f = tfont(80)
    w = int(f.getlength(name)) + 56
    tile = Image.new("RGBA", (w + 20, 132), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rectangle([0, 10, 11, 122], fill=(200, 50, 42, 255))
    d.text((34, 12), name, font=f, fill=(250, 248, 242), stroke_width=6, stroke_fill=(0, 0, 0))
    return tile


_icons = {}


def _icon(size):
    if size not in _icons:
        _icons[size] = Image.open(BRAND / brand["logo"]).convert("RGBA").resize((size, size), Image.LANCZOS)
    return _icons[size]


def title_tile(alpha):
    t = R.STORY.TITLE
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = tfont(140, SUB_FONT)
    x = (W - f.getlength(t)) / 2
    d.text((x, 600), t, font=f, fill=(250, 248, 242, int(255 * alpha)), stroke_width=10, stroke_fill=(0, 0, 0, int(235 * alpha)))
    f2 = tfont(58, SUB_FONT)
    s = brand["name"]
    icon = _icon(84)
    rw = 84 + 18 + f2.getlength(s); x0 = (W - rw) / 2
    ic = icon.copy(); ic.putalpha(ic.split()[3].point(lambda v: int(v * alpha)))
    im.alpha_composite(ic, (round(x0), 832))
    d.text((x0 + 102, 838), s, font=f2, fill=(245, 242, 236, int(255 * alpha)), stroke_width=4, stroke_fill=(0, 0, 0, int(220 * alpha)))
    return im


# ---------------------------------------------------------------- timeline
def build():
    tl, t = [], 0.0
    vo_events, dia_events, amb_events, sfx_events, subs = [], [], [], [], []
    for sh in SPEC["shots"]:
        if sh.get("black"):
            tl.append({"kind": "black", "start": t, "dur": sh["black"]}); t += sh["black"]
        lead, gap, tail = sh.get("lead", SPEC.get("lead", 0.35)), sh.get("gap", SPEC.get("gap", 0.32)), sh.get("tail", SPEC.get("tail", 0.6))
        cur = t + lead
        for ln in sh.get("lines", []):
            if isinstance(ln, str):
                a = vo_take(ln)
                d = len(a) / SR
                vo_events.append((cur, a))
                txt = SCRIPT[ln]
                if txt.startswith("「") and txt.endswith("」"):   # a character's line from speak.py: quote every piece
                    pieces = [] if sh.get("nosub") else ["「" + c + "」" for c in chunks(txt[1:-1])]
                else:
                    pieces = [] if sh.get("nosub") else chunks(txt)
                tot = sum(len(c) for c in pieces) or 1
                c0 = cur
                for c in pieces:
                    cd = d * len(c) / tot
                    subs.append((c0, c0 + cd, c, sh.get("big", False), False)); c0 += cd
                cur += d + gap
            elif "sub" in ln:  # a subtitle with no voice of its own (a mouthed line, or one carried by a sound file)
                subs.append((cur, cur + ln["dur"], ln["sub"], sh.get("big", False), True))
                cur += ln["dur"] + gap
            else:  # speech inside the clip's own audio: the clip is placed so it plays at `cur`
                a0, a1 = ln["clip_speech"]
                sh["_clip_start"] = cur - t - (a0 - sh.get("offset", 0.0))
                dia_events.append((cur, sh["clip"], a0, a1, ln.get("gain", 1.0)))
                pieces = chunks(ln["text"].strip("「」"))
                tot = sum(len(c) for c in pieces)
                c0 = cur
                for c in pieces:
                    cd = (a1 - a0) * len(c) / tot
                    subs.append((c0, c0 + cd, "「" + c + "」", sh.get("big", False), True)); c0 += cd
                cur += (a1 - a0) + gap
        dur = sh.get("dur") or max(sh.get("min", 2.0), cur - gap - t + tail if sh.get("lines") else sh.get("min", 2.0))
        sh["_start"], sh["_dur"] = t, dur
        for name, at, g in sh.get("sfx", []):
            sfx_events.append((t + at, name, g))
        if sh.get("music_cut"):   # [a, b] in this shot's seconds (negative = from its end): no music there
            a_, b_ = (x if x >= 0 else dur + x for x in sh["music_cut"])
            if b_ <= a_: b_ = dur   # [-1.5, 0] means the last 1.5 s
            SPEC.setdefault("music_cuts", []).append((t + a_, t + b_))
            SPEC.setdefault("_hush", []).append((t + a_, t + b_))   # the room sound goes too: a real silence
        if sh.get("theme"):   # a music file that starts with this shot (the 鬼唱詩 theme on the end card)
            sfx_events.append((t + sh.get("theme_at", 0.0), "file:" + sh["theme"], sh.get("theme_gain", 1.0)))
        if sh.get("clip") and sh.get("amb", SPEC.get("amb_gain", 0.3)) > 0:
            amb_events.append((t, sh, dur))
        tl.append({"kind": "shot", "sh": sh, "start": t, "dur": dur}); t += dur
    return tl, t, vo_events, dia_events, amb_events, sfx_events, subs


# ---------------------------------------------------------------- pictures
_stills = {}


def still(sh):
    key = sh.get("still") or sh.get("clip0")
    if key not in _stills:
        if sh.get("still"):
            _stills[key] = Image.open(p(sh["still"])).convert("RGB")
        else:
            _stills[key] = Image.fromarray(R.clip_frames(str(p(sh["clip0"])))[0])
    return _stills[key]


FROZEN = {}   # shot id -> frames held on the clip's last frame


def clip_pic(sh, i, n):
    arr = R.clip_frames(str(p(sh["clip"])))
    src_fps = 24
    off = sh.get("offset", 0.0)
    usable = min(len(arr) / src_fps, sh.get("max_t", 99)) - off
    shot = n / FPS
    speed = sh.get("speed") or (1.0 if "_clip_start" in sh else max(sh.get("min_speed", SPEC.get("min_speed", 0.55)), min(1.0, usable / shot)))
    ts = off + (i / FPS - sh.get("_clip_start", 0.0)) * speed
    if ts > off + usable + 0.04:   # past the clip's last usable frame: the picture stands still
        FROZEN[sh["id"]] = FROZEN.get(sh["id"], 0) + 1
    k = int(min(max(ts, 0), off + usable) * src_fps)
    return Image.fromarray(arr[min(len(arr) - 1, k)])


_TFX = []


def _tfx():
    if not _TFX:
        sys.path.insert(0, str(SKILL))
        # title_fx reads the title from GF_TITLE at import and falls back to 上鋪的腳; v9 of 氣窗 shipped with that title
        os.environ["GF_TITLE"] = SPEC["title"]
        import title_fx
        _TFX.append(title_fx)
    return _TFX[0]


def lift(img, g):
    if not g or g == 1:
        return img
    a = np.asarray(img).astype(np.float32) / 255
    return Image.fromarray((np.clip(a ** g, 0, 1) * 255).astype(np.uint8))


def _soft_mask(x0, y0, x1, y1, feather=0.06):
    yy, xx = np.mgrid[0:H, 0:W]
    fx, fy = xx / W, yy / H
    mx = np.clip(np.minimum(fx - x0, x1 - fx) / feather, 0, 1)
    my = np.clip(np.minimum(fy - y0, y1 - fy) / feather, 0, 1)
    return (mx * my)[..., None].astype(np.float32)


def _flicker(n, lo=0.12, hi=0.85, seed=3):
    """A slow random opacity (0.12-0.85) with a few quick drop-outs: there, not there."""
    rng = np.random.default_rng(seed)
    pts = rng.uniform(lo, hi, n // 10 + 3)
    x = np.interp(np.arange(n) / 10, np.arange(len(pts)), pts)
    for k in rng.choice(n, max(1, n // 40), replace=False):
        x[k:k + 3] = lo * 0.5
    return x


def _pop(n, seed=5):
    """There, not there: the ghost is either fully in the frame or gone, for 4-18 frames at a time, mostly there."""
    rng = np.random.default_rng(seed)
    x = np.zeros(n); k = 0; on = True
    while k < n:
        ln = int(rng.integers(8, 22) if on else rng.integers(2, 7))
        x[k:k + ln] = 1.0 if on else 0.0
        k += ln; on = not on
    return x


def _breathe(n, gb, seed=9):
    """若隱若現 that breathes: the opacity drifts between lo and hi with 0.3-0.6 s fades and short holds, and for the
    last `hold` seconds stays at its clearest."""
    rng = np.random.default_rng(seed)
    lo, hi, hold = gb.get("lo", 0.0), gb.get("hi", 0.6), gb.get("hold", 1.5)
    x = np.zeros(n); k = 0; level = lo
    end = n - int(hold * FPS)
    while k < end:
        target = hi * rng.uniform(0.55, 1.0) if level < (lo + hi) / 2 else lo + (hi - lo) * rng.uniform(0, 0.2)
        fade = int(rng.uniform(0.3, 0.6) * FPS); stay = int(rng.uniform(0.15, 0.6) * FPS)
        seg = np.linspace(level, target, fade)
        x[k:k + fade] = seg[: max(0, min(fade, n - k))]; k += fade
        x[k:k + stay] = target; k += stay; level = target
    if end < n:
        r = max(1, min(n - end, int(0.4 * FPS)))
        x[end:end + r] = np.linspace(x[max(0, end - 1)], hi, r)
        x[end + r:] = hi
    return x[:n]


def shot_frames(item, subs):
    sh, n = item["sh"], round(item["dur"] * FPS)
    if sh.get("ghost_blend"):
        gbm = sh["ghost_blend"].get("mode")
        if gbm == "curve":   # [[t, opacity], ...] in shot seconds, smoothly interpolated (a negative t counts from the end)
            pts = [((t if t >= 0 else item["dur"] + t) * FPS, a) for t, a in sh["ghost_blend"]["curve"]]
            xs, ys = zip(*sorted(pts))
            sh["ghost_blend"]["_noise"] = np.interp(np.arange(n), xs, ys)
        else:
            sh["ghost_blend"]["_noise"] = _pop(n) if gbm == "pop" else _breathe(n, sh["ghost_blend"]) if gbm == "breathe" else _flicker(n)
    fxs = sh.get("fx", [])
    t0 = item["start"]

    zoom = sh.get("zoom", 0.0)          # start this much tighter (cuts the frame's edges away)
    mot = sh.get("motion") or ("push" if zoom else None)
    amt = sh.get("amt", 0.05 if sh.get("motion") else 0.0)
    foc = tuple(sh.get("focus", (0.5, 0.5)))

    def draw(i):
        if sh.get("end"):
            if "_bg" not in sh and sh.get("bg_clip"):
                arr = R.clip_frames(str(p(sh["bg_clip"])))
                sh["_bg"] = R.frame_crop(Image.fromarray(arr[min(len(arr) - 1, int(sh.get("bg_t", 99) * 24))]), W, H, 0, "push", tuple(sh.get("bg_focus", (0.5, 0.4))), 0, sh.get("bg_zoom", 0))
            base = end_card_film(sh.get("_bg")).convert("RGB")
        elif sh.get("clip"):
            base = clip_pic(sh, i, n)
            if mot:
                base = R.frame_crop(base, W, H, i / max(1, n - 1), mot, foc, amt, zoom)
        else:
            base = R.frame_crop(still(sh), W, H, i / max(1, n - 1), mot or "push", foc, sh.get("amt", 0.05), zoom)
        gb = sh.get("ghost_blend")
        if gb and sh.get("clip"):
            # 若隱若現: inside the region, mix the clip's first frame (nothing there) with the current frame (the
            # ghost there) at a slowly flickering opacity
            first = R.clip_frames(str(p(sh["clip"])))[int(gb.get("ref_t", 0) * 24)]
            cur = np.asarray(base).astype(np.float32)
            f0 = np.asarray(R.frame_crop(Image.fromarray(first), W, H, i / max(1, n - 1), mot, foc, amt, zoom)
                            if mot else Image.fromarray(first).resize((W, H))).astype(np.float32)
            tt_ = i / FPS
            k = 0.0 if tt_ < gb.get("from", 0) else min(1, (tt_ - gb.get("from", 0)) / gb.get("ramp", 1.5))
            fl = gb["_noise"][min(i, len(gb["_noise"]) - 1)]
            alpha = k * fl
            x0, y0, x1, y1 = gb["region"]
            mask = gb.setdefault("_mask", _soft_mask(x0, y0, x1, y1, gb.get("feather", 0.06)))
            if gb.get("tint"):   # the ghost layer in the climax's grey-blue
                cur = cur * np.array(gb["tint"], dtype=np.float32)
            if gb.get("scale"):   # shrink the ghost: cut it out where it differs from the empty frame, scale it about an anchor
                diff = np.abs(cur - f0).max(axis=2)
                leg = np.clip((diff - 10) / 30, 0, 1)
                leg = np.asarray(Image.fromarray((leg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
                lm = leg[..., None] * mask
                sc = gb["scale"]; ax, ay = gb.get("anchor", (0.5, 0.0))
                def _sc(img_arr, mode):
                    im_ = Image.fromarray(np.clip(img_arr, 0, 255).astype(np.uint8), mode)
                    w2, h2 = round(W * sc), round(H * sc)
                    small = im_.resize((w2, h2), Image.LANCZOS)
                    canvas_ = Image.new(mode, (W, H), 0)
                    canvas_.paste(small, (round(ax * W * (1 - sc)), round(ay * H * (1 - sc))))
                    return np.asarray(canvas_).astype(np.float32)
                cur_s = _sc(cur, "RGB")
                lm_s = _sc(lm[..., 0] * 255, "L")[..., None] / 255
                base = Image.fromarray(np.clip(cur_s * lm_s * alpha + f0 * (1 - lm_s * alpha), 0, 255).astype(np.uint8))
            elif gb.get("outside_ref"):   # the ghost only ever shows inside the region: everywhere else is the empty frame
                base = Image.fromarray(np.clip(cur * mask * alpha + f0 * (1 - mask * alpha), 0, 255).astype(np.uint8))
            else:
                base = Image.fromarray(np.clip(cur * (1 - mask * (1 - alpha)) + f0 * mask * (1 - alpha), 0, 255).astype(np.uint8))
        base = lift(base, sh.get("lift"))
        pic = R.apply_fx(base, fxs, i, n, base_vig=sh.get("vig", 0.35), grain=sh.get("grain", 5.0), tint=sh.get("tint"))
        dx, dy = R.shake_offset(fxs, i)
        if dx or dy:
            pic = Image.fromarray(np.roll(np.asarray(pic), (dy, dx), axis=(0, 1)))
        if sh.get("title_fx"):   # the poster title, animated (cover/title_fx.py; owner picked 1 霧中浮現)
            k_ = i / FPS
            if k_ <= sh.get("title_fx_dur", 3.5):
                pic = Image.fromarray(_tfx().frame(sh["title_fx"], k_, np.asarray(pic.convert("RGB")), sh.get("title_fx_dur", 3.5)))
        canvas = pic.convert("RGBA")
        tt = t0 + i / FPS
        if sh.get("title"):
            k = i / FPS
            ta, tb = sh["title"] if isinstance(sh["title"], list) else (0, item["dur"])
            if ta <= k <= tb:
                a = min(1, (k - ta) / 0.5) * min(1, max(0, (tb - k) / 0.5))
                canvas.alpha_composite(title_tile(a))
        if sh.get("headline"):
            ha, hb = sh.get("headline_at", [0, item["dur"]])
            k = i / FPS
            if ha <= k <= hb:
                canvas.alpha_composite(headline_tile(sh["headline"], min(1, (k - ha) / 0.15 + (1 if ha == 0 else 0)) * min(1, max(0, (hb - k) / 0.3))))
        if sh.get("tag") and i / FPS < sh.get("tag_sec", 2.5):
            tg = tag_tile(sh["tag"])
            canvas.alpha_composite(tg, (70, round(H * 0.16)))
        live = [s_ for s_ in subs if s_[0] <= tt < s_[1] + 0.05]
        for a0, a1, text, big, said in live[-1:]:   # one subtitle at a time: the newest
            if True:
                tile = sub_tile(text, 80 if big else SPEC.get("sub_size", 64), (255, 236, 200) if said else (250, 250, 248))
                fade = min(1, (tt - a0) / 0.08)
                if fade < 1:
                    tile.putalpha(tile.split()[3].point(lambda v: int(v * fade)))
                R.paste_center(canvas, tile, W / 2, H * sh.get("sub_y", 0.5 if big else SPEC.get("sub_y", 0.705)))
        return canvas.convert("RGB")
    return {"n": n, "draw": draw, "xfade": sh.get("xfade", 0)}


# ---------------------------------------------------------------- sound
def movavg(x, n):
    """Moving average of length n (same length as x), by cumulative sums: np.convolve with a long window is far too slow."""
    n = max(1, int(n))
    c = np.concatenate([[0.0], np.cumsum(x, dtype=np.float64)])
    i = np.arange(len(x)); lo = np.clip(i - n // 2, 0, len(x)); hi = np.clip(i + n - n // 2, 0, len(x))
    return (c[hi] - c[lo]) / np.maximum(1, hi - lo)


def place(out, start, a, gain=1.0):
    s = int(start * SR)
    if s >= len(out):
        return
    e = min(len(out), s + len(a))
    out[s:e] += a[: e - s] * gain


def mixdown(total, vo_events, dia_events, amb_events, sfx_events):
    n = int(total * SR) + SR
    vo = np.zeros((n, 2)); amb = np.zeros((n, 2)); fx = np.zeros((n, 2))
    for start, a in vo_events:
        place(vo, start, a)
    for start, clip, a0, a1, g in dia_events:
        a = audio(clip)[int(a0 * SR): int(a1 * SR)].copy()
        rms = np.sqrt((a ** 2).mean()) + 1e-9
        f = int(SR * 0.03)
        a[:f] *= np.linspace(0, 1, f)[:, None]; a[-f:] *= np.linspace(1, 0, f)[:, None]
        place(vo, start, a * (0.085 / rms) * g)
    for start, sh, dur in amb_events:
        a = audio(sh["clip"])
        off = sh.get("offset", 0.0)
        seg = a[int(off * SR): int((off + dur) * SR)].copy()
        if "_clip_start" in sh:   # a dialogue clip: its speech goes on the voice bus, keep only what is around it
            continue
        if len(seg) == 0:
            continue
        f = min(len(seg) // 2, int(SR * 0.25))
        seg[:f] *= np.linspace(0, 1, f)[:, None]; seg[-f:] *= np.linspace(1, 0, f)[:, None]
        rms = np.sqrt((seg ** 2).mean()) + 1e-9
        place(amb, start, seg * min(1.0, 0.05 / rms) * sh.get("amb", SPEC.get("amb_gain", 0.3)) / 0.3)
    for start, name, g in sfx_events:
        if name.startswith("file:"):
            a = audio(name[5:]).copy()
            a *= 0.12 / (np.sqrt((a ** 2).mean()) + 1e-9)
            fo = int(SR * 1.2); a[-fo:] *= np.linspace(1, 0, fo)[:, None]
            place(fx, start, a * g)
            continue
        x = np.asarray(SFX._make(name, 2.0), dtype=np.float64)
        x = np.stack([x, x], axis=1) if x.ndim == 1 else x
        place(fx, start, x * g)
    # music, ducked under the voice (smoothed side-chain)
    mus = np.zeros((n, 2))
    if SPEC.get("music"):
        m = audio(p(SPEC["music"]) if p(SPEC["music"]).exists() else BRAND / "music" / SPEC["music"])
        m = m * (0.1 / (np.sqrt((m ** 2).mean()) + 1e-9))
        if SPEC.get("music_level"):   # even out a score that starts very quietly: 2-s RMS leveling, at most +12 dB
            env_ = np.sqrt(movavg((m ** 2).mean(axis=1), SR * 2)) + 1e-6
            g_ = np.clip(0.1 / env_, 0.5, 4.0)
            g_ = movavg(g_, SR)
            m = m * g_[:, None]
        reps = math.ceil(n / len(m))
        mus = np.tile(m, (reps, 1))[:n] * SPEC.get("music_gain", 0.22)
        env = np.abs(vo).max(axis=1)
        win = int(SR * 0.3)
        env = movavg(env, win)
        duck = 1 - (1 - SPEC.get("duck", 0.45)) * np.clip(env / 0.01, 0, 1)
        for a, b in SPEC.get("music_cuts", []):   # silence the music here (before a scare)
            duck[int(a * SR): int(b * SR)] = 0.0
        sm = int(SR * 0.15)
        duck = movavg(duck, sm)
        fade = np.ones(n); fo = int(SR * 2.5); fade[-fo:] = np.linspace(1, 0, fo); fade[:int(SR * 0.5)] = np.linspace(0, 1, int(SR * 0.5))
        mus *= (duck * fade)[:, None]
    # the room sound also dips under the voice, so every word stays clear
    venv = movavg(np.abs(vo).max(axis=1), int(SR * 0.3))
    amb *= (1 - 0.5 * np.clip(venv / 0.01, 0, 1))[:, None]
    if SPEC.get("_hush"):
        hush = np.ones(n)
        for a, b in SPEC["_hush"]:
            hush[int(a * SR): int(b * SR)] = 0.0
        amb *= movavg(hush, int(SR * 0.12))[:, None]
    out = vo * SPEC.get("vo_gain", 1.4) + amb + fx + mus
    out = out[: int(total * SR)]
    return out / (np.abs(out).max() + 1e-9) * 0.89, vo[: int(total * SR)]


# ---------------------------------------------------------------- main
def main():
    tl, total, vo_e, dia_e, amb_e, sfx_e, subs = build()
    shots = []
    for it in tl:
        if it["kind"] == "black":
            n = round(it["dur"] * FPS)
            shots.append({"n": n, "draw": lambda i: Image.new("RGB", (W, H), "black")})
        else:
            shots.append(shot_frames(it, subs))
    silent = OUT / "_silent.mp4"
    if REUSE and silent.exists():
        samples = None
    else:
        n, samples = R.render(shots, silent, int(1.5 * FPS))
    audio_mix, vo_only = mixdown(total, vo_e, dia_e, amb_e, sfx_e)
    wav = OUT / "_mix.wav"
    SFX.write_wav(wav, audio_mix)
    SFX.write_wav(OUT / "_vo_only.wav", vo_only / (np.abs(vo_only).max() + 1e-9) * 0.89)
    final = OUT / f"{SPEC.get('out', 'reel_v1')}.mp4"
    R.mux(silent, wav, final)
    if samples:
        R.sheet(samples, OUT / "_frames.jpg")
    # timeline for review: every shot's start, and every subtitle
    with open(OUT / "_timeline.txt", "w", encoding="utf-8") as f:
        for it in tl:
            if it["kind"] == "shot":
                f.write(f"{it['start']:6.2f} {it['dur']:5.2f}  {it['sh']['id']}\n")
        f.write("\n")
        for a0, a1, text, big, said in subs:
            f.write(f"{a0:6.2f}-{a1:6.2f}  {text}\n")
        # the owner: 「有些片段，是定格的圖，很奇怪」. Every frozen tail and every still is listed here.
        held = [f"{k} {v / FPS:.1f}s" for k, v in FROZEN.items() if v / FPS > 0.2]
        stills = [it["sh"]["id"] for it in tl if it["kind"] == "shot" and (it["sh"].get("still") or it["sh"].get("clip0"))]
        f.write(f"\nfrozen tails: {', '.join(held) or 'none'}\nstills: {', '.join(stills) or 'none'}\n")
    print(f"{final}  {total:.1f}s  {len(tl)} shots")
    if held or stills:
        print("WARN frozen tails:", held, "stills:", stills, "(slower min_speed + motion push, a longer clip, or a shorter line)")


if __name__ == "__main__":
    main()
