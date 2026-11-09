# V3 voices: Microsoft neural TTS (edge-tts) instead of Piper - far more natural Hindi/Urdu and Indian English.
# Every line is built from short chunks placed at fixed times inside its clip, so the English subtitles
# (post/timeline.py SUBS) and the lip-sync (lib/acting.py reads audio/vo/<clip>.wav at render time) stay in step.
# The speaking rate of each chunk is fitted so it fills its subtitle window without running over.
#   python post/vo_edge.py            -> writes audio/vo/*.wav (Piper originals are kept in audio/vo_piper/)
import asyncio, os, shutil, subprocess, sys, json
import numpy as np
import wave
import edge_tts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio", "vo")
BACK = os.path.join(ROOT, "audio", "vo_piper")
TMP = os.path.join(ROOT, "audio", "_tts")
SR = 48000
FFMPEG = shutil.which("ffmpeg") or r"C:\ffmpeg\bin\ffmpeg.exe"

VOICE = {"father": ("hi-IN-MadhurNeural", "-3Hz"),
         "father_old": ("hi-IN-MadhurNeural", "-7Hz"),      # 1980-81 tapes: the same man, more tired
         "son": ("ur-IN-SalmanNeural", "+0Hz"),
         "radio": ("en-IN-PrabhatNeural", "+0Hz"),
         "news": ("hi-IN-SwaraNeural", "+0Hz")}            # 1992: an All India Radio newsreader from a window

# clip -> (voice, [(start_s, end_limit_s, text, rate%)], cut)   times are relative to the clip start (AUDIO_VO)
# cut = (word, seconds_into_word, clip_cut_s): the clip is hard-cut that far into that word (radio dies / tape stops)
LINES = {
    "B2": ("father", [(0.10, 5.40, "अगले हफ़्ते, अपने मुल्क का पहला सैटेलाइट, वहाँ ऊपर जाएगा।", -6)], None),
    "B3": ("father", [(0.21, 4.40, "वो हमेशा ज़मीन की तरफ़ गिरता रहता है।", -10),
                      (4.63, 9.00, "लेकिन इतनी तेज़ चलता है, कि हर बार चूक जाता है।", -8),
                      (9.29, 13.90, "हमेशा घर की तरफ़ गिरता है, और हमेशा चूक जाता है।", -16)], None),
    "B4": ("father", [(0.21, 4.33, "हर रात जब वो गुज़रेगा, मैं ऊपर देखूँगा।", -10),
                      (4.50, 6.40, "तुम भी ऊपर देखना।", -12),
                      (6.63, 10.15, "फिर हम दोनों, एक ही चीज़ देख रहे होंगे।", -14)], None),
    "C4": ("radio", [(0.05, 3.50, "Acquisition of signal. Aryabhata is in orbit.", 0)], None),
    "D1": ("radio", [(0.05, 2.62, "Telemetry nominal. Spin rate stable.", 0),
                     (2.83, 5.02, "X-ray detector on. Day three.", 0),
                     (5.25, 7.02, "Solar panel current dropping.", 0),
                     (7.25, 9.80, "Day four. Power bus voltage dropping.", 14)], ("voltage", 0.17, 9.29)),
    "F2": ("father", [(0.08, 5.02, "बेटा, अब्बा ठीक हैं। बिल्डिंग अब बहुत ऊँची हो गई है।", -4),
                      (5.33, 7.55, "रात को ऊपर देखते हो ना?", -6)], None),
    "F5": ("father_old", [(0.10, 0.95, "बेटा,", -18),
                          (1.10, 2.75, "दिल लगा के पढ़ना।", -18),
                          (3.00, 4.95, "अम्मी का ख़्याल रखना।", -18)], None),
    "G1": ("father_old", [(0.20, 1.05, "बेटा,", -22),
                          (1.35, 2.60, "माफ़ करना।", -22),
                          (2.95, 4.45, "अगले साल,", -20),
                          (4.84, 6.00, "शायद अगले साल।", -20)], ("शायद", 0.20, 5.04)),
    "J2": ("son", [(0.12, 1.30, "ابّا۔", -30)], None),
    # ---- the ending, said out loud (V3)
    "N1": ("news", [(0.10, 3.50, "आकाशवाणी। भारत का पहला उपग्रह, आर्यभट्ट,", -4),
                    (3.75, 7.70, "सत्रह साल बाद, आज रात धरती पर लौट रहा है।", -4)], None),
    "J3": ("father_old", [(0.10, 0.75, "बेटा...", -18),
                          (0.95, 1.80, "मैं आ गया।", -14)], None),
    "K1a": ("father_old", [(0.10, 1.10, "हर रात...", -16),
                           (1.40, 3.20, "मैं ऊपर देखता था।", -10)], None),
    "K1b": ("son", [(0.10, 0.90, "میں بھی...", -18),
                    (1.05, 1.90, "ابّا۔", -22)], None),
}


def decode(path):
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


async def synth(text, who, rate, path):
    voice, pitch = VOICE[who]
    com = edge_tts.Communicate(text, voice, rate=f"{rate:+d}%", pitch=pitch, boundary="WordBoundary")
    words = []
    with open(path, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append((ch["text"], ch["offset"] / 1e7, ch["duration"] / 1e7))
    return words


def trim(x, words, thr_db=-42.0, pre=0.025, post=0.06):
    a = np.abs(x)
    k = max(1, int(0.01 * SR))
    e = np.convolve(a, np.ones(k) / k, mode="same")
    on = np.where(e > e.max() * 10 ** (thr_db / 20))[0]
    if not len(on):
        return x, words
    s = max(0, on[0] - int(pre * SR))
    t = min(len(x), on[-1] + int(post * SR))
    shift = s / SR
    return x[s:t], [(w, o - shift, d) for w, o, d in words]


def fit_chunk(key, i, text, who, rate, avail, final_cut=False):
    lo = min(-20, rate)
    """synthesize, then refit the rate so the chunk fills ~92% of its window (never more than 100%)"""
    best = None
    for it in range(4):
        p = os.path.join(TMP, f"{key}_{i}_{it}.mp3")
        words = asyncio.run(synth(text, who, rate, p))
        x, words = trim(decode(p), words)
        dur = len(x) / SR
        best = (x, words, rate, dur)
        if final_cut:
            return best
        if 0.80 * avail <= dur <= 0.98 * avail:
            break
        target = 0.92 * avail
        new = int(round((100 + rate) * dur / target - 100))
        new = max(lo, min(30, new))
        if new == rate:
            break
        if dur < 0.80 * avail and new < rate and rate <= lo:
            break
        rate = new
    return best


def build(key):
    who, chunks, cut = LINES[key]
    end = max(c[1] for c in chunks) + 0.5
    clip = np.zeros(int(end * SR) + SR, np.float32)
    report = []
    last_end = 0.0
    for i, (st, lim, text, rate) in enumerate(chunks):
        is_cut = cut is not None and i == len(chunks) - 1
        x, words, r, dur = fit_chunk(key, i, text, who, rate, lim - st, final_cut=is_cut)
        if is_cut:
            w, into, at = cut
            bias = (0.025 - words[0][1]) if words else 0.0
            onset = next((o + bias for (ww, o, d) in words if w in ww or ww in w), None)
            if onset is None:
                print("  ! cut word not found", key, w, words)
                onset = dur * 0.6
            st = at - into - onset                 # the cut lands `into` seconds into the word
        st = max(st, last_end + 0.12)
        a = int(st * SR)
        if a + len(x) > len(clip):
            clip = np.concatenate([clip, np.zeros(a + len(x) - len(clip) + SR, np.float32)])
        clip[a:a + len(x)] += x
        last_end = st + dur
        report.append(f"{st:5.2f}-{st + dur:5.2f}s (limit {lim:5.2f}) rate {r:+d}%  {text}")
    if cut is not None:
        n = int(cut[2] * SR)
        clip = clip[:n]
        clip[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))      # tape stop / dead air: hard cut
    else:
        nz = np.where(np.abs(clip) > 1e-4)[0]
        clip = clip[: nz[-1] + int(0.15 * SR)] if len(nz) else clip
    peak = np.abs(clip).max() + 1e-9
    clip = clip / peak * 0.89
    with wave.open(os.path.join(OUT, key + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(clip, -1, 1) * 32767).astype(np.int16).tobytes())
    print(key, f"{len(clip) / SR:.2f}s")
    for ln in report:
        print("   ", ln)


def main():
    os.makedirs(TMP, exist_ok=True)
    if not os.path.isdir(BACK):
        os.makedirs(BACK)
        for f in os.listdir(OUT):
            if f.endswith(".wav"):
                shutil.copy2(os.path.join(OUT, f), os.path.join(BACK, f))
    keys = sys.argv[1:] or list(LINES)
    for k in keys:
        build(k)
    shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
