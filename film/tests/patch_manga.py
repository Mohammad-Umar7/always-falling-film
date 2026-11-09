"""V2 post: manga-panel split (slanted ink-bordered panels on a starry gap), side captions, year headers,
hand-drawn line boil + paper grain + ink edges."""
ROOT = __file__.rsplit("tests", 1)[0]
p = ROOT + "post/edit.py"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert a in s, "MISSING " + a[:90]
    s = s.replace(a, b, 1)


# ---------------------------------------------------------------- split as manga panels
a = s.index("def draw_divider(img, hw, alpha=1.0):")
b = s.index("def split(f, ls, rs, lf, rf, kind, right_warm=False):")
s = s[:a] + '''SLANT = 44.0          # px the gutter leans across the frame height (manga panel cut)
_PANEL = {}


def _panel_fields():
    if "d" not in _PANEL:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        xc = 960.0 + SLANT * (0.5 - yy / H)
        _PANEL["d"] = xx - xc                                   # signed distance (px) from the slanted centre line
        # the gap is a strip of night sky: deep gradient + small stars (only the satellite crosses it)
        rng = np.random.default_rng(1975)
        sky = np.zeros((H, W, 3), np.float32)
        t = (yy / H)[..., None]
        sky[:] = np.array([0.03, 0.035, 0.09], np.float32) * (1 - t) + np.array([0.06, 0.05, 0.14], np.float32) * t
        for _ in range(420):
            x, y = rng.integers(0, W), rng.integers(0, H)
            br = rng.uniform(0.35, 1.0)
            cv2.circle(sky, (int(x), int(y)), 1 if br < 0.8 else 2, (br * 0.9, br * 0.92, br), -1, cv2.LINE_AA)
        _PANEL["sky"] = sky
    return _PANEL["d"], _PANEL["sky"]


def draw_divider(img, hw, alpha=1.0):
    """Two slanted manga panels with ink-and-paper borders; the gap between them widens over the years."""
    if alpha <= 0:
        return img
    d, sky = _panel_fields()
    g = max(4.0, hw)
    gap = np.clip((g - np.abs(d)) / 1.2 + 0.5, 0, 1)                        # 1 inside the gap (AA edge)
    border = np.clip((g + 4.5 - np.abs(d)) / 1.2 + 0.5, 0, 1) - gap        # 4.5 px paper-white border
    ink = np.clip((g + 6.5 - np.abs(d)) / 1.2 + 0.5, 0, 1) - gap - border  # 2 px ink line outside the border
    side = (d > 0)[..., None]
    paper = np.where(side, np.array([1.0, 0.95, 0.88], np.float32), np.array([0.92, 0.95, 1.0], np.float32))
    out = img * (1 - gap[..., None] * alpha) + sky * (gap[..., None] * alpha)
    out = out * (1 - border[..., None] * alpha) + paper * (border[..., None] * alpha)
    out = out * (1 - ink[..., None] * 0.85 * alpha)
    return out


''' + s[b:]

# ---------------------------------------------------------------- captions + year headers
rep('''def text_overlay(img, f):
    items = []''', '''def caption_box(d, x, y, txt, fn, align="left", alpha=1.0, tag_col=None):
    """manga caption: paper box, ink border, small coloured tab"""
    tw = d.textlength(txt, font=fn)
    pad_x, pad_y = 16, 9
    bw, bh = tw + pad_x * 2 + (10 if tag_col else 0), fn.size + pad_y * 2
    x0 = x if align == "left" else (x - bw if align == "right" else x - bw / 2)
    a = int(255 * alpha)
    d.rectangle([x0 + 4, y + 4, x0 + bw + 4, y + bh + 4], fill=(0, 0, 0, int(90 * alpha)))
    d.rectangle([x0, y, x0 + bw, y + bh], fill=(248, 244, 234, a), outline=(16, 14, 22, a), width=3)
    tx = x0 + pad_x
    if tag_col:
        d.rectangle([x0 + 9, y + 9, x0 + 15, y + bh - 9], fill=tag_col + (a,))
        tx += 10
    d.text((tx, y + pad_y - 2), txt, font=fn, fill=(18, 16, 26, a))


def text_overlay(img, f):
    items = []''')
rep('''    subs = [s for s in TL.SUBS if s[0] <= f <= s[1]]
    counter = TL.H1_COUNTER[0] <= f <= TL.H1_COUNTER[1]
    if not items and not subs and not counter:
        return img''', '''    subs = [s for s in TL.SUBS if s[0] <= f <= s[1]]
    counter = TL.H1_COUNTER[0] <= f <= TL.H1_COUNTER[1]
    labels = [l for l in TL.LABELS if l[0] <= f <= l[1]]
    if not items and not subs and not counter and not labels:
        return img''')
rep('''    d = ImageDraw.Draw(ov)
    for (a, b, txt, where, style) in items:''', '''    d = ImageDraw.Draw(ov)
    for (a, b, lt, rt) in labels:
        al = min(1.0, (f - a) / 10.0, (b - f) / 10.0)
        fn = font(F_SUB, 27)
        if lt:
            caption_box(d, 30, 28, lt, fn, "left", al, tag_col=(70, 120, 230))
        if rt:
            caption_box(d, W - 30, 28, rt, fn, "right", al, tag_col=(235, 140, 60))
    for (a, b, txt, where, style) in items:''')
# year/date stamps over a split become a chapter header at the top centre (in the gap)
rep('''            if style == "stamp":
                y = 70
                x = 1040 if where == "br_half" else 70''', '''            if style == "stamp" and where == "tc":
                fn2 = font(F_TITLE, 44)
                al = min(1.0, (f - a) / 8.0) * fade
                tw2 = d.textlength(txt, font=fn2)
                bx0, by0 = (W - tw2) / 2 - 22, 96
                d.rectangle([bx0, by0, bx0 + tw2 + 44, by0 + 66], fill=(10, 10, 20, int(225 * al)), outline=(244, 238, 226, int(255 * al)), width=3)
                d.text(((W - tw2) / 2, by0 + 6), txt, font=fn2, fill=(250, 244, 230, int(255 * al)))
                continue
            if style == "stamp":
                y = 70
                x = 1040 if where == "br_half" else 70''')

# ---------------------------------------------------------------- hand-drawn look
rep('''def dot_pos(t, x0=240, x1=1680, y=150):''', '''_DRAW = {}


def line_boil(img, f, amp=1.05):
    """hand-drawn 'living line': a smooth random warp redrawn every 2 frames (flat colour areas don't move,
    only edges wobble a little - like lines traced by hand on each drawing)"""
    h, w = img.shape[:2]
    if "grid" not in _DRAW:
        gy, gx = np.mgrid[0:h, 0:w].astype(np.float32)
        _DRAW["grid"] = (gx, gy)
    gx, gy = _DRAW["grid"]
    rng = np.random.default_rng((f // 2) * 7919 + 13)
    cw, ch = w // 48 + 2, h // 48 + 2
    dx = cv2.resize(rng.standard_normal((ch, cw)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC) * amp
    dy = cv2.resize(rng.standard_normal((ch, cw)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC) * amp
    return cv2.remap(img, gx + dx, gy + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def ink_edges(img, strength=0.42, lo=0.06, hi=0.2):
    """trace contour edges in ink (geometry edges that have no outline mesh get a drawn line too)"""
    l = cv2.GaussianBlur(lum(img), (0, 0), 0.8)
    gx = cv2.Sobel(l, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(l, cv2.CV_32F, 0, 1, ksize=3)
    m = np.sqrt(gx * gx + gy * gy)
    e = np.clip((m - lo) / (hi - lo), 0, 1)
    return img * (1 - e[..., None] * strength) + e[..., None] * strength * np.array([0.03, 0.025, 0.06], np.float32)


def paper(img, k=0.045):
    """drawing paper: fine static fibre grain (multiplied)"""
    h, w = img.shape[:2]
    if "paper" not in _DRAW:
        rng = np.random.default_rng(42)
        n = rng.standard_normal((h, w)).astype(np.float32)
        fib = cv2.GaussianBlur(n, (0, 0), sigmaX=6.0, sigmaY=0.6) * 2.2 + cv2.GaussianBlur(n, (0, 0), 0.8) * 0.6
        fib = (fib - fib.mean()) / (fib.std() + 1e-6)
        _DRAW["paper"] = (1.0 + fib * 0.5).astype(np.float32)
    return img * (1 - k + k * _DRAW["paper"][..., None])


def dot_pos(t, x0=240, x1=1680, y=150):''')
# apply: ink edges + line boil on the picture (before text), paper over everything except black cards
rep('''    if kind not in ("title", "credits", "black"):
        img = vignette(img, 0.3)
        img = grain(img, f, 0.011)''', '''    if kind not in ("title", "credits", "black"):
        if TL.STYLE.get("ink", True):
            img = ink_edges(np.clip(img, 0, 1.5))
        if TL.STYLE.get("boil", True):
            img = line_boil(img, f)
        img = vignette(img, 0.3)
        if TL.STYLE.get("paper", True):
            img = paper(img)
        img = grain(img, f, 0.008)''')
open(p, "w", encoding="utf-8").write(s)

# ---------------------------------------------------------------- timeline: labels, header stamps, style flags
p = ROOT + "post/timeline.py"
t = open(p, encoding="utf-8").read()
for a_, b_ in [
    ('''    (1290, 1340, "ABU DHABI · 1975", "br_half", "stamp"),\n''', ''),
    ('''    (1360, 1436, "19 APRIL 1975", "bl", "stamp"),''', '''    (1360, 1436, "19 APRIL 1975", "tc", "stamp"),'''),
    ('''    (2410, 2530, "1976", "bl", "stamp"),''', '''    (2410, 2530, "1976", "tc", "stamp"),'''),
    ('''    (2890, 3110, "1977", "bl", "stamp"),''', '''    (2890, 3110, "1977", "tc", "stamp"),'''),
    ('''    (3130, 3350, "1979", "bl", "stamp"),''', '''    (3130, 3350, "1979", "tc", "stamp"),'''),
    ('''    (3370, 3590, "1980", "bl", "stamp"),''', '''    (3370, 3590, "1980", "tc", "stamp"),'''),
]:
    assert a_ in t, "TL MISSING " + a_[:50]
    t = t.replace(a_, b_, 1)
t += """
# who is where: manga caption boxes on each side of the split (start, end, left, right)
LABELS = [
    (112, 288, "THE SON", "THE FATHER"),
    (1266, 1344, "HYDERABAD · THE SON", "ABU DHABI · THE FATHER"),
    (1345, 1440, "HYDERABAD · THE SON", "ABU DHABI · THE FATHER"),
    (2401, 4560, "HYDERABAD · THE SON", "ABU DHABI · THE FATHER"),
    (5161, 5352, "HYDERABAD · THE SON, 1992", "THE FATHER"),
    (5713, 5880, "THE SON", "THE FATHER"),
]

# hand-drawn look switches
STYLE = {"ink": True, "boil": True, "paper": True}
"""
open(p, "w", encoding="utf-8").write(t)
import ast
ast.parse(s)
ast.parse(t)
print("manga split + captions + drawn look patched")
