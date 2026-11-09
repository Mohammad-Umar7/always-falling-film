"""ALWAYS FALLING — 2D compositor: split screen, anime FX, grade, text. Streams frames into ffmpeg.
usage: python edit.py [--from F] [--to F] [--out path.mp4] [--audio mix.wav] [--workers 8] [--png DIR]"""
import os, sys, math, bisect, argparse, subprocess, random
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import timeline as TL

W, H = 1920, 1080
R = os.path.join(ROOT, "renders")
FONTS = os.path.join(ROOT, "assets", "dl", "fonts")
F_LOG = os.path.join(FONTS, "IBMPlexMono-Medium.ttf")
F_SUB = os.path.join(FONTS, "NotoSans-Variable.ttf")
F_TITLE = os.path.join(FONTS, "ShipporiMincho-SemiBold.ttf")
F_TITLE2 = os.path.join(FONTS, "ShipporiMincho-Regular.ttf")
FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"

_index = {}
_fonts = {}


def font(path, size):
    k = (path, size)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(path, size)
    return _fonts[k]


def frames_of(sid):
    if sid not in _index:
        d = os.path.join(R, sid)
        fs = []
        if os.path.isdir(d):
            for n in os.listdir(d):
                if n.endswith(".png") and n[:-4].isdigit() and os.path.getsize(os.path.join(d, n)) > 0:
                    fs.append(int(n[:-4]))
        _index[sid] = sorted(fs)
    return _index[sid]


def load(sid, f, size=None):
    fs = frames_of(sid)
    if not fs:
        img = np.full((size[1] if size else H, size[0] if size else W, 3), 0.08, np.float32)
        cv2.putText(img, f"MISSING {sid} {f}", (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0.9, 0.3, 0.3), 3)
        return img
    i = bisect.bisect_right(fs, f) - 1
    n = fs[max(0, i)]
    im = cv2.imread(os.path.join(R, sid, f"{n:04d}.png"), cv2.IMREAD_COLOR)
    # EEVEE soft-shadow speckle -> clean cel areas; edges (outlines, ramp steps) survive the bilateral filter
    im = cv2.bilateralFilter(im, 7, 24, 5)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    if size and (im.shape[1], im.shape[0]) != size:
        im = cv2.resize(im, size, interpolation=cv2.INTER_AREA)
    return im


# ------------------------------------------------------------------ grading
LUMW = np.array([0.2126, 0.7152, 0.0722], np.float32)


def lum(img):
    return img @ LUMW


def saturate(img, s):
    l = lum(img)[..., None]
    return l + (img - l) * s


def contrast(img, c=1.08, pivot=0.45):
    return (img - pivot) * c + pivot


_grad_cache = {}


def vgrad(h, w):
    k = (h, w)
    if k not in _grad_cache:
        _grad_cache[k] = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    return _grad_cache[k]


def grade(img, kind):
    if kind == "night":
        img = saturate(img, 1.32)
        g = vgrad(*img.shape[:2])
        img = img + (1 - g) * np.array([0.035, 0.0, 0.07], np.float32) + g * np.array([0.0, 0.02, 0.035], np.float32)
        sh = np.clip(1 - lum(img)[..., None] * 3, 0, 1)
        img = img + sh * np.array([0.02, 0.0, 0.05], np.float32)
        img = contrast(img, 1.06)
    elif kind == "dusk":
        img = saturate(img, 1.25)
        img = contrast(img, 1.05)
        img = img + np.array([0.02, 0.0, 0.015], np.float32)
    elif kind == "day":
        img = saturate(img, 1.18)
        hl = np.clip(lum(img)[..., None] * 1.5 - 0.5, 0, 1)
        img = img + hl * np.array([0.03, 0.015, -0.01], np.float32) + (1 - hl) * np.array([-0.01, 0.01, 0.025], np.float32)
        img = contrast(img, 1.06)
    elif kind == "space":
        img = saturate(img, 1.2)
        img = contrast(img, 1.08, 0.35)
        img = img + np.array([0.0, 0.004, 0.018], np.float32) * (1 - np.clip(lum(img)[..., None] * 4, 0, 1))
    elif kind == "fire":
        img = saturate(img, 1.3)
        img = contrast(img, 1.1, 0.4)
    elif kind == "warm":
        l = lum(img)[..., None]
        amber = l * np.array([1.35, 0.92, 0.55], np.float32) + np.array([0.05, 0.02, 0.0], np.float32)
        img = img * 0.45 + amber * 0.55
        img = saturate(img, 1.25)
    elif kind == "cool":
        img = saturate(img, 1.28)
        img = img + np.array([-0.01, 0.01, 0.04], np.float32)
    return img


def bloom(img, thr=0.72, strength=0.32, sigma=18):
    small = cv2.resize(img, (img.shape[1] // 4, img.shape[0] // 4), interpolation=cv2.INTER_AREA)
    b = np.clip(small - thr, 0, None) / (1 - thr)
    b = cv2.GaussianBlur(b, (0, 0), sigma / 4)
    b = cv2.resize(b, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    return img + b * strength


def chroma(img, amt):
    if amt <= 0:
        return img
    h, w = img.shape[:2]
    out = img.copy()
    for ch, s in ((0, 1 + amt), (2, 1 - amt)):
        M = np.float32([[s, 0, (1 - s) * w / 2], [0, s, (1 - s) * h / 2]])
        out[..., ch] = cv2.warpAffine(img[..., ch], M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return out


def vignette(img, k=0.35):
    h, w = img.shape[:2]
    key = ("vig", h, w)
    if key not in _grad_cache:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2)
        _grad_cache[key] = np.clip(1 - k * np.clip(d - 0.55, 0, None) ** 1.6, 0, 1)[..., None]
    return img * _grad_cache[key]


def grain(img, f, s=0.022):
    rng = np.random.default_rng(f * 7919)
    n = rng.standard_normal((img.shape[0] // 2, img.shape[1] // 2), dtype=np.float32) * s
    n = cv2.resize(n, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)[..., None]
    return img + n


def shake(img, f, amp):
    rng = random.Random(f // 2)
    dx, dy = rng.uniform(-amp, amp), rng.uniform(-amp, amp)
    M = np.float32([[1.02, 0, dx - W * 0.01], [0, 1.02, dy - H * 0.01]])
    return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), borderMode=cv2.BORDER_REFLECT)


# ------------------------------------------------------------------ anime FX
def speed_lines(img, f, intensity=0.6, color=(1.0, 1.0, 1.0), center=None, n=110):
    h, w = img.shape[:2]
    cx, cy = center or (w / 2, h / 2)
    rng = random.Random(f // 2 * 31 + 7)
    ov = np.zeros((h, w), np.float32)
    diag = math.hypot(w, h)
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(0.3, 0.55) * diag * 0.5
        x0, y0 = cx + math.cos(a) * r0, cy + math.sin(a) * r0
        x1, y1 = cx + math.cos(a) * diag, cy + math.sin(a) * diag
        cv2.line(ov, (int(x0), int(y0)), (int(x1), int(y1)), rng.uniform(0.35, 1.0), rng.choice([1, 2, 2, 3, 4]), cv2.LINE_AA)
    ov = cv2.GaussianBlur(ov, (0, 0), 0.8)[..., None] * intensity
    return img * (1 - ov * 0.35) + ov * np.array(color, np.float32)


def impact(img, f, red=False):
    l = lum(img)
    b = (l > np.median(l) * 1.05 + 0.05).astype(np.float32)
    b = cv2.GaussianBlur(b, (0, 0), 0.9)
    inv = 1 - b
    if red:
        out = np.stack([inv * 1.0, inv * 0.12, inv * 0.1], -1) + np.stack([b * 0.05, b * 0.0, b * 0.02], -1)
    else:
        out = np.stack([inv, inv * 0.97, inv * 0.94], -1)
    # black radial lines
    return speed_lines(out, f + 991, intensity=1.0, color=(0.0, 0.0, 0.0), n=70)


def rain(img, f, region=(0, 960)):
    h = img.shape[0]
    rng = random.Random(4242)
    ov = np.zeros(img.shape[:2], np.float32)
    for i in range(420):
        x = rng.uniform(region[0], region[1])
        y0 = rng.uniform(0, h)
        sp = rng.uniform(45, 70)
        y = (y0 + f * sp) % (h + 60) - 30
        L = rng.uniform(18, 34)
        cv2.line(ov, (int(x), int(y)), (int(x - L * 0.18), int(y + L)), rng.uniform(0.25, 0.6), 1, cv2.LINE_AA)
    ov = ov[..., None]
    return img + ov * np.array([0.55, 0.7, 0.95], np.float32) * 0.6


def haze(img, region=(960, 1920), col=(0.9, 0.55, 0.35), k=0.28):
    h = img.shape[0]
    g = np.linspace(0, 1, h, dtype=np.float32)[:, None, None] ** 1.5
    out = img.copy()
    sl = slice(region[0], region[1])
    out[:, sl] = img[:, sl] * (1 - g * k) + np.array(col, np.float32) * g * k
    return out


def draw_dot(img, x, y, glow=1.0, trail=None):
    h, w = img.shape[:2]
    ov = np.zeros((h, w), np.float32)
    if trail is not None:
        tx, ty = trail
        for i in range(12):
            t = i / 12
            cv2.circle(ov, (int(x + (tx - x) * t), int(y + (ty - y) * t)), 1, 0.35 * (1 - t), -1, cv2.LINE_AA)
    cv2.circle(ov, (int(x), int(y)), 3, 1.0, -1, cv2.LINE_AA)
    g = cv2.GaussianBlur(ov, (0, 0), 6) * 2.2 * glow
    core = ov[..., None] * np.array([1.0, 1.0, 1.0], np.float32)
    halo = g[..., None] * np.array([0.6, 0.85, 1.0], np.float32)
    return img + core + halo


def focus_lines(img, f, center=None, intensity=0.8, color=(0.0, 0.0, 0.0), n=170, clear=0.36):
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


def dot_pos(t, x0=240, x1=1680, y=150):
    return x0 + (x1 - x0) * t, y + 70 * math.sin(math.pi * t) * -1 + 70


def streak(img, f, f0, f1):
    t = (f - f0) / max(1, (f1 - f0))
    if t < 0 or t > 1.2:
        return img
    t = min(t, 1.0)
    hx, hy = 120 + (960 - 120) * t, 120 + (360 - 120) * t ** 1.3
    ov = np.zeros(img.shape[:2], np.float32)
    for i in range(60):
        s = i / 60
        x = hx - (hx - 40) * s * 0.9
        y = hy - (hy - 60) * s * 0.9
        cv2.circle(ov, (int(x), int(y)), max(1, int(9 * (1 - s))), 1.0 - s, -1, cv2.LINE_AA)
    g = cv2.GaussianBlur(ov, (0, 0), 10)[..., None]
    core = cv2.GaussianBlur(ov, (0, 0), 1.5)[..., None]
    return img + g * np.array([1.6, 0.6, 0.25], np.float32) + core * np.array([1.2, 1.0, 0.8], np.float32)


# ------------------------------------------------------------------ divider
def divider_w(f):
    ks = TL.DIVIDER
    if f <= ks[0][0]:
        return ks[0][1]
    for (fa, wa), (fb, wb) in zip(ks[:-1], ks[1:]):
        if fa <= f <= fb:
            t = (f - fa) / (fb - fa)
            return wa + (wb - wa) * t
    return ks[-1][1]


def draw_divider(img, hw, alpha=1.0):
    if hw <= 0:
        return img
    x0, x1 = int(960 - hw), int(960 + hw)
    out = img.copy()
    out[:, x0:x1] = out[:, x0:x1] * (1 - alpha)
    # glowing edges: cool on the Hyderabad side, warm on the Abu Dhabi side
    edge = np.zeros(img.shape[:2], np.float32)
    edge[:, max(0, x0 - 1):x0 + 1] = 1.0
    eg = cv2.GaussianBlur(edge, (0, 0), 3)[..., None] * alpha
    edge2 = np.zeros(img.shape[:2], np.float32)
    edge2[:, x1 - 1:min(W, x1 + 1)] = 1.0
    eg2 = cv2.GaussianBlur(edge2, (0, 0), 3)[..., None] * alpha
    return out + eg * np.array([0.35, 0.6, 1.0], np.float32) * 0.8 + eg2 * np.array([1.0, 0.7, 0.35], np.float32) * 0.8


def split(f, ls, rs, lf, rf, kind, right_warm=False):
    L = load(ls, lf, (960, 1080))
    Rr = load(rs, rf, (960, 1080))
    L = grade(L, "night" if kind != "mixed" else "night")
    Rr = grade(Rr, "warm" if right_warm else ("dusk" if kind in ("mixed",) else "night"))
    if not right_warm and kind != "mixed":
        Rr = grade(Rr, "cool") if False else Rr
    return np.concatenate([L, Rr], axis=1)


# ------------------------------------------------------------------ text
def text_overlay(img, f):
    items = []
    for (a, b, txt, where, style) in TL.TEXTS:
        if a <= f <= b:
            items.append((a, b, txt, where, style))
    subs = [s for s in TL.SUBS if s[0] <= f <= s[1]]
    counter = TL.H1_COUNTER[0] <= f <= TL.H1_COUNTER[1]
    if not items and not subs and not counter:
        return img
    pil = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8))
    ov = Image.new("RGBA", pil.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for (a, b, txt, where, style) in items:
        fade = min(1.0, (b - f) / 12.0) if b - f < 12 else 1.0
        if style in ("log", "stamp"):
            n = int((f - a) * (0.9 if style == "log" else 1.4))
            shown = txt[:max(0, n)]
            fn = font(F_LOG, 30 if style == "log" else 26)
            y = {"bl": 960, "bl2": 1000, "bl3": 1040, "br_half": 960}[where]
            x = 1040 if where == "br_half" else 80
            if style == "stamp":
                y = 70
                x = 1040 if where == "br_half" else 70
            col = (210, 236, 255, int(235 * fade)) if style == "log" else (255, 240, 220, int(230 * fade))
            d.text((x + 2, y + 2), shown, font=fn, fill=(0, 0, 0, int(160 * fade)))
            d.text((x, y), shown, font=fn, fill=col)
            if n < len(txt) + 30 and (f // 8) % 2 == 0:
                tw = d.textlength(shown, font=fn)
                d.rectangle([x + tw + 4, y + 4, x + tw + 18, y + 32], fill=col)
        elif style == "end":
            fn = font(F_TITLE, 58)
            a_in = min(1.0, (f - a) / 24.0) * fade
            tw = d.textlength(txt, font=fn)
            y = 470 if where == "center_hi" else 550
            d.text(((W - tw) / 2 + 2, y + 2), txt, font=fn, fill=(0, 0, 0, int(200 * a_in)))
            d.text(((W - tw) / 2, y), txt, font=fn, fill=(255, 246, 230, int(255 * a_in)))
    for (a, b, txt) in subs:
        fn = font(F_SUB, 40)
        a_in = min(1.0, (f - a) / 4.0, (b - f) / 4.0)
        tw = d.textlength(txt, font=fn)
        x, y = (W - tw) / 2, 965
        d.rounded_rectangle([x - 26, y - 8, x + tw + 26, y + 56], radius=16, fill=(6, 6, 14, int(120 * a_in)))
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)):
            d.text((x + ox, y + oy), txt, font=fn, fill=(0, 0, 0, int(200 * a_in)))
        d.text((x, y), txt, font=fn, fill=(255, 255, 255, int(255 * a_in)))
    if counter:
        f0, f1, v0, v1 = TL.H1_COUNTER
        t = (f - f0) / (f1 - f0)
        v = int(v0 + (v1 - v0) * (t ** 2.2))
        fn = font(F_LOG, 46)
        s = f"ORBIT {v:,}"
        d.text((W - 80 - d.textlength(s, font=fn), 60), s, font=fn, fill=(220, 240, 255, 240))
        yr = [y for (ff, y) in TL.H1_YEARS if f >= ff]
        if yr:
            fn2 = font(F_LOG, 30)
            d.text((80, 980), str(yr[-1]), font=fn2, fill=(255, 230, 190, 230))
    pil = Image.alpha_composite(pil.convert("RGBA"), ov).convert("RGB")
    return np.asarray(pil).astype(np.float32) / 255.0


def title_card(f, a, b):
    img = np.zeros((H, W, 3), np.float32)
    rng = random.Random(77)
    for i in range(380):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        br = rng.uniform(0.15, 0.7) * (0.7 + 0.3 * math.sin(f * 0.15 + i))
        cv2.circle(img, (int(x), int(y)), 1, (br * 0.85, br * 0.9, br), -1, cv2.LINE_AA)
    pil = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8)).convert("RGBA")
    ov = Image.new("RGBA", pil.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    txt = "ALWAYS FALLING"
    fn = font(F_TITLE, 120)
    total = d.textlength(txt, font=fn) + 12 * (len(txt) - 1)
    x = (W - total) / 2
    out_a = min(1.0, (b - f) / 10.0)
    for i, ch in enumerate(txt):
        t0 = a + i * 2
        t = max(0.0, min(1.0, (f - t0) / 14.0))
        e = 1 - (1 - t) ** 3
        yoff = -90 * (1 - e)
        alpha = int(255 * e * out_a)
        d.text((x, 470 + yoff), ch, font=fn, fill=(250, 244, 232, alpha))
        x += d.textlength(ch, font=fn) + 12
    # thin rule + the moving dot crossing behind the title
    d.line([(W / 2 - 260, 640), (W / 2 + 260, 640)], fill=(200, 210, 255, int(120 * out_a)), width=1)
    pil = Image.alpha_composite(pil, ov).convert("RGB")
    img = np.asarray(pil).astype(np.float32) / 255.0
    t = (f - a) / (b - a)
    img = draw_dot(img, 300 + 1320 * t, 380 - 40 * math.sin(math.pi * t), trail=(300 + 1320 * t - 60, 380 - 40 * math.sin(math.pi * t) + 4))
    return img


def credits_card(f, a, b):
    img = np.zeros((H, W, 3), np.float32)
    rng = random.Random(91)
    for i in range(300):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        br = rng.uniform(0.1, 0.5)
        cv2.circle(img, (int(x), int(y)), 1, (br * 0.85, br * 0.9, br), -1, cv2.LINE_AA)
    pil = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8)).convert("RGBA")
    ov = Image.new("RGBA", pil.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    t = f - a
    EPI = 96
    if t < EPI:                      # the payoff of "always falling... always missing", alone on black
        fn = font(F_TITLE, 66)
        txt = "This time, it didn't miss."
        al = min(1.0, t / 22.0, (EPI - t) / 18.0)
        tw = d.textlength(txt, font=fn)
        d.text(((W - tw) / 2, H / 2 - 40), txt, font=fn, fill=(255, 244, 226, int(255 * max(0.0, al))))
        pil = Image.alpha_composite(pil, ov).convert("RGB")
        return np.asarray(pil).astype(np.float32) / 255.0
    t -= EPI
    fade = min(1.0, t / 24.0, (b - f) / 30.0)
    step = {"title": 132, "line": 62, "small": 46, "gap": 30}
    y = (H - sum(step.get(k, 30) for k, _ in TL.CREDITS)) / 2
    for kind, txt in TL.CREDITS:
        if kind == "title":
            fn = font(F_TITLE, 100)
            tw = d.textlength(txt, font=fn)
            d.text(((W - tw) / 2, y), txt, font=fn, fill=(250, 244, 232, int(255 * fade)))
        elif kind == "line":
            fn = font(F_SUB, 38)
            tw = d.textlength(txt, font=fn)
            d.text(((W - tw) / 2, y), txt, font=fn, fill=(232, 232, 242, int(245 * fade)))
        elif kind == "small":
            fn = font(F_SUB, 29)
            tw = d.textlength(txt, font=fn)
            d.text(((W - tw) / 2, y), txt, font=fn, fill=(205, 210, 230, int(240 * fade)))
        y += step.get(kind, 30)
    pil = Image.alpha_composite(pil, ov).convert("RGB")
    return np.asarray(pil).astype(np.float32) / 255.0


def burn_mask(f, f0, f1, h=H, w=W):
    """1 = still split (unburnt), 0 = burnt through to the unified frame. Front expands from the divider."""
    t = (f - f0) / max(1, (f1 - f0))
    key = ("noise", h, w)
    if key not in _grad_cache:
        rng = np.random.default_rng(5)
        n = rng.random((h // 16, w // 16)).astype(np.float32)
        n = cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.resize(rng.random((h // 4, w // 4)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        x = np.abs(np.arange(w, dtype=np.float32) - w / 2)[None, :] / (w / 2)
        _grad_cache[key] = np.clip(x * 0.85 + n * 0.25 + n2 * 0.08, 0, 1.2)
    field = _grad_cache[key]
    thr = t * 1.25
    m = np.clip((field - thr) / 0.03, 0, 1)
    edge = np.clip(1 - np.abs(field - thr) / 0.06, 0, 1)
    return m, edge


# ------------------------------------------------------------------ frame assembly
def seq_at(f):
    for s in TL.SEQ:
        if s[1] <= f <= s[2]:
            return s
    return TL.SEQ[-1]


def make_frame(f):
    sid, a, b, kind, src, ex = seq_at(f)
    loc = f - a + 1
    g = ex.get("grade", "night")
    if kind == "black":
        img = np.zeros((H, W, 3), np.float32)
    elif kind == "title":
        img = title_card(f, a, b)
    elif kind == "credits":
        img = credits_card(f, a, b)
    elif kind == "full":
        img = grade(load(src, loc), g)
    elif kind == "split":
        img = split(f, src[0], src[1], loc, loc, g, ex.get("right_warm", False) or sid == "A2")
        img = draw_divider(img, divider_w(f))
    elif kind == "c1":
        sa = ex["split_at"]
        full = grade(load(src[0], loc), "day")
        if f < sa:
            img = full
        else:
            rgt = grade(load(src[1], f - sa + 1, (960, 1080)), "dusk")
            img = np.concatenate([full[:, :960], rgt], axis=1)
            slide = min(1.0, (f - sa) / 6.0)
            if slide < 1.0:
                img[:, 960:] = full[:, 960:] * (1 - slide) + img[:, 960:] * slide
            img = draw_divider(img, divider_w(f) * min(1.0, (f - sa) / 3.0))
            if f - sa < 3:
                img = img + np.where(np.abs(np.arange(W) - 960)[None, :, None] < 6 + (f - sa) * 30, 0.9, 0.0).astype(np.float32)
    elif kind == "i4":
        f0, f1 = ex["burn"]
        base = grade(load(src[2], loc), "night")
        if f <= f1:
            sp = split(f, src[0], src[1], 168, 168, "night", True)
            sp = draw_divider(sp, divider_w(f))
            m, edge = burn_mask(f, f0, f1)
            img = sp * m[..., None] + base * (1 - m[..., None])
            img = img + edge[..., None] * np.array([1.8, 0.75, 0.25], np.float32)
        else:
            img = base
    elif kind == "k1":
        off = ex["split_offset"]
        d0, d1 = ex["dissolve"]
        base = grade(load(src[2], loc), "night")
        if f < d1:
            sp = split(f, src[0], src[1], off + loc, off + loc, "night", f < d0)
            t = 0.0 if f < d0 else (f - d0) / (d1 - d0)
            hw = 100 * (1 - t) if f >= d0 else 100
            sp = draw_divider(sp, hw, alpha=1 - t)
            img = sp * (1 - t) + base * t
        else:
            img = base
        if ex.get("dot") is None:
            pass
    else:
        img = np.zeros((H, W, 3), np.float32)

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
        img = speed_lines(img, f, 0.45)
    # --- FX
    if "dot" in ex:
        d0, d1 = ex["dot"]
        if d0 <= f <= d1:
            t = (f - d0) / (d1 - d0)
            x, y = dot_pos(t)
            px, py = dot_pos(max(0, t - 0.03))
            img = draw_dot(img, x, y, trail=(px, py))
            img = glint(img, x, y, f)
    if "dot_right_only" in ex:
        d0, d1 = ex["dot_right_only"]
        if d0 <= f <= d1:
            t = (f - d0) / (d1 - d0)
            x, y = dot_pos(t, x0=1100, x1=1860)
            img = draw_dot(img, x, y)
            img = glint(img, x, y, f, strength=0.7)
    if kind == "k1" and 6640 <= f <= 6830:
        t = (f - 6640) / 190
        x, y = dot_pos(t)
        img = draw_dot(img, x, y, glow=0.8)
    for (a_, b_, cx_, cy_, it_, col_) in TL.FOCUS:
        if a_ <= f <= b_:
            fade_ = 1.0 if f - a_ < (b_ - a_) * 0.6 else max(0.0, (b_ - f) / max(1.0, (b_ - a_) * 0.4))
            img = focus_lines(img, f, (cx_, cy_), it_ * fade_, col_)
    for c_ in TL.SWEEPS:
        if c_ <= f < c_ + 10:
            img = light_sweep(img, (f - c_) / 10.0, 0.5)
    if ex.get("rain_left"):
        img = rain(img, f)
    if ex.get("haze_right"):
        img = haze(img)
    if "streak_cross" in ex:
        img = streak(img, f, *ex["streak_cross"])
    if "speed" in ex:
        s0, s1, it = ex["speed"]
        if s0 <= f <= s1:
            img = speed_lines(img, f, it)
    if "shake" in ex:
        s0, s1, amp = ex["shake"]
        if s0 <= f <= s1:
            img = shake(img, f, amp)
    if g in ("fire",):
        img = chroma(img, 0.004)
    img = bloom(img, 0.7 if g != "space" else 0.65, 0.34 if g in ("night", "space", "fire") else 0.22)
    if f in ex.get("impact", []):
        img = impact(np.clip(img, 0, 1), f, red=(g == "fire" or kind == "i4"))
    if kind not in ("title", "credits", "black"):
        img = vignette(img, 0.3)
        img = grain(img, f, 0.011)
    img = text_overlay(np.clip(img, 0, 1), f)
    # global fades
    if kind == "black":
        pass
    if 1 <= f <= 96:
        img = img * 0.0
    if 97 <= f <= 120:
        img = img * ((f - 97) / 23.0)
    if 7170 <= f:
        img = img * max(0.0, (7200 - f) / 30.0)
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="f0", type=int, default=1)
    ap.add_argument("--to", dest="f1", type=int, default=TL.TOTAL)
    ap.add_argument("--out", default=os.path.join(ROOT, "final", "AlwaysFalling_preview.mp4"))
    ap.add_argument("--audio", default=None)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--png", default=None, help="write these frames as PNG stills instead (comma list)")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--crf", type=int, default=17)
    a = ap.parse_args()
    if a.png:
        os.makedirs(os.path.join(ROOT, "final", "stills"), exist_ok=True)
        for f in [int(x) for x in a.png.split(",")]:
            fr = make_frame(f)
            cv2.imwrite(os.path.join(ROOT, "final", "stills", f"{f:05d}.png"), cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
            print("still", f)
        return
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    ow, oh = int(W * a.scale) // 2 * 2, int(H * a.scale) // 2 * 2
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ow}x{oh}", "-r", str(TL.FPS), "-i", "-"]
    if a.audio:
        start = (a.f0 - 1) / TL.FPS
        cmd += ["-ss", f"{start:.4f}", "-i", a.audio]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf) if a.scale >= 1 else "22", "-pix_fmt", "yuv420p", "-tune", "animation"]
    if a.audio:
        cmd += ["-c:a", "aac", "-b:a", "256k", "-shortest"]
    cmd += [a.out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frames = list(range(a.f0, a.f1 + 1))
    with Pool(a.workers) as pool:
        for i, fr in enumerate(pool.imap(make_frame, frames, chunksize=4)):
            if a.scale != 1.0:
                fr = cv2.resize(fr, (ow, oh), interpolation=cv2.INTER_AREA)
            p.stdin.write(fr.tobytes())
            if i % 240 == 0:
                print("frame", frames[i], flush=True)
    p.stdin.close()
    p.wait()
    print("wrote", a.out)


if __name__ == "__main__":
    main()
