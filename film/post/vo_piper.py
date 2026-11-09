# Voice lines with Piper (offline neural TTS). Hindi male: IIT Madras IndicTTS "rohan"; telemetry: en_GB "alan".
import os, wave, inspect
from piper import PiperVoice
try:
    from piper import SynthesisConfig
except Exception:
    SynthesisConfig = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, "assets", "dl", "piper")
OUT = os.path.join(ROOT, "audio", "vo")
os.makedirs(OUT, exist_ok=True)
voices = {"father": PiperVoice.load(os.path.join(M, "hi_IN-rohan-medium.onnx")),
          "son": PiperVoice.load(os.path.join(M, "hi_IN-pratham-medium.onnx")),
          "radio": PiperVoice.load(os.path.join(M, "en_GB-alan-medium.onnx"))}
LINES = [
    ("B2", "father", 1.18, "अगले हफ़्ते, अपने मुल्क का पहला सैटेलाइट, वहाँ ऊपर जाएगा।"),
    ("B3", "father", 1.2, "वो हमेशा ज़मीन की तरफ़ गिरता रहता है। लेकिन इतनी तेज़ चलता है, कि हर बार चूक जाता है। हमेशा घर की तरफ़ गिरता है, और हमेशा चूक जाता है।"),
    ("B4", "father", 1.2, "हर रात जब वो गुज़रेगा, मैं ऊपर देखूँगा। तुम भी ऊपर देखना। फिर हम दोनों, एक ही चीज़ देख रहे होंगे।"),
    ("F2", "father", 1.12, "बेटा, अब्बा ठीक हैं। बिल्डिंग अब बहुत ऊँची हो गई है। रात को ऊपर देखते हो ना?"),
    ("F5", "father", 1.3, "बेटा, दिल लगा के पढ़ना। अम्मी का ख़्याल रखना।"),
    ("G1", "father", 1.35, "बेटा, माफ़ करना। अगले साल, शायद"),
    ("J2", "son", 1.4, "अब्बा।"),
    ("D1", "radio", 1.05, "Telemetry nominal. Spin rate stable. X-ray detector on. Day three. Solar panel current dropping. Day four. Power bus vol"),
    ("C4", "radio", 1.0, "Acquisition of signal. Aryabhata is in orbit."),
]
print("synth sig:", list(inspect.signature(PiperVoice.synthesize_wav).parameters) if hasattr(PiperVoice, "synthesize_wav") else "n/a")
for key, who, ls, text in LINES:
    v = voices[who]
    path = os.path.join(OUT, f"{key}.wav")
    with wave.open(path, "wb") as wf:
        if hasattr(v, "synthesize_wav") and SynthesisConfig is not None:
            v.synthesize_wav(text, wf, syn_config=SynthesisConfig(length_scale=ls, noise_scale=0.6, noise_w_scale=0.7))
        else:
            v.synthesize(text, wf, length_scale=ls)
    with wave.open(path) as r:
        print(key, round(r.getnframes() / r.getframerate(), 2), "s")
