"""py -X utf8 sheet.py out.jpg a.png b.png ...  one row of pictures with their names"""
import sys
from PIL import Image, ImageDraw, ImageFont
F = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 26)
out, fs = sys.argv[1], sys.argv[2:]
W, H = 540, 960
cols = min(len(fs), 4); rows = -(-len(fs) // cols)
S = Image.new("RGB", (W * cols, H * rows), "gray"); d = ImageDraw.Draw(S)
for i, f in enumerate(fs):
    x, y = (i % cols) * W, (i // cols) * H
    S.paste(Image.open(f).convert("RGB").resize((W, H)), (x, y)); d.text((x + 5, y + 5), f.split("/")[-1], fill="yellow", font=F)
S.save(out, quality=85)
