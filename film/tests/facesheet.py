import cv2, glob, os, sys, numpy as np
name = sys.argv[1]
fs = sorted(glob.glob(f"tests/face/{name}_*.png"))
tiles = []
for f in fs:
    im = cv2.imread(f)
    lab = os.path.basename(f)[len(name) + 1:-4]
    cv2.putText(im, lab, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 3); cv2.putText(im, lab, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
    tiles.append(im)
while len(tiles) % 4: tiles.append(np.zeros_like(tiles[0]))
rows = [np.hstack(tiles[i:i+4]) for i in range(0, len(tiles), 4)]
cv2.imwrite(f"tests/face/sheet_{name}.png", np.vstack(rows)); print(len(fs))
