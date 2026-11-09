"""tile timeline stills (final/stills/NNNNN.png) into labelled contact sheets for auditing"""
import sys, os, cv2, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frames = [int(f) for f in sys.argv[1].split(",")]
out = sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 2
w = int(sys.argv[4]) if len(sys.argv) > 4 else 960
tiles = []
for f in frames:
    im = cv2.imread(os.path.join(ROOT, "final", "stills", f"{f:05d}.png"))
    h = int(im.shape[0] * w / im.shape[1])
    im = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
    cv2.putText(im, str(f), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 4)
    cv2.putText(im, str(f), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    tiles.append(im)
while len(tiles) % cols:
    tiles.append(np.zeros_like(tiles[0]))
rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
cv2.imwrite(out, np.vstack(rows))
print(out)
