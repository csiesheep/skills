"""數字卡與封面（1080x1920，遊戲的米紙、墨色、朱紅）。

    py -X utf8 cards.py stats <reel>/cards/stats.png <spec.json>
        spec：{"kicker": "遊戲模擬的", "title": "明清女性",
               "rows": [["17 歲", "出嫁年齡的中位數"], ["82%", "的母親，失去過孩子"], ...],      # 最多 4 列
               "note": ["模擬 2 萬個明清女性（活過 15 歲的 12,899 人）", "遊戲模擬，不是史料統計"]}
    py -X utf8 cards.py cover <reel>/out/reel_cover.jpg "古代女生的一生" "是怎麼過的？" <reel>/portraits/age03_c.png:3 歲 ... (4 張)
        四格肖像封面：大標、副標、2x2 肖像各附年紀。
數字卡上的數字只能來自引擎模擬（life.mjs 或自寫的統計），而且一定要寫「遊戲模擬，不是史料統計」。
"""
import json
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
SERIF = "C:/Windows/Fonts/NotoSerifTC-VF.ttf"
KAI = "C:/Windows/Fonts/kaiu.ttf"
PAPER, INK, INK2, INK3, SEAL = (239, 230, 210), (31, 26, 20), (77, 68, 56), (107, 96, 77), (150, 36, 28)


def f(sz, path=SERIF, bold=True):
    x = ImageFont.truetype(path, sz)
    if path == SERIF:
        try:
            x.set_variation_by_name("Black" if bold else "Regular")
        except Exception:
            pass
    return x


def stats(out, spec):
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle([40, 40, W - 40, H - 40], outline=INK, width=4)
    d.rectangle([56, 56, W - 56, H - 56], outline=(201, 186, 154), width=2)
    d.text((W / 2, 260), spec.get("kicker", "遊戲模擬的"), font=f(64, bold=False), anchor="mm", fill=INK2)
    d.text((W / 2, 370), spec["title"], font=f(120, KAI), anchor="mm", fill=INK)
    y = 600
    for big, small in spec["rows"][:4]:
        d.text((W / 2, y), big, font=f(150, KAI), anchor="mm", fill=(179, 38, 30))
        d.text((W / 2, y + 120), small, font=f(56, bold=False), anchor="mm", fill=INK)
        y += 300
    for k, line in enumerate(spec.get("note", ["遊戲模擬，不是史料統計"])[-2:]):
        d.text((W / 2, H - 150 + 55 * k), line, font=f(38, bold=False), anchor="mm", fill=INK3)
    im.save(out)
    print(out)


def cover(out, title, sub, items):
    bg = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(bg)
    d.text((W / 2, 170), title, font=f(118, KAI), anchor="mm", fill=INK)
    d.text((W / 2, 290), sub, font=f(84, KAI), anchor="mm", fill=SEAL)
    cw, ch = 470, 588
    gx, y0 = (W - 2 * cw) // 3, 390
    for i, item in enumerate(items[:4]):
        path, lab = item.rsplit(":", 1)
        im = Image.open(path).convert("RGB")
        s = max(cw / im.width, ch / im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        im = im.crop(((im.width - cw) // 2, 0, (im.width - cw) // 2 + cw, ch))
        x, y = gx + (i % 2) * (cw + gx), y0 + (i // 2) * (ch + 100)
        bg.paste(im, (x, y))
        d.rectangle([x - 3, y - 3, x + cw + 2, y + ch + 2], outline=(140, 40, 30), width=3)
        d.text((x + cw / 2, y + ch + 46), lab, font=f(54, KAI), anchor="mm", fill=SEAL)
    d.text((W / 2, H - 70), "《生在中國》網頁遊戲", font=f(44, bold=False), anchor="mm", fill=INK2)
    bg.save(out, quality=92)
    print(out)


if __name__ == "__main__":
    if sys.argv[1] == "stats":
        stats(sys.argv[2], json.loads(open(sys.argv[3], encoding="utf-8").read()))
    elif sys.argv[1] == "cover":
        cover(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
    else:
        print(__doc__)
