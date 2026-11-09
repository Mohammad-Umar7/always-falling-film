p = "post/edit.py"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert a in s, "MISSING " + a[:80]
    s = s.replace(a, b, 1)

rep('''def dot_pos(t, x0=240, x1=1680, y=150):''', '''def focus_lines(img, f, center=None, intensity=0.8, color=(0.0, 0.0, 0.0), n=170, clear=0.36):
    """manga focus lines (shuchusen): tapered wedges converging on a clear centre, re-drawn on twos"""
    h, w = img.shape[:2]
    cx, cy = center or (w / 2, h / 2)
    rng = random.Random(f // 2 * 97 + 3)
    ov = np.zeros((h, w), np.float32)
    R = math.hypot(w, h)
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        da = rng.uniform(0.003, 0.012)
        r0 = rng.uniform(clear, clear + 0.3) * min(w, h)
        pts = np.array([(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                        (cx + math.cos(a - da) * R, cy + math.sin(a - da) * R),
                        (cx + math.cos(a + da) * R, cy + math.sin(a + da) * R)], np.int32)
        cv2.fillConvexPoly(ov, pts, rng.uniform(0.55, 1.0), cv2.LINE_AA)
    ov = cv2.GaussianBlur(ov, (0, 0), 0.7)[..., None] * intensity
    return img * (1 - ov) + ov * np.array(color, np.float32)


_SWEEP = {}


def light_sweep(img, t, strength=0.85):
    """anime time-jump: a warm diagonal light band crosses the frame (t 0..1)"""
    h, w = img.shape[:2]
    if (h, w) not in _SWEEP:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        _SWEEP[(h, w)] = (xx + yy * 0.45) / (w + h * 0.45)
    pos = _SWEEP[(h, w)]
    band = np.exp(-((pos - (t * 1.3 - 0.15)) / 0.05) ** 2) * strength * math.sin(math.pi * min(1.0, t))
    return img + band[..., None] * np.array([1.0, 0.9, 0.75], np.float32)


def glint(img, x, y, f, size=30.0, strength=1.0):
    """rotating 4-point star glint on the satellite dot"""
    h, w = img.shape[:2]
    r = int(size + 6)
    x0, y0 = int(x) - r, int(y) - r
    if x0 < 0 or y0 < 0 or x0 + 2 * r >= w or y0 + 2 * r >= h:
        return img
    ov = np.zeros((2 * r, 2 * r), np.float32)
    ang = f * 0.035
    for k in range(4):
        a = ang + k * math.pi / 2
        ln = size * (1.0 if k % 2 == 0 else 0.6)
        cv2.line(ov, (r, r), (int(r + math.cos(a) * ln), int(r + math.sin(a) * ln)), 1.0, 1, cv2.LINE_AA)
    ov = cv2.GaussianBlur(ov, (0, 0), 0.9) * strength
    img = img.copy()
    img[y0:y0 + 2 * r, x0:x0 + 2 * r] += ov[..., None] * np.array([0.85, 0.95, 1.0], np.float32)
    return img


def panel_slam(f, f0, srcs):
    """three slanted manga panels slam in (boy | rocket | father)"""
    k = f - f0
    out = np.ones((H, W, 3), np.float32) * 0.96
    cuts = [(0, 0), (int(W * 0.34) + 46, int(W * 0.34) - 46), (int(W * 0.66) + 46, int(W * 0.66) - 46), (W + 60, W + 60)]
    for i, img in enumerate(srcs):
        (t0, b0), (t1, b1) = cuts[i], cuts[i + 1]
        g = 7
        poly = np.array([(t0 + (g if i else 0), 0), (t1 - g, 0), (b1 - g, H), (b0 + (g if i else 0), H)], np.int32)
        m = np.zeros((H, W), np.uint8)
        cv2.fillConvexPoly(m, poly, 1)
        dy = int(max(0, 4 - k) * 70 * (1 if i % 2 == 0 else -1))       # slide in, alternating directions
        src = np.roll(img, dy, axis=0)
        out = np.where(m[..., None] > 0, src, out)
        cv2.polylines(out, [poly], True, (0.02, 0.02, 0.05), 3, cv2.LINE_AA)
    return out


def fit_panel(img, cx_frac=0.5):
    """crop a source to a vertical slice ~0.4W wide centred at cx_frac, then place it full-height in a WxH canvas"""
    h, w = img.shape[:2]
    sw = int(min(w, h * 0.62))
    c = int(w * cx_frac)
    x0 = max(0, min(w - sw, c - sw // 2))
    sl = cv2.resize(img[:, x0:x0 + sw], (int(sw * H / h), H))
    canvas = np.zeros((H, W, 3), np.float32)
    return sl, canvas


def dot_pos(t, x0=240, x1=1680, y=150):''')

# panels during the launch climb
rep('''    elif kind == "split":
        img = split(f, src[0], src[1], loc, loc, g, ex.get("right_warm", False) or sid == "A2")
        img = draw_divider(img, divider_w(f))''', '''    elif kind == "split":
        img = split(f, src[0], src[1], loc, loc, g, ex.get("right_warm", False) or sid == "A2")
        img = draw_divider(img, divider_w(f))
    if "panels" in ex and ex["panels"][0] <= f <= ex["panels"][1]:
        p0 = ex["panels"][0]
        boy = grade(load("C2L", 1 + (f - p0) % 96, (960, 1080)), "night")
        fa = grade(load("C2R", 1 + (f - p0) % 96, (960, 1080)), "warm")
        rk = img
        def place(src, frac):
            sl, canvas = fit_panel(src, frac)
            ww = sl.shape[1]
            return sl, ww
        sl_b, wb = place(boy, 0.45)
        sl_f, wf = place(fa, 0.35)
        L = np.zeros((H, W, 3), np.float32); L[:, :min(W, wb)] = sl_b[:, :min(W, wb)]
        Rr = np.zeros((H, W, 3), np.float32); xo = W - wf; Rr[:, max(0, xo):] = sl_f[:, max(0, -xo):]
        img = panel_slam(f, p0, [L, rk, Rr])
        img = speed_lines(img, f, 0.45)''')

# FX hooks: glint on dots, focus lines, sweeps
rep('''            img = draw_dot(img, x, y, trail=(px, py))''', '''            img = draw_dot(img, x, y, trail=(px, py))
            img = glint(img, x, y, f)''')
rep('''            x, y = dot_pos(t, x0=1100, x1=1860)
            img = draw_dot(img, x, y)''', '''            x, y = dot_pos(t, x0=1100, x1=1860)
            img = draw_dot(img, x, y)
            img = glint(img, x, y, f, strength=0.7)''')
rep('''    if ex.get("rain_left"):''', '''    for (a_, b_, cx_, cy_, it_, col_) in TL.FOCUS:
        if a_ <= f <= b_:
            fade_ = 1.0 if f - a_ < (b_ - a_) * 0.6 else max(0.0, (b_ - f) / max(1.0, (b_ - a_) * 0.4))
            img = focus_lines(img, f, (cx_, cy_), it_ * fade_, col_)
    for c_ in TL.SWEEPS:
        if c_ <= f < c_ + 10:
            img = light_sweep(img, (f - c_) / 10.0)
    if ex.get("rain_left"):''')
open(p, "w", encoding="utf-8").write(s)

p = "post/timeline.py"
s = open(p, encoding="utf-8").read()
rep('''    ("C3b", 1489, 1584, "full", "C3b", {"grade": "day", "speed": (1489, 1584, 0.5), "shake": (1489, 1584, 4)}),''',
    '''    ("C3b", 1489, 1584, "full", "C3b", {"grade": "day", "speed": (1489, 1584, 0.5), "shake": (1489, 1584, 4), "panels": (1546, 1584)}),''')
s += '''
# anime FX: manga focus lines (start, end, cx, cy, intensity, colour) and time-jump light sweeps (cut frames)
FOCUS = [
    (5758, 5784, 960, 470, 0.75, (0.0, 0.0, 0.0)),     # I3: the streak appears - both look up
    (5883, 5896, 960, 540, 0.9, (1.0, 0.95, 0.85)),    # I4: the divider burns
    (6121, 6136, 960, 520, 0.55, (0.02, 0.02, 0.08)),  # J1: the son finds his father in the lane
]
SWEEPS = [2401, 2545, 2689, 2881, 3121, 3361, 3601, 3841]
'''
open(p, "w", encoding="utf-8").write(s)
import ast
ast.parse(open("post/edit.py").read()); ast.parse(s)
print("fx patched")
