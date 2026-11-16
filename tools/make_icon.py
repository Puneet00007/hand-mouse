"""Generates handmouse/assets/icon.png + icon.ico + docs/logo.png (run once; output is committed)."""
from PIL import Image, ImageChops, ImageDraw, ImageFilter

S = 2048                       # draw big, downsample for smooth edges
R = int(S * 0.225)
m = int(S * 0.04)

# graphite squircle with a soft top-lit gradient
grad = Image.new("RGBA", (S, S))
gp = ImageDraw.Draw(grad)
top, bot = (46, 46, 50), (14, 14, 16)
for y in range(S):
    t = y / S
    gp.line([(0, y), (S, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,))
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle((m, m, S - m, S - m), radius=R, fill=255)
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
img.paste(grad, (0, 0), mask)

# hairline inner highlight
ring = Image.new("L", (S, S), 0)
ImageDraw.Draw(ring).rounded_rectangle((m, m, S - m, S - m), radius=R, outline=255, width=6)
hl = Image.new("RGBA", (S, S), (255, 255, 255, 36))
img.paste(hl, (0, 0), ImageChops.multiply(ring, mask))

# tracking ring around the pointer tip
d = ImageDraw.Draw(img)
tip = (int(S * 0.345), int(S * 0.235))
for r, a in ((int(S * 0.085), 90), (int(S * 0.145), 40)):
    d.ellipse((tip[0] - r, tip[1] - r, tip[0] + r, tip[1] + r), outline=(255, 255, 255, a), width=7)

# cursor arrow
u = S / 1024
arrow = [(0, 0), (0, 560), (140, 440), (240, 670), (330, 630), (232, 405), (410, 405)]
pts = [(tip[0] + x * u * 0.80, tip[1] + y * u * 0.80) for x, y in arrow]
sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(sh).polygon([(x + 14 * u, y + 26 * u) for x, y in pts], fill=(0, 0, 0, 150))
img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(26 * u)))
d = ImageDraw.Draw(img)
d.polygon(pts, fill=(246, 246, 247, 255))
d.line(pts + [pts[0]], fill=(246, 246, 247, 255), width=int(22 * u), joint="curve")

img.resize((256, 256), Image.LANCZOS).save("handmouse/assets/icon.png")
big = img.resize((1024, 1024), Image.LANCZOS)
big.save("handmouse/assets/icon.ico", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
big.resize((512, 512), Image.LANCZOS).save("docs/logo.png")
print("icons written")
