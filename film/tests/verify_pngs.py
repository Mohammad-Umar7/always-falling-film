"""Decode-check every rendered frame (truncated PNGs pass a size check but fail to decode).
   python tests/verify_pngs.py [--delete]   -> lists bad files per shot; --delete removes them so a repair render refills them"""
import os, sys, glob
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "renders")
bad = {}
n = 0
for d in sorted(glob.glob(os.path.join(R, "*"))):
    sid = os.path.basename(d)
    if sid.startswith("_") or not os.path.isdir(d):
        continue
    for p in sorted(glob.glob(os.path.join(d, "[0-9][0-9][0-9][0-9].png"))):
        n += 1
        try:
            if os.path.getsize(p) == 0:
                raise IOError("empty")
            with Image.open(p) as im:
                im.load()                       # full decode: catches truncated data
        except Exception as e:
            bad.setdefault(sid, []).append(os.path.basename(p))
print(f"checked {n} frames")
for sid, fs in bad.items():
    print(f"BAD {sid}: {len(fs)} -> {fs[:8]}")
print("BAD SHOTS:", len(bad))
if "--delete" in sys.argv:
    for sid, fs in bad.items():
        for f in fs:
            os.remove(os.path.join(R, sid, f))
    print("deleted", sum(len(v) for v in bad.values()), "bad frames")
