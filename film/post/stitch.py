"""Stitch images side by side: python stitch.py out.png a.png b.png ... [--h 700]"""
import sys
from PIL import Image

args = sys.argv[1:]
h = None
if "--h" in args:
    i = args.index("--h")
    h = int(args[i + 1])
    del args[i:i + 2]
out, files = args[0], args[1:]
ims = [Image.open(f).convert("RGB") for f in files]
if h:
    ims = [im.resize((int(im.width * h / im.height), h)) for im in ims]
W = sum(im.width for im in ims)
Hh = max(im.height for im in ims)
s = Image.new("RGB", (W, Hh), (20, 20, 28))
x = 0
for im in ims:
    s.paste(im, (x, 0))
    x += im.width
s.save(out)
print(out, s.size)
