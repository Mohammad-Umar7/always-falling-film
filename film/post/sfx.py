"""V3 sound effects: real recordings (CC0, Freesound; see assets/dl/sfx/manifest.json) in place of synthesized ones.
Each recording is matched in loudness to the V2 synth cue it replaces, so the mix keeps its designed balance and
only the sound itself becomes real.
"""
import os, json, subprocess, shutil, random
import numpy as np

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "assets", "dl", "sfx")
FFMPEG = shutil.which("ffmpeg") or r"C:\ffmpeg\bin\ffmpeg.exe"
_man = None
_cache = {}


def files(key):
    global _man
    if _man is None:
        p = os.path.join(D, "manifest.json")
        _man = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    return [os.path.join(D, it["file"]) for it in _man.get(key, [])
            if it.get("file") and os.path.exists(os.path.join(D, it["file"]))]


def decode(path):
    if path not in _cache:
        raw = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                             capture_output=True, check=True).stdout
        _cache[path] = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    return _cache[path]


def rms(x):
    x = np.asarray(x, np.float32)
    if x.ndim == 2:
        x = x.mean(1) * np.sqrt(2)
    return float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0


def bed(key, n, seed=0, idx=None, xf=0.6):
    """n stereo samples of the recording from a seeded offset, looped with crossfades if needed (None if missing)"""
    fs = files(key)
    if not fs or n <= 0:
        return None
    rng = random.Random(seed * 7919 + len(key))
    p = fs[idx % len(fs)] if idx is not None else fs[rng.randrange(len(fs))]
    x = decode(p)
    a, b = int(0.3 * SR), len(x) - int(0.3 * SR)              # skip handling noise at the ends
    if b - a < SR:
        a, b = 0, len(x)
    body = x[a:b]
    if len(body) >= n:
        off = rng.randrange(0, len(body) - n + 1)
        return body[off:off + n].copy()
    f = int(min(xf * SR, len(body) / 3))
    fi = np.sqrt(np.linspace(0, 1, f, dtype=np.float32))[:, None]
    fo = fi[::-1]
    out = body.copy()
    while len(out) < n:
        out = np.concatenate([out[:-f], out[-f:] * fo + body[:f] * fi, body[f:]])
    return out[:n]


def hit(key, idx=0, pre=0.03, length=0.6):
    """one transient (a click, a knock) cut around the loudest moment of the recording"""
    fs = files(key)
    if not fs:
        return None
    x = decode(fs[idx % len(fs)])
    e = np.abs(x).max(1)
    k = int(np.argmax(e))
    a = max(0, k - int(pre * SR))
    y = x[a:a + int(length * SR)].copy()
    m = max(1, int(len(y) * 0.3))
    y[-m:] *= np.linspace(1, 0, m, dtype=np.float32)[:, None]
    return y


def match(y, ref, db=0.0):
    """scale y to the loudness of the synth reference"""
    rr, ry = rms(ref), rms(y)
    if ry < 1e-7 or rr < 1e-9:
        return y
    y = y * (rr / ry * 10 ** (db / 20))
    thr = 4.0 * rr * 10 ** (db / 20)                 # tame crackle spikes: soft knee at 4x the average level
    return (thr * np.tanh(y / thr)).astype(np.float32)


def match_peak(y, ref, db=0.0):
    """one-shots (clicks, knocks): scale by peak, not average - a short synth tick and a recorded click with a
    tail have very different averages, and average-matching blew the recorded transient up into the limiter"""
    pr = float(np.abs(np.asarray(ref)).max()) if len(ref) else 0.0
    py = float(np.abs(y).max()) if len(y) else 0.0
    if py < 1e-7 or pr < 1e-9:
        return y
    return (y * (pr / py * 10 ** (db / 20))).astype(np.float32)
