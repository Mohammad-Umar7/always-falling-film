"""Loudness of each recorded instrument vs the synth voice it replaces (same call, same arguments)."""
import os, sys
import numpy as np
HERE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "post")
sys.path.insert(0, HERE)
import audio_v2_synth as SY          # the V2 synth instruments
import audio as SA                   # V3: recorded instruments


def rms(x, sec=None):
    x = np.asarray(x, np.float32)
    if x.ndim == 2:
        x = x.mean(1) * np.sqrt(2)
    if sec:
        x = x[: int(sec * 48000)]
    return float(np.sqrt(np.mean(x ** 2)) + 1e-9)


tests = [("pluck", ("D5", 3.2, 0.3)), ("pluck", ("A4", 3.2, 0.55)), ("pluck", ("F#5", 3.2, 0.42)),
         ("strings", ("A4", 3.0, 0.06, 0.4, 1.5)), ("strings", ("D3", 8.0, 0.12, 2.0, 4.0)), ("strings", ("E5", 7.0, 0.025, 3.0, 3.0)),
         ("strings", ("D4", 3.0, 0.1, 0.4, 1.5)), ("strings", ("F#4", 3.0, 0.1, 0.4, 1.5)), ("strings", ("D2", 6.0, 0.1, 1.0, 2.0)),
         ("strings", ("A2", 6.0, 0.1, 1.0, 2.0)), ("strings", ("D5", 3.0, 0.1, 0.4, 1.5)),
         ("pad", (["D3", "F#3", "A3", "D4"], 4.8, 0.065, 1400, 1.2, 1.6)), ("pad", (["D2", "A2"], 25.0, 0.11, 600, 6.0, 4.0)),
         ("bell", ("D6", 3.0, 0.06)), ("bell", ("E7", 1.6, 0.025)),
         ("taiko", (1.2, 0.3, 80)), ("taiko", (0.9, 0.3, 58)), ("boom", (3.5, 0.35, 44))]
for name, args in tests:
    a = getattr(SY, name)(*args)
    b = getattr(SA, name)(*args)
    ra, rb = rms(a, 2.0), rms(b, 2.0)
    print(f"{name:8s} {str(args)[:46]:46s} synth {20*np.log10(ra):6.1f} dB  sampled {20*np.log10(rb):6.1f} dB  diff {20*np.log10(rb/ra):+5.1f}")
for k in ("piano_p", "piano_mf", "violin", "viola", "cello", "bass", "glock"):
    i = SA.SM.inst(k)
    print(k, "range", i.notes[0][0], "-", i.notes[-1][0])
