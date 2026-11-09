"""ALWAYS FALLING - score, sound design and voice mix, synthesised from scratch (48 kHz stereo).

Hyderabad lives in the LEFT speaker and Abu Dhabi in the RIGHT while the screen is split; the satellite's
sound crosses the stereo field exactly when its dot crosses the divider. Three buses (music, ambience/SFX,
voice) are ducked, reverberated, loudness-normalised and peak-limited into audio/mix.wav (exactly 300 s).

    python post/audio.py            -> audio/mix.wav + audio/mix_report.txt
"""
import os, sys, math, wave
import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, maximum_filter1d, uniform_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import timeline as TL

SR = 48000
DUR = TL.TOTAL / TL.FPS
N = int(round(DUR * SR))
rng = np.random.default_rng(1975)

BUS = {k: np.zeros((N + SR * 8, 2), np.float32) for k in ("music", "amb", "vo")}


def fr(f):
    """timeline frame -> seconds"""
    return (f - 1) / TL.FPS


# ------------------------------------------------------------------ dsp helpers
def _sos(kind, fc, order):
    if kind == "band":
        lo, hi = fc
        return signal.butter(order, [lo / (SR / 2), min(hi, SR * 0.45) / (SR / 2)], "band", output="sos")
    return signal.butter(order, min(fc, SR * 0.45) / (SR / 2), kind, output="sos")


def lowpass(x, fc, order=2):
    return signal.sosfilt(_sos("low", fc, order), x, axis=0).astype(np.float32)


def highpass(x, fc, order=2):
    return signal.sosfilt(_sos("high", fc, order), x, axis=0).astype(np.float32)


def bandpass(x, f1, f2, order=2):
    return signal.sosfilt(_sos("band", (f1, f2), order), x, axis=0).astype(np.float32)


def ns(n, color="white", r=None):
    """noise with exactly n samples"""
    r = r or rng
    w = r.standard_normal(int(n)).astype(np.float32)
    if color == "pink":
        b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
        a = [1, -2.494956002, 2.017265875, -0.522189400]
        w = (signal.lfilter(b, a, w) * 3).astype(np.float32)
    elif color == "brown":
        w = highpass((np.cumsum(w) / 60).astype(np.float32), 15)
    return w


def env(n, a=0.01, r=0.3, sus=1.0):
    n = int(n)
    e = np.full(n, sus, np.float32)
    na, nr = min(int(a * SR), n), min(int(r * SR), n)
    if na:
        e[:na] = np.linspace(0, sus, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def tvec(sec):
    return np.arange(int(sec * SR)) / SR


def hz(note):
    names = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    n, o = note[:-1], int(note[-1])
    return 440.0 * 2 ** ((names[n] + (o - 4) * 12) / 12)


def shift(note, octaves):
    return note[:-1] + str(int(note[-1]) + octaves)


def stereo(sig, pan):
    """equal-power pan; pan may be a scalar or a per-sample array in -1..1"""
    a = (np.asarray(pan) + 1) * math.pi / 4
    return np.stack([sig * np.cos(a), sig * np.sin(a)], -1).astype(np.float32)


def put(sig, t, gain=1.0, pan=0.0, bus="music", fade=0.006):
    """mix a mono (n,) or stereo (n,2) signal into a bus at t seconds; short fades kill clicks."""
    if sig is None or len(sig) == 0:
        return
    sig = np.array(sig, np.float32)
    nf = min(int(fade * SR), len(sig) // 2)
    if nf > 1:
        ramp = np.linspace(0, 1, nf, dtype=np.float32)
        if sig.ndim == 1:
            sig[:nf] *= ramp
            sig[-nf:] *= ramp[::-1]
        else:
            sig[:nf] *= ramp[:, None]
            sig[-nf:] *= ramp[::-1, None]
    if sig.ndim == 1:
        sig = stereo(sig, pan)
    elif np.ndim(pan) == 0 and pan != 0:
        a = (pan + 1) * math.pi / 4
        sig = sig * (np.array([math.cos(a), math.sin(a)], np.float32) * math.sqrt(2))
    i = int(round(t * SR))
    B = BUS[bus]
    if i < 0:
        sig, i = sig[-i:], 0
    n = min(len(sig), len(B) - i)
    if n > 0:
        B[i:i + n] += sig[:n] * gain


def sweep(sig, t, p0, p1, gain=1.0, bus="music", fade=0.05):
    """mono signal panned from p0 to p1 over its length"""
    put(stereo(sig, np.linspace(p0, p1, len(sig))), t, gain, bus=bus, fade=fade)


def reverb_ir(sec, seed, damp=6000, pre=0.012):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    t = np.arange(n) / SR
    irs = []
    for _ in range(2):
        ir = r.standard_normal(n).astype(np.float32) * np.exp(-t * 6.9 / sec).astype(np.float32)
        ir = lowpass(ir, damp)
        ir[: int(pre * SR)] = 0
        ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
        irs.append(ir)
    return irs


def reverb(x, sec=2.2, wet=0.3, seed=0, damp=6000):
    """mono or stereo in, stereo out (length + tail)"""
    irL, irR = reverb_ir(sec, seed, damp)
    if x.ndim == 1:
        L, R = signal.fftconvolve(x, irL), signal.fftconvolve(x, irR)
        dry = np.zeros((len(L), 2), np.float32)
        dry[:len(x), 0] = x
        dry[:len(x), 1] = x
    else:
        L, R = signal.fftconvolve(x[:, 0], irL), signal.fftconvolve(x[:, 1], irR)
        dry = np.zeros((len(L), 2), np.float32)
        dry[:len(x)] = x
    return (dry * (1 - wet) + np.stack([L, R], -1) * wet).astype(np.float32)


# ------------------------------------------------------------------ instruments
def ks(freq, sec, bright=0.6, decay=0.996):
    """Karplus-Strong string"""
    n = int(sec * SR)
    P = max(2, int(round(SR / freq)))
    exc = np.zeros(n, np.float32)
    exc[:P] = lowpass(rng.standard_normal(P).astype(np.float32), 1500 + 9000 * bright)
    a = np.zeros(P + 2)
    a[0] = 1.0
    a[P] = -decay * 0.5
    a[P + 1] = -decay * 0.5
    y = signal.lfilter([1.0], a, exc).astype(np.float32)
    return y / (np.max(np.abs(y)) + 1e-6)


def pluck(note, sec=3.5, vel=0.6):
    """santoor-like struck string: two slightly detuned KS strings + a sine body"""
    f = hz(note)
    s = ks(f, sec, 0.35 + 0.45 * vel, 0.9986) * 0.55 + ks(f * 1.002, sec, 0.3, 0.998) * 0.35
    t = np.arange(len(s)) / SR
    s += (np.sin(2 * np.pi * f * t) * np.exp(-t * 1.6) * 0.35).astype(np.float32)
    s = lowpass(s, 2600 + 3200 * vel)
    return s * env(len(s), 0.003, 0.8) * vel


def strings(note, sec, vol=0.2, attack=0.7, release=1.4, bright=1.0):
    """bowed-string section: two detuned additive voices with delayed vibrato"""
    f = hz(note)
    t = tvec(sec)
    out = np.zeros(len(t), np.float32)
    for det, ph in ((-0.07, 0.3), (0.08, 1.9)):
        vib = 1 + (0.0045 * np.sin(2 * np.pi * 5.3 * t + ph)) * np.clip(t / 0.9, 0, 1)
        phase = 2 * np.pi * f * 2 ** (det / 12) * np.cumsum(vib) / SR
        for k in range(1, 11):
            out += (np.sin(k * phase + ph * k) / k ** (1.35 - 0.25 * bright)).astype(np.float32)
    out = lowpass(out, 2400 + 2000 * bright) / 6
    return out * env(len(out), attack, release) * vol


def tanpura_cycle(sec=6.4):
    """Pa - Sa - Sa - Sa(low) with jawari buzz"""
    out = np.zeros(int(sec * SR), np.float32)
    for k, f in enumerate([hz("A2"), hz("D3"), hz("D3"), hz("D2")]):
        s = ks(f, sec - k * sec / 4 + 2.0, 0.9, 0.9995)
        s = np.tanh(s * 2.2) * 0.6 + s * 0.4
        s = s * env(len(s), 0.01, 1.2)
        i = int(k * sec / 4 * SR)
        n = min(len(s), len(out) - i)
        out[i:i + n] += s[:n] * 0.5
    return lowpass(out, 5000)


def pad(chord, sec, vol=0.2, cutoff=1400, attack=1.5, release=2.0, sub=True):
    t = tvec(sec)
    sig = np.zeros(len(t), np.float32)
    for note in chord:
        f = hz(note)
        for det in (-0.11, 0.0, 0.12):
            ff = f * 2 ** (det / 12)
            sig += (2 * ((t * ff + rng.uniform()) % 1.0) - 1).astype(np.float32)
    sig = lowpass(sig, cutoff, 2) / (len(chord) * 3)
    if sub:
        sig += (np.sin(2 * np.pi * hz(chord[0]) / 2 * t) * 0.35).astype(np.float32)
    lfo = (1 + 0.07 * np.sin(2 * np.pi * 0.17 * t)).astype(np.float32)
    return sig * lfo * env(len(sig), attack, release) * vol


def bell(note, sec=4.0, vol=0.25):
    f = hz(note)
    t = tvec(sec)
    mod = np.sin(2 * np.pi * f * 3.5 * t) * 2.2 * np.exp(-t * 2)
    return (np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 1.2) * vol).astype(np.float32)


def taiko(sec=1.4, vol=0.9, f0=85):
    t = tvec(sec)
    f = f0 * (1 + 1.6 * np.exp(-t * 18))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
    hit = lowpass(ns(len(t)), 900) * np.exp(-t * 30)
    return ((body * 0.9 + hit * 0.6) * vol).astype(np.float32)


def boom(sec=3.0, vol=0.9, f0=48):
    """cinematic sub boom for impact frames"""
    t = tvec(sec)
    f = f0 * (1 + 2.5 * np.exp(-t * 9))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    crack = highpass(ns(len(t)), 1200) * np.exp(-t * 22) * 0.5
    air = lowpass(ns(len(t), "pink"), 2500) * np.exp(-t * 2.5) * 0.25
    return ((body + crack + air) * vol).astype(np.float32)


def whoosh(sec=1.2, up=True, vol=0.5, lo=300, hi=5300):
    n = ns(int(sec * SR))
    out = np.zeros_like(n)
    steps = 32
    for k in range(steps):
        a, b = int(k * len(n) / steps), int((k + 1) * len(n) / steps)
        u = k / steps if up else 1 - k / steps
        fc = lo + (hi - lo) * u
        seg = bandpass(n[max(0, a - 2400):b], fc * 0.6, min(fc * 1.4, 20000))
        out[a:b] = seg[-(b - a):]
    t = np.arange(len(n)) / SR
    e = np.sin(np.pi * np.clip(t / sec, 0, 1)) ** 2
    return (out * e * vol).astype(np.float32)


def reverse_swell(sec=1.5, vol=0.4, note="D5"):
    """reversed bell + air swell that lands on the next downbeat"""
    s = bell(note, sec, 1.0) + lowpass(ns(int(sec * SR), "pink"), 4000) * np.exp(-tvec(sec) * 2.5).astype(np.float32) * 0.3
    return s[::-1].copy() * vol


def beep(f=1400, sec=0.07, vol=0.25):
    t = tvec(sec)
    return (np.sin(2 * np.pi * f * t) * env(len(t), 0.004, 0.035) * vol).astype(np.float32)


def blip(f=1396.9, vol=0.2):
    """Aryabhata's carrier 'heartbeat': a soft sine pip with a faint octave ghost"""
    t = tvec(0.5)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 14) + 0.25 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 22)
    return (s * env(len(t), 0.003, 0.05) * vol).astype(np.float32)


def shimmer(sec, vol=0.12):
    """the satellite passing overhead: a high glassy cluster with tremolo"""
    t = tvec(sec)
    s = np.zeros(len(t), np.float32)
    for k, nt in enumerate(["A6", "D7", "E7", "F#7"]):
        s += (np.sin(2 * np.pi * hz(nt) * t + k) * (0.6 + 0.4 * np.sin(2 * np.pi * (5 + k * 1.3) * t))).astype(np.float32)
    e = np.sin(np.pi * np.clip(t / sec, 0, 1)) ** 1.5
    return s * e.astype(np.float32) * vol / 4


def crickets(sec, vol=0.08, seed=0):
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


def city_hum(sec, vol=0.08, seed=1):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    return (lowpass(ns(n, "brown", r), 300) * 2 + lowpass(ns(n, "pink", r), 1200) * 0.3) * vol


def clangs(sec, vol=0.06, seed=3):
    r = np.random.default_rng(seed)
    out = np.zeros(int(sec * SR), np.float32)
    t = tvec(1.2)
    for _ in range(int(sec / 2.2)):
        f = r.uniform(600, 1500)
        c = ((np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-t * 6)).astype(np.float32)
        i = int(r.uniform(0, max(0.01, sec - 1.3)) * SR)
        m = min(len(c), len(out) - i)
        out[i:i + m] += c[:m] * r.uniform(0.3, 1.0)
    return out * vol


def footsteps(sec, every=0.5, vol=0.2, fade_to=0.25, seed=5):
    r = np.random.default_rng(seed)
    out = np.zeros(int(sec * SR), np.float32)
    t = tvec(0.12)
    k = 0
    while k * every < sec - 0.15:
        g = 1 + (fade_to - 1) * (k * every / sec)
        thud = (np.sin(2 * np.pi * r.uniform(70, 95) * t) * np.exp(-t * 40)
                + lowpass(ns(len(t), "white", r), 1800) * np.exp(-t * 60) * 0.6).astype(np.float32)
        i = max(0, int((k * every + r.uniform(-0.02, 0.02)) * SR))
        m = min(len(thud), len(out) - i)
        out[i:i + m] += thud[:m] * g
        k += 1
    return out * vol


def birds(sec, n=10, vol=0.05, seed=8):
    """evening myna/sparrow chirps: short FM sweeps"""
    r = np.random.default_rng(seed)
    out = np.zeros(int(sec * SR), np.float32)
    for _ in range(n):
        d = r.uniform(0.05, 0.14)
        t = tvec(d)
        f0, f1 = r.uniform(2500, 4200), r.uniform(1800, 5200)
        f = f0 + (f1 - f0) * t / d
        c = (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d)).astype(np.float32)
        base = r.uniform(0, max(0.01, sec - 0.6))
        for rep in range(int(r.integers(1, 4))):
            i = int((base + rep * d * 1.4) * SR)
            if i + len(c) < len(out):
                out[i:i + len(c)] += c * r.uniform(0.3, 1)
    return out * vol


def pigeon_flaps(sec, vol=0.2, seed=4):
    r = np.random.default_rng(seed)
    out = np.zeros(int(sec * SR), np.float32)
    w = np.hanning(int(0.06 * SR)).astype(np.float32)
    for _ in range(int(sec * 12)):
        i = int(r.uniform(0, sec - 0.1) * SR)
        b = bandpass(ns(len(w), "white", r), 400, 2500) * w
        out[i:i + len(b)] += b * r.uniform(0.3, 1)
    return out * vol


def ticks(mask, r, ms=4.0, lo=1500):
    """turn a sparse impulse mask into short decaying noise bursts"""
    m = int(ms / 1000 * SR)
    burst = highpass(ns(m, "white", r), lo) * np.exp(-np.arange(m) / (m / 4)).astype(np.float32)
    burst /= np.abs(burst).max() + 1e-9
    imp = mask.astype(np.float32) * r.uniform(0.2, 1.0, len(mask)).astype(np.float32)
    return signal.fftconvolve(imp, burst)[: len(mask)].astype(np.float32)


def rumble(sec, vol=0.6, seed=6):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    low = lowpass(ns(n, "brown", r), 160) * 3
    cr = ticks(r.random(n) > 0.9995, r, 6.0, 2000)
    return (low + lowpass(cr, 6000) * 0.25) * vol


def roar(sec, vol=0.6, seed=7):
    r = np.random.default_rng(seed)
    n = ns(int(sec * SR), "white", r)
    out = np.zeros_like(n)
    steps = 48
    for k in range(steps):
        a, b = int(k * len(n) / steps), int((k + 1) * len(n) / steps)
        fc = 200 + 2600 * (k / steps) ** 1.5
        out[a:b] = lowpass(n[max(0, a - 4000):b], fc)[-(b - a):]
    t = np.arange(len(n)) / SR
    crack = ticks(r.random(len(n)) > 0.9992, r, 5.0, 1500)
    return ((out * (0.3 + 0.7 * t / sec) + crack * 0.25) * vol).astype(np.float32)


def fire_crackle(sec, vol=0.15, seed=9):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    pops = ticks(r.random(n) > 0.9993, r, 3.0, 800)
    return (pops * 0.5 + lowpass(ns(n, "brown", r), 400) * 0.4) * vol


def rain_sfx(sec, vol=0.2, seed=10):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    hiss = bandpass(ns(n, "pink", r), 800, 9000) * 0.7
    drops = ticks(r.random(n) > 0.999, r, 2.5, 3000)
    return (hiss + drops * 0.12) * vol


def click(vol=0.4, heavy=False):
    t = tvec(0.06)
    s = highpass(ns(len(t)), 600 if heavy else 1500) * np.exp(-t * (70 if heavy else 120)).astype(np.float32)
    if heavy:
        s += (np.sin(2 * np.pi * 180 * t) * np.exp(-t * 60) * 0.6).astype(np.float32)
    return (s * vol).astype(np.float32)


def tape_hiss(sec, vol=0.03):
    n = int(sec * SR)
    h = highpass(ns(n, "pink"), 2500)
    t = np.arange(n) / SR
    return h * (1 + 0.15 * np.sin(2 * np.pi * 0.8 * t)).astype(np.float32) * vol


def creak(sec=1.0, vol=0.25):
    t = tvec(sec)
    f = 190 + 70 * np.sin(2 * np.pi * 1.1 * t) + 40 * t
    s = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR).astype(np.float32) * (np.sin(2 * np.pi * 16 * t) > 0.2).astype(np.float32)
    return (bandpass(s, 300, 2500) * env(len(t), 0.06, 0.3) * vol).astype(np.float32)


def chain_knock(vol=0.3, seed=11):
    """iron ring knocker against a wooden door: thud + jingle"""
    r = np.random.default_rng(seed)
    out = np.zeros(int(0.7 * SR), np.float32)
    t = tvec(0.35)
    for k in range(3):
        f = r.uniform(2200, 3600)
        c = np.sin(2 * np.pi * f * t) * np.exp(-t * 22) + 0.4 * np.sin(2 * np.pi * f * 1.48 * t) * np.exp(-t * 30)
        i = int(k * 0.06 * SR)
        out[i:i + len(c)] += c.astype(np.float32)
    knock = taiko(0.3, 0.9, 140)
    out[: len(knock)] += knock
    return out * vol


def paper(sec=0.4, vol=0.08, seed=12):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    crackle = ticks(r.random(n) > 0.995, r, 3.0, 2500) * 0.6 + highpass(ns(n, "white", r), 3000) * 0.15
    return crackle * env(n, 0.03, 0.12) * vol


def train_horn(sec=3.5, vol=0.1):
    t = tvec(sec)
    s = np.zeros(len(t), np.float32)
    for f in (311.1, 392.0):
        s += signal.sawtooth(2 * np.pi * f * t).astype(np.float32)
    return lowpass(s, 1200) * env(len(t), 0.4, 1.2) * vol


def quindar(f=2525, vol=0.12):
    return beep(f, 0.25, vol)


# ------------------------------------------------------------------ V3: recorded instruments (post/sampler.py)
SAMPLED = os.environ.get("AF_SYNTH_ONLY", "0") != "1"
if SAMPLED:
    import sampler as SM
    _syn_pad, _syn_boom, _syn_taiko = pad, boom, taiko

    def _m(note):
        return SM.note_midi(note)

    def pluck(note, sec=3.5, vel=0.6):
        """the promise motif: an upright piano, soft hammers for quiet phrases"""
        k = "piano_p" if vel < 0.4 else "piano_mf"
        return SM.inst(k).note(_m(note), max(0.3, sec), amp=SM.CAL["piano"] * vel / 0.5, attack=0.002, release=0.6)

    def strings(note, sec, vol=0.2, attack=0.7, release=1.4, bright=1.0):
        m = _m(note)
        y = SM.inst(SM.string_section(m)).note(m, max(0.15, sec - release), amp=SM.CAL["strings"] * vol / 0.2,
                                               attack=max(0.06, attack), release=max(0.25, release))
        if bright < 0.8:
            y = lowpass(y, 2500 + 4000 * bright)
        return y

    def pad(chord, sec, vol=0.2, cutoff=1400, attack=1.5, release=2.0, sub=True):
        """a low string section chord, glued with a little of the old analogue pad"""
        parts = []
        for note in chord:
            m = _m(note)
            parts.append(SM.inst(SM.string_section(m)).note(m, max(0.3, sec - release), amp=SM.CAL["strings"] * vol / 0.2 / math.sqrt(len(chord)),
                                                            attack=max(0.15, attack), release=max(0.4, release)))
        n = max(len(p) for p in parts)
        out = np.zeros((n, 2), np.float32)
        for p in parts:
            out[:len(p)] += p
        if cutoff < 1200:
            out = lowpass(out, cutoff * 2.2)
        syn = stereo(_syn_pad(chord, sec, vol * 0.35, cutoff, attack, release, sub), 0.0)
        m2 = max(n, len(syn))
        res = np.zeros((m2, 2), np.float32)
        res[:n] += out
        res[:len(syn)] += syn
        return res

    def bell(note, sec=4.0, vol=0.25):
        """glockenspiel"""
        return SM.inst("glock").note(_m(note), max(0.2, sec * 0.75), amp=SM.CAL["glock"] * vol / 0.1, attack=0.001, release=sec * 0.25)

    def taiko(sec=1.4, vol=0.9, f0=85):
        """low hits are a real orchestral bass drum; high 'slams' stay synthetic"""
        if f0 >= 100:
            return _syn_taiko(sec, vol, f0)
        name = "bdrum_p_1" if vol < 0.2 else "bdrum_f_1" if vol < 0.3 else "bdrum_ff_1" if vol < 0.4 else "bdrum_fff_1"
        x = SM.one_shot(f"VSCO 1 Percussion/drums/bass/{name}.wav")
        r = f0 / 70.0                                           # tune the drum a little with f0
        idx = np.arange(int(min(len(x) - 2, sec * SR * r) / r)) * r
        y = np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in range(2)], -1).astype(np.float32)
        y *= np.linspace(1, 0, len(y))[:, None] ** 0.5
        return y * (SM.CAL["drum"] * vol / 0.3)

    def boom(sec=3.0, vol=0.9, f0=48):
        y = stereo(_syn_boom(sec, vol, f0), 0.0)
        x = SM.one_shot("VSCO 1 Percussion/drums/bass/bdrum_fff_1.wav")[: len(y)]
        y[:len(x)] += x * (SM.CAL["boom_drum"] * vol)
        return y


# ------------------------------------------------------------------ voices
def load_wav(path):
    with wave.open(path) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    if sr != SR:
        data = signal.resample_poly(data, SR, sr).astype(np.float32)
    return data


def speech_rms(x):
    e = np.maximum(uniform_filter1d(x ** 2, int(0.05 * SR)), 0) ** 0.5
    m = e > (e.max() * 0.08)
    return float(np.sqrt(np.mean(x[m] ** 2))) if m.any() else float(np.sqrt(np.mean(x ** 2)))


def vo_fx(x, kind):
    x = highpass(x, 85)
    if kind == "outdoor":          # rooftop at night: a little slap off the walls
        return reverb(x, 0.8, 0.16, 4, damp=5000)
    if kind == "radio":            # ground-station loudspeaker
        x = bandpass(x, 420, 3200, 3)
        x = np.tanh(x * 5) * 0.45
        return (x + bandpass(ns(len(x)), 900, 4500) * 0.035).astype(np.float32)
    if kind in ("tape", "tape_far"):
        t = np.arange(len(x)) / SR
        wob = 1 + 0.004 * np.sin(2 * np.pi * 0.7 * t) + 0.0012 * np.sin(2 * np.pi * 5.3 * t)
        idx = np.clip(np.cumsum(wob) - 1, 0, len(x) - 1)
        x = np.interp(idx, np.arange(len(x)), x).astype(np.float32)
        far = kind == "tape_far"
        x = bandpass(x, 300 if far else 200, 2800 if far else 4500, 2)
        x = (np.tanh(x * 2.5) / 2.5).astype(np.float32)
        x = x + highpass(ns(len(x), "pink"), 3000) * (0.012 if far else 0.007)
        return reverb(x, 0.35, 0.12, 5, damp=4000)
    return reverb(x, 0.6, 0.10, 2, damp=6000)     # dry: close, intimate


VO_GAIN = {"outdoor": 1.0, "radio": 0.8, "tape": 0.9, "tape_far": 0.72, "dry": 0.85}
VO_PAN = {"tape": -0.15, "tape_far": -0.25}


def voices():
    target = 0.11
    for clip, f, kind in TL.AUDIO_VO:
        p = os.path.join(ROOT, "audio", "vo", clip + ".wav")
        if not os.path.exists(p):
            print("missing vo", clip)
            continue
        x = load_wav(p)
        x = x * (target / (speech_rms(x) + 1e-6))
        if clip == "D1":                     # cut dead on the impact frame: "power bus vol-"
            x = x[: int((fr(2101) - fr(f)) * SR)]
        y = vo_fx(x, kind)
        put(y, fr(f), VO_GAIN[kind], VO_PAN.get(kind, 0.0), bus="vo", fade=0.01)
        if kind == "radio":
            put(quindar(2525, 0.05), fr(f) - 0.3, bus="vo")
            if clip != "D1":
                put(quindar(2475, 0.05), fr(f) + len(x) / SR + 0.05, bus="vo")


# ------------------------------------------------------------------ score
PROMISE = ["A4", "D5", "E5", "F#5", "A5", "F#5", "E5", "D5"]     # the promise (lullaby) motif
ANSWER = ["B4", "D5", "F#5", "E5", "D5", "A4"]
CH = {"D": ["D3", "F#3", "A3", "D4"], "Bm": ["B2", "D3", "F#3", "B3"], "G": ["G2", "B2", "D3", "G3"],
      "A": ["A2", "C#3", "E3", "A3"], "Em": ["E3", "G3", "B3", "E4"], "F#m": ["F#2", "A2", "C#3", "F#3"],
      "Gmaj7": ["G2", "B2", "D3", "F#3"]}


def motif(t0, notes, beat=0.62, vol=0.5, pan=0.0, octave=0, inst="pluck", hold=3.2):
    for k, n in enumerate(notes):
        n = shift(n, octave) if octave else n
        if inst == "pluck":
            put(pluck(n, hold, vol), t0 + k * beat, 1.0, pan)
        else:
            put(strings(n, beat * 1.6, vol, 0.12, 0.5), t0 + k * beat, 1.0, pan)


def progression(t0, chords, bar=3.2, vol=0.12, pan=0.0, cutoff=1300, strings_too=False):
    for k, c in enumerate(chords):
        put(pad(CH[c], bar + 1.6, vol, cutoff, 1.2, 1.6), t0 + k * bar, 1.0, pan)
        if strings_too:
            for nt in CH[c][1:]:
                put(strings(shift(nt, 1), bar + 1.0, vol * 0.5, 0.9, 1.0), t0 + k * bar, 1.0, pan)


def tanpura(t0, t1, vol=0.12, pan=0.0):
    t = t0
    while t < t1:
        put(tanpura_cycle(), t, vol, pan, fade=0.02)
        t += 6.4


def build():
    S = fr

    def A(sig, t, g=1.0, pan=0.0, fade=0.5):
        put(sig, t, g, pan, bus="amb", fade=fade)

    # ---- A: black -> two skies -> title
    tanpura(0.8, 15.0, 0.07)
    put(blip(vol=0.16), 1.6)                                   # Aryabhata's voice, first heard alone
    progression(S(97), ["D", "Bm"], 3.6, 0.06)
    motif(S(118), PROMISE[:4], 0.72, 0.30)
    sweep(shimmer(S(250) - S(150), 0.10), S(150), -0.8, 0.8)    # the dot crosses the divider
    put(blip(vol=0.10), S(200))
    put(reverse_swell(1.2, 0.25, "D5"), S(289) - 1.2)
    put(boom(3.5, 0.35, 44), S(289))
    put(bell("D6", 5, 0.10), S(296))
    put(strings("A4", 3.0, 0.06, 0.4, 1.5), S(289))

    # ---- B: Hyderabad, April 1975
    A(birds(6.0, 16, 0.09), S(361))
    A(pigeon_flaps(6.0, 0.32), S(361), pan=0.2)
    A(city_hum(6.5, 0.045), S(361))
    tanpura(S(361), S(1200), 0.06)
    A(crickets(S(1215) - S(505), 0.05, 1), S(505), fade=1.5)
    progression(S(505), ["D", "Bm", "G", "A", "D", "Bm", "G", "A", "D", "Gmaj7"], 3.4, 0.065)
    motif(S(505) + 0.6, PROMISE, 0.78, 0.26)
    motif(S(697) + 7.0, ANSWER, 0.82, 0.22)
    for k, f in enumerate([706, 728, 750, 772, 800]):          # Newton's cannon: each orbit line rings
        put(bell(["D6", "F#6", "A6", "D7", "A6"][k], 3.0, 0.06), S(f), pan=-0.4 + 0.2 * k)
    motif(S(985) + 0.3, PROMISE[:6], 0.74, 0.24)
    put(strings("F#4", 6.0, 0.05, 1.5, 2.5), S(1045))
    put(strings("D4", 6.0, 0.05, 1.5, 2.5), S(1045))
    A(train_horn(4.0, 0.035), S(1100), pan=0.5)
    put(bell("F#6", 4, 0.07), S(1150))

    # ---- C1: morning, the father walks away; the slash
    A(birds(3.0, 6, 0.05, 9), S(1201))
    A(city_hum(2.6, 0.03), S(1201), pan=-0.2)
    A(footsteps(2.5, 0.5, 0.22, 0.3), S(1201) + 0.15, pan=0.3, fade=0.05)
    put(whoosh(0.45, True, 0.55, 600, 8000), S(1262) - 0.4)
    put(boom(2.0, 0.45, 70), S(1262))
    put(bell("A6", 2.5, 0.14), S(1262))
    A(city_hum(3.4, 0.05, 3) + clangs(3.4, 0.05), S(1263), pan=0.85, fade=0.05)
    A(birds(3.4, 5, 0.04, 10), S(1263), pan=-0.85, fade=0.05)

    # ---- C2: both nights, split stereo
    A(crickets(4.4, 0.05, 2), S(1345), pan=-0.85)
    A(city_hum(4.4, 0.05, 4), S(1345), pan=0.85)
    put(pad(CH["Bm"], 4.5, 0.07, 900), S(1345))

    # ---- C3: LAUNCH
    put(reverse_swell(1.8, 0.35, "A5"), S(1452) - 1.8)
    A(rumble(1.0, 0.12), S(1441), fade=0.3)
    put(boom(3.0, 0.5, 40), S(1452))
    put(whoosh(0.5, True, 0.45), S(1450))
    A(rumble(10.5, 0.22), S(1452), fade=0.05)
    for k in range(12):
        put(taiko(1.2, 0.22 + 0.025 * k, 80), S(1489) + k * 0.6)
    put(pad(["D2", "A2", "D3", "F#3"], 10.0, 0.08, 2400, 2.0, 1.0), S(1452))
    for nt in ["D4", "A4", "D5", "F#5"]:
        put(strings(nt, 9.0, 0.05, 3.0, 0.8, 1.4), S(1452) + 1.0)
    put(whoosh(2.5, True, 0.45), S(1636))

    # anime FX sound: the manga panel slam during the climb
    put(whoosh(0.32, True, 0.4, 900, 9500), S(1546) - 0.28)
    put(taiko(0.5, 0.45, 150), S(1546))
    put(bell("A6", 1.5, 0.06), S(1546))
    # ---- C3d / C4: orbit - sudden quiet
    put(pad(["D3", "A3", "E4", "F#4"], 11.0, 0.08, 1800, 0.3, 3.0), S(1657))
    for k, nt in enumerate(["A5", "D6", "E6", "F#6"]):
        put(bell(nt, 4.0, 0.08), S(1660) + k * 0.9, pan=-0.3 + 0.2 * k)
    for k in range(int((S(1921) - S(1729)) / 0.5)):
        put(beep(1700, 0.04, 0.04), S(1729) + k * 0.5, pan=0.1)
    put(blip(vol=0.08), S(1700))

    # ---- D1: telemetry; the LEDs die on 2101 - hard cut to silence
    for k in range(int((S(2101) - S(1921)) / 0.5)):
        put(beep(1900 if k % 2 else 1500, 0.035, 0.035), S(1921) + k * 0.5)
    put(pad(["D3", "A3", "E4"], S(2101) - S(1921), 0.05, 1500, 1.0, 0.01), S(1921))
    put(boom(4.0, 0.7, 36), S(2101))

    # ---- D2: silent tumbling; the faint carrier heartbeat starts with "STILL IN ORBIT."
    put(strings("E5", 7.0, 0.025, 3.0, 3.0), S(2200))
    put(strings("B4", 7.0, 0.025, 3.0, 3.0), S(2200))
    hb_t, hb_end = S(2310), S(4191)
    while hb_t < hb_end - 0.2:
        put(blip(vol=0.09), hb_t)
        hb_t += 2.0

    # time-jump light sweeps: an airy whoosh + a faint high chime
    for f_ in TL.SWEEPS:
        put(whoosh(0.45, True, 0.13, 2500, 9500), S(f_) - 0.05)
        put(bell("E7", 1.6, 0.025), S(f_) + 0.12)
    # kirakira: the boy's eyes light up (rooftop wonder; looking up from his homework)
    for f_, nt in ((889, "B6"), (2980, "A6")):
        put(bell(nt, 2.2, 0.05), S(f_), pan=-0.2)
        put(bell(shift(nt, 1), 1.6, 0.03), S(f_) + 0.09, pan=0.2)
    # ---- E/F/G: two lives (L = Hyderabad, R = Abu Dhabi)
    A(crickets(S(4570) - S(2401), 0.04, 5), S(2401), pan=-0.85, fade=1.0)
    A(city_hum(S(4570) - S(2401), 0.035, 6), S(2401), pan=0.85, fade=1.0)
    for f in (2440, 2470, 2500):
        A(paper(0.35, 0.10, f), S(f), pan=0.8, fade=0.02)
    sweep(shimmer(S(2520) - S(2440), 0.08), S(2440), -0.8, 0.8)
    A(paper(0.5, 0.08, 1), S(2585), pan=-0.8, fade=0.02)          # through the door slot
    A(taiko(0.5, 0.18, 170), S(2604), pan=0.8, fade=0.01)         # post box swallow
    A(paper(0.25, 0.14, 2), S(2618), pan=-0.8, fade=0.01)         # it lands on the floor
    sweep(shimmer(S(2840) - S(2740), 0.09), S(2740), -0.8, 0.8)
    progression(S(2401), ["D", "Bm", "G", "A", "D", "Bm", "Em", "A", "D", "Bm", "G", "A", "D", "F#m", "G", "A"], 4.0, 0.08)
    motif(S(2700), PROMISE, 0.82, 0.27, pan=-0.3)
    motif(S(2950), ANSWER, 0.86, 0.25, pan=0.3)
    A(clangs(S(3120) - S(2881), 0.05, 13), S(2881), pan=0.85)
    A(click(0.2, True), S(3158), pan=0.7, fade=0.002)            # record key
    A(tape_hiss(S(3360) - S(3121), 0.02), S(3121), pan=-0.6)
    A(rain_sfx(S(3845) - S(3601), 0.16), S(3601), pan=-0.85, fade=1.0)
    motif(S(3612), PROMISE[:5], 0.92, 0.22, pan=-0.2, octave=-1)
    sweep(shimmer(S(3760) - S(3650), 0.08), S(3650), -0.8, 0.8)
    A(click(0.17, True), S(3888), pan=-0.6, fade=0.002)            # play
    A(tape_hiss(S(4080) - S(3888), 0.022), S(3888), pan=-0.6)
    put(pad(["B2", "F#3", "D4"], 7.0, 0.04, 900, 2.0, 3.0), S(3841))
    # G1 - the last tape. "next year, maybe-" CLICK. The heartbeat stops with it.
    A(click(0.17, True), S(4062), pan=-0.6, fade=0.002)
    A(tape_hiss(S(4191) - S(4062), 0.03), S(4062), pan=-0.6, fade=0.02)
    A(click(0.26, True), S(4191), pan=-0.6, fade=0.002)
    put(pad(["B2", "F#3", "D4"], 6.0, 0.035, 800, 3.0, 3.0), S(4215))
    A(taiko(0.35, 0.2, 210), S(4358), pan=-0.7, fade=0.002)       # shutters
    A(taiko(0.35, 0.2, 195), S(4366), pan=-0.7, fade=0.002)
    sweep(shimmer(S(4400) - S(4300), 0.06), S(4300), 0.45, 0.95)  # R only: it passes, no beep

    # ---- H1: 92,000 orbits - the full theme
    put(reverse_swell(1.5, 0.3, "D5"), S(4561) - 1.5)
    progression(S(4561), ["D", "Bm", "G", "A", "D", "Bm", "G", "A"], 3.1, 0.17, cutoff=2200, strings_too=True)
    motif(S(4575), PROMISE, 0.62, 0.55)
    motif(S(4575) + 5.0, ANSWER, 0.62, 0.52)
    motif(S(4575) + 9.4, PROMISE, 0.56, 0.58)
    motif(S(4575) + 9.4, PROMISE, 0.56, 0.09, inst="strings", octave=-1)
    motif(S(4575) + 14.0, ANSWER + ["D5"], 0.6, 0.6)
    motif(S(4575) + 14.0, ANSWER + ["D5"], 0.6, 0.09, inst="strings", octave=-1)
    for k in range(17):
        put(bell(["D6", "F#6", "A6", "E6", "B6", "A6"][k % 6], 3.0, 0.05), S(4600) + k * 1.3, pan=math.sin(k * 1.7) * 0.7)
    put(pad(["D2", "A2"], 25.0, 0.11, 600, 6.0, 4.0), S(4561))
    put(strings("D3", 8.0, 0.12, 2.0, 4.0), S(5000))

    # ---- I1: 1992, quiet
    A(crickets(8.2, 0.035, 9), S(5161), pan=-0.6)
    A(city_hum(8.2, 0.03, 12), S(5161), pan=0.7)
    put(pad(["B2", "F#3", "C#4"], 8.0, 0.045, 800), S(5161))

    # ---- I2: RE-ENTRY
    A(roar(15.0, 0.27), S(5353), fade=1.0)
    A(fire_crackle(14.0, 0.12), S(5400), fade=1.0)
    put(pad(["D2", "A2", "D#3", "A3"], 15.0, 0.12, 2600, 3.0, 0.5), S(5353))
    for nt in ["A3", "D#4", "A4"]:
        put(strings(nt, 14.0, 0.04, 4.0, 1.0, 1.5), S(5353))
    for k in range(16):
        put(taiko(1.0, 0.22 + 0.02 * k, 75), S(5400) + k * 0.55)
    for f in [5480, 5503, 5530, 5560, 5585]:
        put(boom(2.0, 0.4, 50), S(f))
        put(whoosh(0.4, False, 0.35), S(f) - 0.3)
    put(whoosh(4.0, False, 0.3), S(5593))

    # ---- I3: the streak crosses the night (left -> right), both look up
    sw = whoosh(5.5, True, 0.5, 200, 3500) + roar(5.5, 0.12, 21)
    sweep(sw, S(5713) + 1.0, -0.9, 0.9, bus="amb")
    put(pad(["D3", "A3", "F#4", "B4"], 7.0, 0.08, 1800, 2.0, 0.5), S(5713))
    put(reverse_swell(2.0, 0.28, "D5"), S(5881) - 2.0)

    # manga focus lines as both look up at the streak
    put(boom(1.6, 0.32, 72), S(5758))
    put(bell("D7", 2.0, 0.05), S(5758) + 0.05)
    # ---- I4: the fireball burns through the divider - the two halves become one place
    put(boom(5.0, 0.6, 34), S(5881))
    A(roar(2.5, 0.3, 22), S(5876), fade=0.3)
    put(pad(["D2", "A2", "D3", "F#3", "A3"], 9.0, 0.13, 2500, 0.2, 6.0), S(5884))
    for nt in ["D4", "F#4", "A4", "D5"]:
        put(strings(nt, 9.0, 0.045, 0.6, 6.0), S(5884))
    put(bell("D6", 6.0, 0.12), S(5900))
    A(crickets(S(6125) - S(5960), 0.03, 14), S(5960), fade=2.0)

    # the son finds his father in the lane: one low heartbeat, then silence
    put(taiko(0.9, 0.3, 58), S(6121))
    put(taiko(0.9, 0.22, 52), S(6121) + 0.32)
    # ---- J: silence. "Abba." The door.
    A(crickets(S(6600) - S(6121), 0.022, 11), S(6121), fade=1.0)
    A(chain_knock(0.30, 11), S(6505), pan=0.1, fade=0.002)
    A(chain_knock(0.26, 12), S(6522), pan=0.1, fade=0.002)
    A(creak(1.5, 0.18), S(6550), pan=0.1, fade=0.05)
    put(strings("A4", 5.0, 0.04, 1.5, 2.0), S(6560))

    # ---- K1: the promise returns, the split dissolves
    tanpura(S(6601), S(6840), 0.07)
    motif(S(6606), PROMISE, 0.82, 0.42)
    progression(S(6630), ["D", "G", "D"], 3.2, 0.10, strings_too=True)
    A(crickets(S(6845) - S(6601), 0.02, 15), S(6601), fade=1.0)

    # ---- L1: credits
    tanpura(S(6841), S(7190), 0.06)
    progression(S(6841), ["D", "Bm", "G", "A", "D"], 3.1, 0.11)
    motif(S(6846), PROMISE, 0.72, 0.44)
    motif(S(6846) + 5.8, ANSWER + ["D5"], 0.72, 0.42)
    put(bell("D6", 6.0, 0.08), S(7120))


# ------------------------------------------------------------------ master
def rms_db(x):
    return 20 * math.log10(float(np.sqrt(np.mean(np.square(x, dtype=np.float64)))) + 1e-9)


def limiter(x, ceiling=0.89, look=0.02, smooth=0.06):
    """lookahead brickwall: the smoothed gain never exceeds what each sample needs"""
    need = np.minimum(1.0, ceiling / np.maximum(np.abs(x).max(axis=1), 1e-9))
    w = int(look * SR) * 2 + 1
    g = uniform_filter1d(minimum_filter1d(need, w), w)
    w2 = int(smooth * SR) * 2 + 1
    g = uniform_filter1d(minimum_filter1d(g, w2), w2)
    return x * g[:, None].astype(np.float32), g


def main():
    print("building score + sfx ...")
    build()
    print("placing voices ...")
    voices()
    music, amb, vo = BUS["music"], BUS["amb"], BUS["vo"]
    # duck music/ambience under the voice (about -9 dB); hold through gaps between words
    ve = uniform_filter1d(np.abs(vo).mean(axis=1), int(0.05 * SR))
    ve = uniform_filter1d(maximum_filter1d(ve, int(0.5 * SR)), int(0.25 * SR))
    duck = (1 - np.clip(ve / 0.02, 0, 1) * 0.65).astype(np.float32)
    print("reverb ...")
    music = reverb(music, 2.8, 0.26, 7)[: len(duck)] * duck[:, None]
    amb = amb * (0.5 + 0.5 * duck[:, None])
    out = (music + amb + vo)[:N]
    vo_n = vo[:N]
    loud = rms_db(out[int(fr(400) * SR): int(fr(7000) * SR)])
    gain = 10 ** ((-19.5 - loud) / 20)
    out = out * gain
    out, g = limiter(out, ceiling=0.89)
    out[: int(1.2 * SR)] *= np.linspace(0, 1, int(1.2 * SR), dtype=np.float32)[:, None]
    out[-int(2.5 * SR):] *= np.linspace(1, 0, int(2.5 * SR), dtype=np.float32)[:, None]
    os.makedirs(os.path.join(ROOT, "audio"), exist_ok=True)
    path = os.path.join(ROOT, "audio", "mix.wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
    # report: loudness per sequence + limiter activity, so levels can be audited without ears
    lines = [f"mix {len(out) / SR:.2f}s  overall {rms_db(out):.1f} dBFS rms  peak {20 * math.log10(np.abs(out).max() + 1e-9):.1f} dBFS  "
             f"min limiter gain {20 * math.log10(g.min() + 1e-9):.1f} dB"]
    for sid, a, b, *_ in TL.SEQ:
        i0, i1 = int(fr(a) * SR), int(fr(b + 1) * SR)
        seg, vs = out[i0:i1], vo_n[i0:i1] * gain
        lines.append(f"{sid:4s} {a:5d}-{b:5d}  rms {rms_db(seg):6.1f}  L {rms_db(seg[:, 0]):6.1f} R {rms_db(seg[:, 1]):6.1f}"
                     f"  peak {20 * math.log10(np.abs(seg).max() + 1e-9):6.1f}  limiter {20 * math.log10(g[i0:i1].min() + 1e-9):5.1f}"
                     + (f"  voice {rms_db(vs):6.1f}" if np.abs(vs).max() > 1e-4 else ""))
    rep = "\n".join(lines)
    open(os.path.join(ROOT, "audio", "mix_report.txt"), "w").write(rep)
    print(rep)
    print("wrote", path)


if __name__ == "__main__":
    main()
