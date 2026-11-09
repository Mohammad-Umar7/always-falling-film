ROOT = __file__.rsplit("tests", 1)[0]
p = ROOT + "post/audio.py"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert a in s, "MISSING: " + a[:90]
    s = s.replace(a, b, 1)


# --- spike trains -> short natural bursts (no single-sample spikes into the limiter)
rep('''def rumble(sec, vol=0.6, seed=6):''', '''def ticks(mask, r, ms=4.0, lo=1500):
    """turn a sparse impulse mask into short decaying noise bursts"""
    m = int(ms / 1000 * SR)
    burst = highpass(ns(m, "white", r), lo) * np.exp(-np.arange(m) / (m / 4)).astype(np.float32)
    burst /= np.abs(burst).max() + 1e-9
    imp = mask.astype(np.float32) * r.uniform(0.2, 1.0, len(mask)).astype(np.float32)
    return signal.fftconvolve(imp, burst)[: len(mask)].astype(np.float32)


def rumble(sec, vol=0.6, seed=6):''')
rep('''    cr = highpass(ns(n, "white", r), 2000) * (r.random(n) > 0.995).astype(np.float32) * 3
    return (low + lowpass(cr, 6000) * 0.3) * vol''', '''    cr = ticks(r.random(n) > 0.9995, r, 6.0, 2000)
    return (low + lowpass(cr, 6000) * 0.25) * vol''')
rep('''    crack = highpass(ns(len(n), "white", r), 1500) * (r.random(len(n)) > 0.992).astype(np.float32) * 2
    return ((out * (0.3 + 0.7 * t / sec) + crack * 0.3) * vol).astype(np.float32)''', '''    crack = ticks(r.random(len(n)) > 0.9992, r, 5.0, 1500)
    return ((out * (0.3 + 0.7 * t / sec) + crack * 0.25) * vol).astype(np.float32)''')
rep('''    pops = (r.random(n) > 0.9985).astype(np.float32) * r.uniform(0.2, 1, n).astype(np.float32)
    return (bandpass(pops, 800, 7000) * 6 + lowpass(ns(n, "brown", r), 400) * 0.4) * vol''', '''    pops = ticks(r.random(n) > 0.9993, r, 3.0, 800)
    return (pops * 0.5 + lowpass(ns(n, "brown", r), 400) * 0.4) * vol''')
rep('''    drops = highpass(ns(n, "white", r), 3000) * (r.random(n) > 0.997).astype(np.float32) * 2
    return (hiss + drops) * vol''', '''    drops = ticks(r.random(n) > 0.999, r, 2.5, 3000)
    return (hiss + drops * 0.12) * vol''')
rep('''    crackle = highpass(ns(n, "white", r), 2500) * (r.random(n) > 0.6).astype(np.float32)
    return crackle * env(n, 0.03, 0.12) * vol''', '''    crackle = ticks(r.random(n) > 0.995, r, 3.0, 2500) * 0.6 + highpass(ns(n, "white", r), 3000) * 0.15
    return crackle * env(n, 0.03, 0.12) * vol''')
rep('''    e = uniform_filter1d(x ** 2, int(0.05 * SR)) ** 0.5''', '''    e = np.maximum(uniform_filter1d(x ** 2, int(0.05 * SR)), 0) ** 0.5''')

# --- gain staging by section
rep('''    A(birds(6.0, 14, 0.06), S(361))
    A(pigeon_flaps(6.0, 0.22), S(361), pan=0.2)
    A(city_hum(6.5, 0.03), S(361))''', '''    A(birds(6.0, 16, 0.09), S(361))
    A(pigeon_flaps(6.0, 0.32), S(361), pan=0.2)
    A(city_hum(6.5, 0.045), S(361))''')
rep('''    put(boom(3.0, 1.0, 40), S(1452))
    put(whoosh(0.5, True, 0.55), S(1450))
    A(rumble(10.5, 0.55), S(1452), fade=0.05)
    for k in range(12):
        put(taiko(1.2, 0.45 + 0.04 * k, 80), S(1489) + k * 0.6)
    put(pad(["D2", "A2", "D3", "F#3"], 10.0, 0.16, 2400, 2.0, 1.0), S(1452))''', '''    put(boom(3.0, 0.7, 40), S(1452))
    put(whoosh(0.5, True, 0.45), S(1450))
    A(rumble(10.5, 0.33), S(1452), fade=0.05)
    for k in range(12):
        put(taiko(1.2, 0.30 + 0.03 * k, 80), S(1489) + k * 0.6)
    put(pad(["D2", "A2", "D3", "F#3"], 10.0, 0.11, 2400, 2.0, 1.0), S(1452))''')
rep('''    A(roar(15.0, 0.5), S(5353), fade=1.0)''', '''    A(roar(15.0, 0.36), S(5353), fade=1.0)''')
rep('''    for k in range(16):
        put(taiko(1.0, 0.42 + 0.03 * k, 75), S(5400) + k * 0.55)
    for f in [5480, 5503, 5530, 5560, 5585]:
        put(boom(2.0, 0.8, 50), S(f))''', '''    for k in range(16):
        put(taiko(1.0, 0.30 + 0.025 * k, 75), S(5400) + k * 0.55)
    for f in [5480, 5503, 5530, 5560, 5585]:
        put(boom(2.0, 0.55, 50), S(f))''')
# montage music a little more present
rep('''["D", "Bm", "G", "A", "D", "Bm", "Em", "A", "D", "Bm", "G", "A", "D", "F#m", "G", "A"], 4.0, 0.06)
    motif(S(2700), PROMISE, 0.82, 0.20, pan=-0.3)
    motif(S(2950), ANSWER, 0.86, 0.18, pan=0.3)''', '''["D", "Bm", "G", "A", "D", "Bm", "Em", "A", "D", "Bm", "G", "A", "D", "F#m", "G", "A"], 4.0, 0.08)
    motif(S(2700), PROMISE, 0.82, 0.27, pan=-0.3)
    motif(S(2950), ANSWER, 0.86, 0.25, pan=0.3)''')
rep('''    motif(S(3612), PROMISE[:5], 0.92, 0.16, pan=-0.2, octave=-1)''', '''    motif(S(3612), PROMISE[:5], 0.92, 0.22, pan=-0.2, octave=-1)''')
# H1: the emotional peak
rep('''    progression(S(4561), ["D", "Bm", "G", "A", "D", "Bm", "G", "A"], 3.1, 0.11, cutoff=2000, strings_too=True)
    motif(S(4575), PROMISE, 0.62, 0.40)
    motif(S(4575) + 5.0, ANSWER, 0.62, 0.38)
    motif(S(4575) + 9.4, PROMISE, 0.56, 0.42)
    motif(S(4575) + 9.4, PROMISE, 0.56, 0.05, inst="strings", octave=-1)
    motif(S(4575) + 14.0, ANSWER + ["D5"], 0.6, 0.44)
    motif(S(4575) + 14.0, ANSWER + ["D5"], 0.6, 0.05, inst="strings", octave=-1)''', '''    progression(S(4561), ["D", "Bm", "G", "A", "D", "Bm", "G", "A"], 3.1, 0.17, cutoff=2200, strings_too=True)
    motif(S(4575), PROMISE, 0.62, 0.55)
    motif(S(4575) + 5.0, ANSWER, 0.62, 0.52)
    motif(S(4575) + 9.4, PROMISE, 0.56, 0.58)
    motif(S(4575) + 9.4, PROMISE, 0.56, 0.09, inst="strings", octave=-1)
    motif(S(4575) + 14.0, ANSWER + ["D5"], 0.6, 0.6)
    motif(S(4575) + 14.0, ANSWER + ["D5"], 0.6, 0.09, inst="strings", octave=-1)''')
rep('''    put(pad(["D2", "A2"], 25.0, 0.08, 600, 6.0, 4.0), S(4561))
    put(strings("D3", 8.0, 0.08, 2.0, 4.0), S(5000))''', '''    put(pad(["D2", "A2"], 25.0, 0.11, 600, 6.0, 4.0), S(4561))
    put(strings("D3", 8.0, 0.12, 2.0, 4.0), S(5000))''')
# K1 / L1
rep('''    motif(S(6606), PROMISE, 0.82, 0.32)
    progression(S(6630), ["D", "G", "D"], 3.2, 0.07, strings_too=True)''', '''    motif(S(6606), PROMISE, 0.82, 0.42)
    progression(S(6630), ["D", "G", "D"], 3.2, 0.10, strings_too=True)''')
rep('''    progression(S(6841), ["D", "Bm", "G", "A", "D"], 3.1, 0.08)
    motif(S(6846), PROMISE, 0.72, 0.34)
    motif(S(6846) + 5.8, ANSWER + ["D5"], 0.72, 0.32)''', '''    progression(S(6841), ["D", "Bm", "G", "A", "D"], 3.1, 0.11)
    motif(S(6846), PROMISE, 0.72, 0.44)
    motif(S(6846) + 5.8, ANSWER + ["D5"], 0.72, 0.42)''')
# quieter mechanical clicks
for a, b in [("click(0.35, True), S(3158)", "click(0.2, True), S(3158)"), ("click(0.3, True), S(3888)", "click(0.17, True), S(3888)"),
             ("click(0.3, True), S(4062)", "click(0.17, True), S(4062)"), ("click(0.55, True), S(4191)", "click(0.26, True), S(4191)")]:
    rep(a, b)
# dialogue lands near -18 dBFS
rep('''    gain = 10 ** ((-21.0 - loud) / 20)''', '''    gain = 10 ** ((-19.5 - loud) / 20)''')
open(p, "w", encoding="utf-8").write(s)
import ast
ast.parse(s)
print("audio patch ok")
