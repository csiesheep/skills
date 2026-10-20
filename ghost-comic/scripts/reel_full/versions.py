"""Builds the shot list and sound events for each version from the story script."""
from PIL import Image, ImageFilter

import story_name_call as S

W, H, FPS = 1080, 1920, 30
SAFE_TOP, SAFE_BOTTOM, SAFE_L, SAFE_R = 270, 1470, 90, 960


def reading_order(R):
    out = []
    for pi, page in enumerate(R.BOARD["pages"], 1):
        for cell, _ in R.mg.page_cells(R.BOARD, page):
            out.append((pi, cell["id"]))
    return out


def plain(text):
    return text.replace("{", "").replace("}", "")


class Timeline:
    def __init__(self):
        self.shots, self.events, self.ducks, self.t, self.times = [], [], [], 0.0, {}

    def shot(self, n, draw, xfade=0, pid=None):
        if pid and pid not in self.times:
            self.times[pid] = [self.t, self.t + n / FPS]
        elif pid:
            self.times[pid][1] = self.t + n / FPS
        self.shots.append(dict(n=n, draw=draw, xfade=xfade))
        self.t += n / FPS

    def sfx(self, at, name, gain, dur=1.0, pan=0.0):
        self.events.append((at, name, dur, gain, pan))

    def black(self, sec):
        if sec:
            blk = Image.new("RGB", (W, H), "black")
            self.shot(int(sec * FPS), lambda i: blk)

    def beds(self, order):
        ids = [p for _, p in order]

        def shown(pid, forward):
            # a panel left out of this version: use the nearest one that is in it, inside the range
            k = ids.index(pid)
            rng = ids[k:] if forward else ids[:k + 1][::-1]
            return next((x for x in rng if x in self.times), None)
        for a, b, name, gain in S.BEDS:
            a2, b2 = shown(a, True), shown(b, False)
            if a2 and b2 and ids.index(a2) <= ids.index(b2):
                st, en = self.times[a2][0], self.times[b2][1]
                self.sfx(st, name, gain, en - st)


def card_shot(T, R, img, sec, fade=10, sound=None):
    rgb = img.convert("RGB"); blk = Image.new("RGB", (W, H), "black")
    if sound:
        T.sfx(T.t, sound, 0.4)
    T.shot(int(sec * FPS), lambda i: Image.blend(blk, rgb, min(1, (i + 1) / fade)))


# ======================================================================== V1 漫動畫
def build_v1(R):
    T = Timeline()
    BY, BH = 190, 1190
    tbox = (SAFE_L, SAFE_TOP - BY + 10, SAFE_R, BH - 40)   # bubbles stay on the picture, inside the safe area
    BASE = 44
    CPS = 9.5

    def picture(img, cell, o, i, n):
        t = i / max(1, n - 1)
        mot = o.get("motion", "push")
        pic = R.frame_crop(img, W, BH, t, mot, tuple(cell.get("focus", (0.5, 0.5))), 0.07)
        pic = R.apply_fx(pic, o.get("fx", []), i, n, base_vig=0.5)
        f = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        dx, dy = R.shake_offset(o.get("fx", []), i)
        f.paste(pic, (dx, BY + dy))
        return f

    # cold open
    for pid, sec, _, sfxs in S.HOOK:
        cell, img = R.panel(pid, diegetic=False)
        o = S.V1.get(pid, {})
        tiles = R.bubble_tiles(cell, tbox, BASE + 6)
        n = int(sec * FPS)
        for name, at, gain in sfxs:
            T.sfx(T.t + at, name, gain, sec)

        first = not T.shots

        def draw(i, img=img, cell=cell, o=o, tiles=tiles, n=n, first=first):
            f = picture(img, cell, {"fx": o.get("fx", [])}, i, n)
            for e, tile, bx in tiles:
                R.paste_center(f, R.popped(tile, 1.0 if first else (i + 1) / 6), (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2 + BY)
            return f.convert("RGB")
        T.shot(n, draw, xfade=3)
    card_shot(T, R, R.title_card(), 1.7, sound="whoosh")

    order = reading_order(R)
    last_page = None
    for pi, pid in order:
        if pid in S.V1_SKIP:
            continue
        cell, img = R.panel(pid, diegetic=False)
        o = S.V1.get(pid, {})
        if pid in S.V1_SAY:
            import copy
            cell = copy.deepcopy(cell)
            ents = [e for e in cell.get("text", []) if e["kind"] != "title"]
            for e, txt in zip(ents, S.V1_SAY[pid]):
                e["text"] = txt
        T.black(o.get("black", 0))
        if last_page is not None and pi != last_page:
            T.sfx(T.t, "page", 0.5)
        last_page = pi
        # elements in the order the panel's text is written
        bubbles = iter(R.bubble_tiles(cell, tbox, BASE))
        elems, slot = [], 0
        for e in cell.get("text", []):
            if e["kind"] == "title":
                continue
            if e["kind"] == "narration":
                for chunk in R.split_text(e["text"], 26):
                    elems.append(("nar", R.narration_tile(chunk, maxw=SAFE_R - SAFE_L + 60, sizes=(44, 40), lines=2), 0, len(chunk)))
                    slot += 1
            else:
                _, tile, bx = next(bubbles)
                if cell.get("fill") and e["kind"] == "voice":   # a voice in the dark: big, in the middle
                    tile = tile.resize((tile.width * 2, tile.height * 2), Image.LANCZOS)
                    cx, cy = W / 2, BH / 2
                    bx = [cx - tile.width / 2, cy - tile.height / 2, cx + tile.width / 2, cy + tile.height / 2]
                elems.append(("bub", tile, bx, len(e["text"].replace("\n", ""))))
        lead = 0.9 if o.get("motion") == "snap" else 0.35
        t0 = lead
        timed = []
        for el in elems:
            timed.append((t0, el))
            t0 += 0.27 + 0.35 + el[3] / CPS
        sec = max(t0 + 0.3 + o.get("hold", 0), 1.5)
        n = int(sec * FPS)
        start = T.t
        for name, at, gain in o.get("sfx", []):
            T.sfx(start + at, name, gain, sec)
        for at, el in timed:
            if el[0] == "bub":
                T.sfx(start + at, "pop", 0.5)
        if o.get("duck"):
            T.ducks.append((start - o.get("black", 0), start + sec))

        def draw(i, img=img, cell=cell, o=o, timed=timed, n=n):
            f = picture(img, cell, o, i, n)
            now = i / FPS
            shown = [(at, el) for at, el in timed if now >= at]
            # narration: the latest one in each slot (top / lower) stays
            latest = {}
            for at, el in shown:
                if el[0] == "nar":
                    latest[el[2]] = (at, el)
            for s_, (at, el) in latest.items():
                tile = el[1]
                y = min(BY + BH + tile.height / 2 - 30, SAFE_BOTTOM + 10 - tile.height / 2)
                R.paste_center(f, R.popped(tile, (now - at) * FPS / 8), W / 2, y)
            bubs = [(at, el) for at, el in shown if el[0] == "bub"]
            for k, (at, el) in enumerate(bubs):
                bx = el[2]
                later = [b for b in bubs[k + 1:] if R.overlaps(b[1][2], bx)]
                fade = 1.0 if not later else max(0, 1 - (now - later[0][0]) * FPS / 6)
                if fade <= 0:
                    continue
                R.paste_center(f, R.popped(el[1], (now - at) * FPS / 8, fade), (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2 + BY)
            return f.convert("RGB")
        xf = 0 if o.get("black") or o.get("motion") == "snap" else 5
        T.shot(n, draw, xfade=xf, pid=pid)
    T.black(0.3)
    T.sfx(T.t - 0.3, "drone", 0.45, 3.6)
    card_shot(T, R, R.end_card(), 3.2)
    T.beds(order)
    return T.shots, T.events, T.ducks, 0.30


# ======================================================================== V2 說書快剪
def build_v2(R):
    T = Timeline()
    bg_cache = {}

    def background(pid, img):
        if pid not in bg_cache:
            r = max(W / img.width, H / img.height)
            big = img.resize((int(img.width * r) + 2, int(img.height * r) + 2), Image.BILINEAR)
            x, y = (big.width - W) // 2, (big.height - H) // 2
            bg = big.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(28))
            bg = Image.eval(bg, lambda v: int(v * 0.32))
            bg_cache[pid] = bg
        return bg_cache[pid]

    order = []
    for pid, caption, o in S.V2:
        if pid == "TITLE":
            card_shot(T, R, R.title_card(), 1.5, sound="whoosh")
            continue
        cell, img = R.panel(pid)
        T.black(o.get("black", 0))
        beats = [b for b in caption.split("／")] if caption else [""]
        for bi, beat in enumerate(beats):
            sec = (0.7 + len(plain(beat)) / 8.0) if beat else 1.0
            sec = max(sec, 1.3) + (o.get("hold", 0) if bi == len(beats) - 1 else 0)
            n = int(sec * FPS)
            start = T.t
            if bi == 0:
                for name, at, gain in o.get("sfx", []):
                    T.sfx(start + at, name, gain, sec)
                if o.get("duck"):
                    T.ducks.append((start - o.get("black", 0), start + sec * len(beats)))
                T.sfx(start, "whoosh", 0.12)
            tile = R.kinetic_tile(beat) if beat else None
            full = not beat or o.get("motion") == "snap"

            first = not T.shots

            def draw(i, img=img, cell=cell, o=o, tile=tile, n=n, full=full, pid=pid, bi=bi, first=first):
                t = i / max(1, n - 1)
                focus = tuple(cell.get("focus", (0.5, 0.5)))
                if full:
                    pic = R.frame_crop(img, W, H, t, o.get("motion", "push"), focus, 0.06)
                    f = R.apply_fx(pic, o.get("fx", []), i, n, base_vig=0.7).convert("RGBA")
                    dx, dy = R.shake_offset(o.get("fx", []), i)
                    if dx or dy:
                        g = Image.new("RGBA", (W, H), (0, 0, 0, 255)); g.paste(f, (dx, dy)); f = g
                else:
                    f = background(pid, img).convert("RGBA")
                    pw = W
                    ph = int(img.height * pw / img.width)
                    if ph > 900:
                        ph = 900; pw = int(img.width * ph / img.height)
                    punch = 0.05 * max(0, 1 - i / 6) if bi == 0 else 0
                    pic = R.frame_crop(img, pw, ph, t, "push" if o.get("motion") != "pan_rtl" else "pan_rtl", focus, 0.04, start=punch)
                    pic = R.apply_fx(pic, o.get("fx", []), i, n, base_vig=0.35)
                    py = 300
                    f.paste(pic, ((W - pw) // 2, py))
                    if tile is not None:
                        cy = max(py + ph + 40 + tile.height / 2, 1180)
                        cy = min(cy, SAFE_BOTTOM - tile.height / 2)
                        R.paste_center(f, R.popped(tile, 1.0 if first else (i + 1) / 5), W / 2, cy)
                if full and tile is not None:
                    R.paste_center(f, R.popped(tile, 1.0 if first else (i + 1) / 5), W / 2, 1250)
                return f.convert("RGB")
            T.shot(n, draw, xfade=0, pid=pid)
        order.append((0, pid))
    T.black(0.25)
    card_shot(T, R, R.end_card(), 3.0)
    T.sfx(0, "drone", 0.3, T.t)
    return T.shots, T.events, T.ducks, 0.36


# ======================================================================== V3 電影感
def build_v3(R):
    T = Timeline()
    tint = (0.92, 0.97, 1.05)
    global STRIP
    import numpy as np
    g = np.zeros((H, W, 4), dtype=np.uint8)
    ys = np.arange(H)
    a = np.clip((ys - 1180) / 260, 0, 1) * np.clip((1620 - ys) / 120, 0, 1) * 170
    g[..., 3] = a[:, None].astype(np.uint8)
    STRIP = Image.fromarray(g, "RGBA")
    for pid, sec, sub, o in S.V3:
        if pid == "TITLE":
            if o.get("clip"):
                over = R.title_overlay(); n = int(sec * FPS)
                T.sfx(T.t, "whoosh", 0.4)

                def draw(i, o=o, n=n, over=over):
                    pic = R.clip_frame(o["clip"], i, n)
                    pic = R.apply_fx(pic, [], i, n, base_vig=0.9, grain=7, tint=tint)
                    pic = Image.eval(pic, lambda v: int(v * 0.45)).convert("RGBA")
                    t2 = over.copy(); a = min(1, (i + 1) / 12) * min(1, (n - i) / 10)
                    t2.putalpha(t2.split()[3].point(lambda v: int(v * a)))
                    pic.alpha_composite(t2)
                    return pic.convert("RGB")
                T.shot(n, draw, xfade=12)
            else:
                card_shot(T, R, R.title_card(), sec, fade=14, sound="whoosh")
            continue
        cell, img = R.panel(pid)
        T.black(o.get("black", 0))
        n = int(sec * FPS)
        start = T.t
        for name, at, gain in o.get("sfx", []):
            T.sfx(start + at, name, gain, sec)
        if o.get("duck"):
            T.ducks.append((start - o.get("black", 0), start + sec))
        tile = None
        if sub:
            if o.get("voice"):
                f = R.font(96, weight="Regular")
                txt = " ".join(sub)
                tile = Image.new("RGBA", (int(f.getlength(txt)) + 60, 170), (0, 0, 0, 0))
                from PIL import ImageDraw
                ImageDraw.Draw(tile).text((20, 10), txt, font=f, fill=(240, 240, 245), stroke_width=7, stroke_fill=(0, 0, 0))
            else:
                tile = R.subtitle_tile(sub)
        voice = o.get("voice", False)

        first = not T.shots

        def draw(i, img=img, cell=cell, o=o, tile=tile, n=n, voice=voice, first=first):
            t = i / max(1, n - 1)
            focus = tuple(o.get("focus", cell.get("focus", (0.5, 0.5))))
            if o.get("clip"):
                pic = R.clip_frame(o["clip"], i, n, offset=o.get("clip_offset", 0.0))
            else:
                pic = R.frame_crop(img, W, H, t, o.get("motion", "push"), focus, 0.09)
            pic = R.apply_fx(pic, o.get("fx", []), i, n, base_vig=0.85, grain=7, tint=tint)
            f = pic.convert("RGBA")
            if tile is not None and not voice:
                f.alpha_composite(STRIP)
            dx, dy = R.shake_offset(o.get("fx", []), i)
            if dx or dy:
                g = Image.new("RGBA", (W, H), (0, 0, 0, 255)); g.paste(f, (dx, dy)); f = g
            if tile is not None:
                now = i / FPS
                a = (1.0 if first else min(1, max(0, (now - 0.35) / 0.4))) * min(1, max(0, (n - i) / 9))
                if a > 0:
                    t2 = tile.copy(); t2.putalpha(t2.split()[3].point(lambda v: int(v * a)))
                    if voice:
                        jx = int((i % 5) - 2) if i % 3 == 0 else 0
                        R.paste_center(f, t2, W / 2 + jx, o.get("voice_y", 900))
                    else:
                        R.paste_center(f, t2, W / 2, 1400)
            return f.convert("RGB")
        T.shot(n, draw, xfade=0 if o.get("black") else 12, pid=pid)
    T.black(0.4)
    card_shot(T, R, R.end_card(), 3.2, fade=14)
    # beds over the whole film, heavier than the others
    T.sfx(0, "wind", 0.3, T.t)
    T.sfx(0, "drone", 0.35, T.t)
    if "p11" in T.times and "p20" in T.times:
        a, b = T.times["p11"][0], T.times["p20"][1]
        T.sfx(a, "insects", 0.55, b - a)
    return T.shots, T.events, T.ducks, 0.28


def build(version, R):
    return {"v1": build_v1, "v2": build_v2, "v3": build_v3}[version](R)
