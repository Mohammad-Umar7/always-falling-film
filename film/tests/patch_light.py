p = "post/edit.py"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert a in s, "MISSING " + a[:80]
    s = s.replace(a, b, 1)
rep('''def dot_pos(t, x0=240, x1=1680, y=150):''', '''def god_rays(img, strength=0.55, thr=0.82, steps=10, decay=0.86):
    """Shinkai-style crepuscular rays: zoom-blur the brightest region (the sun) outward from its own centre"""
    h, w = img.shape[:2]
    small = cv2.resize(img, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
    l = lum(small)
    if l.max() < thr:
        return img
    y, x = np.unravel_index(np.argmax(cv2.GaussianBlur(l, (0, 0), 6)), l.shape)
    mask = np.clip((l - thr) / (1 - thr), 0, 1)[..., None] * small
    acc = np.zeros_like(mask)
    wgt, sc = 1.0, 1.0
    for _ in range(steps):
        M = np.float32([[sc, 0, x * (1 - sc)], [0, sc, y * (1 - sc)]])
        acc += cv2.warpAffine(mask, M, (w // 4, h // 4), borderMode=cv2.BORDER_CONSTANT) * wgt
        wgt *= decay
        sc *= 1.07
    acc = cv2.resize(cv2.GaussianBlur(acc, (0, 0), 2), (w, h), interpolation=cv2.INTER_LINEAR)
    return img + acc * (strength / steps * 3.0) * np.array([1.0, 0.86, 0.66], np.float32)


def anamorphic(img, thr=0.9, strength=0.35, length=0.35):
    """horizontal anamorphic flare streaks on the hottest highlights (sun, moon, fireball, lamps)"""
    h, w = img.shape[:2]
    small = cv2.resize(img, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
    l = lum(small)
    m = np.clip((l - thr) / (1 - thr), 0, 1)
    if m.max() <= 0:
        return img
    k = int(w // 4 * length) | 1
    streak = cv2.blur(m, (k, 1))
    streak = cv2.blur(streak, (k // 3 | 1, 1))
    streak = cv2.resize(streak, (w, h), interpolation=cv2.INTER_LINEAR)[..., None]
    return img + streak * strength * np.array([0.55, 0.75, 1.0], np.float32)


def motes(img, f, seed, n=26, color=(1.0, 0.86, 0.6), size=(2.0, 5.0), drift=(0.25, -0.35), alpha=0.55, region=None):
    """floating glowing motes (fireflies / dust in light), deterministic and drifting, soft bokeh"""
    h, w = img.shape[:2]
    x0, x1 = region if region else (0, w)
    rng = random.Random(seed)
    ov = np.zeros((h // 2, w // 2), np.float32)
    for i in range(n):
        bx, by = rng.uniform(x0, x1), rng.uniform(0, h)
        sp = rng.uniform(0.4, 1.2)
        ph = rng.uniform(0, 6.28)
        x = (bx + f * drift[0] * sp * 2 + 18 * math.sin(f * 0.03 * sp + ph)) % (x1 - x0) + x0
        y = (by + f * drift[1] * sp * 2 + 10 * math.cos(f * 0.025 * sp + ph)) % h
        r = rng.uniform(*size) / 2
        tw = 0.55 + 0.45 * math.sin(f * 0.12 * sp + ph)
        cv2.circle(ov, (int(x / 2), int(y / 2)), max(1, int(r)), tw * rng.uniform(0.5, 1.0), -1, cv2.LINE_AA)
    ov = cv2.GaussianBlur(ov, (0, 0), 1.6)
    ov = cv2.resize(ov, (w, h), interpolation=cv2.INTER_LINEAR)[..., None]
    return img + ov * alpha * np.array(color, np.float32)


def dot_pos(t, x0=240, x1=1680, y=150):''')
rep('''    if ex.get("rain_left"):''', '''    for (a_, b_, seed_, n_, col_, reg_) in TL.MOTES:
        if a_ <= f <= b_:
            fade_ = min(1.0, (f - a_) / 24.0, (b_ - f) / 24.0)
            img = motes(img, f, seed_, n_, col_, alpha=0.55 * fade_, region=reg_)
    if g == "dusk" or sid in ("C1",):
        img = god_rays(img, 0.5)
    if g in ("dusk", "space", "fire") or sid in ("I3", "I4", "J3", "C1"):
        img = anamorphic(img, 0.88, 0.3 if g != "fire" else 0.22)
    if ex.get("rain_left"):''')
open(p, "w", encoding="utf-8").write(s)

p = "post/timeline.py"
t = open(p, encoding="utf-8").read()
t += '''
# floating light motes: (start, end, seed, count, colour, x-range or None)
MOTES = [
    (505, 1200, 11, 22, (0.75, 0.95, 0.7), None),          # rooftop promise: a few fireflies
    (2689, 2880, 12, 12, (0.75, 0.95, 0.7), (0, 960)),     # E3: the boy holds the note to the sky
    (6500, 6600, 13, 30, (1.0, 0.8, 0.5), None),           # J3: dust in the warm light from the opened door
    (6601, 6840, 14, 18, (0.75, 0.95, 0.7), None),         # K1: the ending, both on the roof
]
'''
open(p, "w", encoding="utf-8").write(t)
import ast
ast.parse(s); ast.parse(t)
print("light fx patched")
