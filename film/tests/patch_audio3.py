ROOT = __file__.rsplit("tests", 1)[0]
p = ROOT + "post/audio.py"
s = open(p, encoding="utf-8").read()
a = s.index("def crickets(")
b = s.index("def city_hum(")
s = s[:a] + '''def crickets(sec, vol=0.08, seed=0):
    """a field of individual crickets: short pulsed chirps at their own rhythms and distances, plus night air"""
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    out = np.zeros(n, np.float32)
    plen = int(0.018 * SR)
    tp = np.arange(plen) / SR
    win = np.hanning(plen).astype(np.float32)
    for _ in range(7):
        f = r.uniform(3900, 5400)
        dist = r.uniform(0.2, 1.0)
        period = r.uniform(0.38, 0.95)
        pulses = int(r.integers(2, 5))
        prate = r.uniform(24, 38)
        pulse = (np.sin(2 * np.pi * f * tp) * win).astype(np.float32) * dist
        t = r.uniform(0, period)
        while t < sec - 0.3:
            for k in range(pulses):
                i = int((t + k / prate) * SR)
                if i + plen < n:
                    out[i:i + plen] += pulse
            t += period * r.uniform(0.92, 1.08)
            if r.random() < 0.07:
                t += r.uniform(0.6, 2.5)
    out = lowpass(out, 7500) * 0.10
    air = lowpass(ns(n, "pink", r), 900) * 0.08
    return (out + air) * vol * 8


''' + s[b:]
open(p, "w", encoding="utf-8").write(s)
import ast
ast.parse(s)
print("crickets patched")
