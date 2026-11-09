"""Replace a TTS voice clip with a human recording (phone voice note etc.).

    python post/swap_voice.py J2 "C:/path/to/abba.m4a"          # one clip
    python post/swap_voice.py B3 rec.ogg --fit                    # time-stretch to the old clip's length (keeps subs/edit)

- converts any format with ffmpeg to 22.05 kHz mono 16-bit (what the lip-sync and mixer expect)
- trims leading/trailing silence, removes DC/rumble, leaves 0.3 s of air at the start like the TTS clips
- keeps the old clip as audio/vo/<clip>_tts.wav (first time only)
- prints the new duration; rerun post/audio.py, re-render the shot (lip-sync), then composite
"""
import os, sys, subprocess, wave, shutil
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"
SR = 22050


def read(path):
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        return x.reshape(-1, w.getnchannels()).mean(axis=1) if w.getnchannels() > 1 else x, w.getframerate()


def main():
    clip, src = sys.argv[1], sys.argv[2]
    fit = "--fit" in sys.argv
    vo = os.path.join(ROOT, "audio", "vo")
    dst = os.path.join(vo, clip + ".wav")
    backup = os.path.join(vo, clip + "_tts.wav")
    if os.path.exists(dst) and not os.path.exists(backup):
        shutil.copy(dst, backup)
    old_len = read(backup)[0].size / SR if os.path.exists(backup) else None
    tmp = os.path.join(vo, f"_{clip}_raw.wav")
    af = "highpass=f=80,afftdn=nf=-25,silenceremove=start_periods=1:start_threshold=-42dB:stop_periods=-1:stop_threshold=-42dB:stop_duration=0.25"
    if fit and old_len:
        probe = subprocess.run([FFMPEG, "-v", "error", "-i", src, "-af", af, "-f", "wav", "-"], capture_output=True)
        n = (len(probe.stdout) - 44) / 2 / 48000 if probe.stdout else 0
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", src, "-af", af, "-ac", "1", "-ar", str(SR), "-sample_fmt", "s16", tmp], check=True)
    x, sr = read(tmp)
    os.remove(tmp)
    if fit and old_len:
        target = old_len - 0.6
        ratio = (x.size / sr) / max(0.3, target)
        if abs(ratio - 1) > 0.02:
            tmp2 = os.path.join(vo, f"_{clip}_fit.wav")
            r = min(2.0, max(0.5, ratio))
            subprocess.run([FFMPEG, "-v", "error", "-y", "-i", src, "-af", af + f",atempo={r:.4f}", "-ac", "1", "-ar", str(SR),
                            "-sample_fmt", "s16", tmp2], check=True)
            x, sr = read(tmp2)
            os.remove(tmp2)
    pk = np.abs(x).max() + 1e-9
    x = x / pk * 0.89
    pad = np.zeros(int(0.3 * SR), np.float32)
    y = np.concatenate([pad, x, pad])
    with wave.open(dst, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f"{clip}: {y.size / SR:.2f}s (TTS was {old_len:.2f}s)" if old_len else f"{clip}: {y.size / SR:.2f}s")


if __name__ == "__main__":
    main()
