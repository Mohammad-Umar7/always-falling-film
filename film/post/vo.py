# Generate the film's voice lines with Microsoft neural TTS (edge-tts). AI voices: declared in the docket.
import asyncio, edge_tts, os
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audio", "vo")
os.makedirs(OUT, exist_ok=True)
FATHER = "hi-IN-MadhurNeural"
SON = "ur-IN-SalmanNeural"
RADIO = "en-IN-PrabhatNeural"
LINES = [
    ("B2", FATHER, "-12%", "-2Hz", "अगले हफ़्ते... अपने मुल्क का पहला सैटेलाइट... वहाँ ऊपर जाएगा।"),
    ("B3", FATHER, "-14%", "-2Hz", "वो हमेशा ज़मीन की तरफ़ गिरता रहता है... लेकिन इतनी तेज़ चलता है कि हर बार चूक जाता है। हमेशा घर की तरफ़ गिरता है... और हमेशा चूक जाता है।"),
    ("B4", FATHER, "-14%", "-2Hz", "हर रात जब वो गुज़रेगा, मैं ऊपर देखूँगा। तुम भी ऊपर देखना। फिर हम दोनों... एक ही चीज़ देख रहे होंगे।"),
    ("F2", FATHER, "-10%", "-1Hz", "बेटा... अब्बा ठीक हैं। बिल्डिंग अब बहुत ऊँची हो गई है। रात को ऊपर देखते हो ना?"),
    ("F5", FATHER, "-18%", "-4Hz", "बेटा... दिल लगा के पढ़ना... अम्मी का ख़्याल रखना..."),
    ("G1", FATHER, "-20%", "-5Hz", "बेटा... माफ़ करना... अगले साल, शायद..."),
    ("J2", SON, "-25%", "+0Hz", "अब्बा।"),
    ("D1", RADIO, "-4%", "-2Hz", "Telemetry nominal. Spin rate stable. X-ray detector, on. ... Day three. Solar panel current, dropping. ... Day four. Power bus, vol"),
    ("C4", RADIO, "-2%", "-2Hz", "Bangalore, this is Sriharikota. We have acquisition of signal. Aryabhata is in orbit."),
]


async def main():
    for key, voice, rate, pitch, text in LINES:
        path = os.path.join(OUT, f"{key}.mp3")
        c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await c.save(path)
        print(key, os.path.getsize(path))

asyncio.run(main())
