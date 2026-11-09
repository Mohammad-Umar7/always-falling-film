"""raw render frames -> big audit sheets. usage: rawsheet.py out.png SID:frame SID:frame ... (halves 480x540, full 960x540)"""
import sys, os, cv2, numpy as np, glob, bisect
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "renders")
out = sys.argv[1]
tiles = []
for a in sys.argv[2:]:
    sid, f = a.split(":")
    fs = sorted(int(os.path.basename(p)[:4]) for p in glob.glob(os.path.join(R, sid, "*.png")))
    if not fs:
        continue
    i = max(0, bisect.bisect_right(fs, int(f)) - 1)
    im = cv2.imread(os.path.join(R, sid, f"{fs[i]:04d}.png"))
    w = 480 if im.shape[1] < 1500 else 960
    im = cv2.resize(im, (w, 540), interpolation=cv2.INTER_AREA)
    cv2.putText(im, a, (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3)
    cv2.putText(im, a, (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    tiles.append(im)
rows, row, wsum = [], [], 0
for t in tiles:
    if wsum + t.shape[1] > 1920:
        rows.append(row); row, wsum = [], 0
    row.append(t); wsum += t.shape[1]
if row:
    rows.append(row)
rows = [np.hstack(r + ([np.zeros((540, 1920 - sum(x.shape[1] for x in r), 3), np.uint8)] if sum(x.shape[1] for x in r) < 1920 else [])) for r in rows]
cv2.imwrite(out, np.vstack(rows))
print(out, len(tiles))
