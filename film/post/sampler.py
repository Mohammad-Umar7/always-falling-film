"""V3 score: real recorded instruments instead of synthesis (team feedback: "bad sound").
Samples: VS Chamber Orchestra 2 Community Edition (Versilian Studios, CC0); upright piano by Simon Dalzell / Ivy Audio.
Drop-in replacements for post/audio.py's pluck / strings / pad / bell / taiko / boom, same signatures and loudness.

Each note picks the nearest recorded pitch, resamples it to the exact pitch, loops the sustain with crossfades for
long notes, and shapes attack/release. File-name octave conventions differ between the instrument folders, so the
octave of every folder is checked against the measured pitch of its recordings.
"""
import os, re, glob, math
import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "assets", "dl", "vsco")
PC = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def note_midi(n):
    m = re.match(r"([A-G]#?)(-?\d+)$", n)
    return 12 * (int(m.group(2)) + 1) + PC[m.group(1)]


_cache = {}


def load(path):
    if path not in _cache:
        x, sr = sf.read(path, dtype="float32", always_2d=True)
        x = np.repeat(x, 2, 1) if x.shape[1] == 1 else x[:, :2]
        if sr != SR:
            x = signal.resample_poly(x, SR, sr, axis=0).astype(np.float32)
        # drop leading silence (keep 4 ms) so notes speak exactly on the beat
        e = np.abs(x).max(1)
        on = np.where(e > e.max() * 0.02)[0]
        a = max(0, (on[0] if len(on) else 0) - int(0.004 * SR))
        _cache[path] = np.ascontiguousarray(x[a:])
    return _cache[path]


def measured_midi(x):
    """pitch of a recording (autocorrelation on the sustain) as a fractional MIDI number, or None"""
    m = x.mean(1)
    a = min(int(0.35 * SR), len(m) // 3)
    seg = m[a:a + int(0.5 * SR)]
    if len(seg) < 4096:
        return None
    seg = (seg - seg.mean()) * np.hanning(len(seg))
    n = 1 << (2 * len(seg) - 1).bit_length()
    f = np.fft.rfft(seg, n)
    ac = np.fft.irfft(f * np.conj(f))[:len(seg)]
    lo, hi = int(SR / 2500), int(SR / 26)
    if hi >= len(ac):
        return None
    k = lo + int(np.argmax(ac[lo:hi]))
    if ac[k] <= 0:
        return None
    return 69 + 12 * math.log2((SR / k) / 440.0)


class Inst:
    def __init__(self, name, pairs, loop=False, gain=1.0, check_octave=True):
        """pairs: [(midi_from_name, path)]"""
        self.name, self.loop, self.gain = name, loop, gain
        off = 0
        if check_octave and pairs:
            votes = {-12: 0, 0: 0, 12: 0, 24: 0}
            for m0, p in pairs[:: max(1, len(pairs) // 6)]:
                d = measured_midi(load(p))
                if d is None:
                    continue
                pc = lambda o: abs(((d - (m0 + o)) + 6) % 12 - 6) < 1.2       # same pitch class?
                for o in votes:
                    if pc(o):
                        votes[o] += 1.0 / (1 + abs(d - (m0 + o)) / 6)       # prefer the octave nearest the measure
            off = max(votes, key=votes.get) if any(votes.values()) else 0
        self.off = off
        self.notes = sorted((m + off, p) for m, p in pairs)

    def nearest(self, midi):
        return min(self.notes, key=lambda t: (abs(t[0] - midi), t[0] < midi))

    def note(self, midi, dur, amp=1.0, attack=0.004, release=0.35):
        sm, p = self.nearest(midi)
        x = load(p)
        ratio = 2 ** ((midi - sm) / 12)
        n_out = int((dur + release) * SR)
        n_in = int(n_out * ratio) + 4
        if self.loop and len(x) < n_in:
            x = extend(x, n_in)
        x = x[:n_in]
        idx = np.arange(int((len(x) - 2) / ratio)) * ratio
        y = np.empty((len(idx), 2), np.float32)
        base = np.arange(len(x))
        y[:, 0] = np.interp(idx, base, x[:, 0])
        y[:, 1] = np.interp(idx, base, x[:, 1])
        y = y[:n_out]
        n = len(y)
        envl = np.ones(n, np.float32)
        na = min(n, max(1, int(attack * SR)))
        envl[:na] = np.linspace(0, 1, na) ** 1.5
        r0 = int(dur * SR)
        if r0 < n:
            nr = n - r0
            envl[r0:] *= np.linspace(1, 0, nr) ** 2
        return y * envl[:, None] * (amp * self.gain)


def extend(x, n, xf=0.45):
    """loop the sustain body with equal-power crossfades until the sample is n long"""
    a = int(min(1.0 * SR, len(x) * 0.3))
    b = len(x) - int(min(0.5 * SR, len(x) * 0.15))
    body = x[a:b]
    f = int(min(xf * SR, len(body) / 3))
    if f < 64 or len(body) < 3 * 64:
        return np.concatenate([x] * (n // len(x) + 1))[:n]
    out = x[:b].copy()
    fi = np.sqrt(np.linspace(0, 1, f, dtype=np.float32))[:, None]
    fo = np.sqrt(np.linspace(1, 0, f, dtype=np.float32))[:, None]
    while len(out) < n:
        mixed = out[-f:] * fo + body[:f] * fi
        out = np.concatenate([out[:-f], mixed, body[f:]])
    return out[:n]


def _pairs(folder, pat, keep=lambda fn: True):
    out = []
    for p in sorted(glob.glob(os.path.join(V, folder, "*.wav"))):
        fn = os.path.basename(p)
        if not keep(fn):
            continue
        m = re.search(pat, fn)
        if m:
            out.append((note_midi(m.group(1)), p))
    return out


# ------------------------------------------------------------------ the orchestra (loaded lazily)
_I = {}


def inst(k):
    if k in _I:
        return _I[k]
    if k in ("piano_p", "piano_mf"):
        dyn = "1" if k == "piano_p" else "2"
        pairs = []
        for p in glob.glob(os.path.join(V, "Keys", "Upright Piano", f"Player_dyn{dyn}_rr1_*.wav")):
            i = int(re.search(r"_(\d+)\.wav$", p).group(1))
            pairs.append((21 + 2 * i, p))                     # MappingChart: index -> key number 21 + 2i
        _I[k] = Inst(k, pairs, loop=False, gain=1.0, check_octave=False)
    elif k == "violin":
        _I[k] = Inst(k, _pairs("Strings/Violin Section/susVib", r"susVib_([A-G]#?\d)_v1"), loop=True)
    elif k == "viola":
        _I[k] = Inst(k, _pairs("Strings/Viola Section/susvib", r"susvib_([A-G]#?\d)_v1"), loop=True)
    elif k == "cello":
        _I[k] = Inst(k, _pairs("Strings/Cello Section/susvib", r"susvib_([A-G]#?\d)_v1_1"), loop=True)
    elif k == "bass":
        _I[k] = Inst(k, _pairs("Strings/Solo Contrabass/SusVib", r"SusVib_([A-G]#?\d)_v1"), loop=True)
    elif k == "harp":
        _I[k] = Inst(k, _pairs("Strings/Harp", r"KSHarp_([A-G]#?\d)_"), loop=False)
    elif k == "glock":
        _I[k] = Inst(k, _pairs("Percussion/Glock", r"medium_([A-G]#?\d)\.wav"), loop=False)
    elif k == "flute":
        _I[k] = Inst(k, _pairs("Woodwinds/Flute/susvib", r"susvib_([A-G]#?\d)_v1_1"), loop=True)
    else:
        raise KeyError(k)
    print(f"  sampler: {k:9s} {len(_I[k].notes):2d} notes, octave fix {_I[k].off:+d}")
    return _I[k]


def one_shot(rel):
    return load(os.path.join(V, rel))


# ------------------------------------------------------------------ calibration against the synth voices
# (gains chosen so a sampled note has about the RMS of the synthesized one it replaces; see tests/sampler_cal.py)
CAL = {"piano": 0.55, "strings": 0.42, "glock": 0.30, "drum": 0.75, "boom_drum": 0.45}


def string_section(midi):
    if midi < 43:
        return "bass"
    if midi < 55:
        return "cello"
    if midi < 67:
        return "viola"
    return "violin"
