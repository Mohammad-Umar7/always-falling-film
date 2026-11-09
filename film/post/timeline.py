# ALWAYS FALLING — master timeline (24 fps, 7200 frames = 5:00). Shared by the video compositor and the audio mixer.
FPS = 24
TOTAL = 7200

# (id, start, end, kind, sources, extra)
#   kind: "black" | "title" | "full" | "split" | "credits"
#   sources: full -> shot id; split -> (left id, right id); local frame = timeline - start + offset
SEQ = [
    ("A1", 1, 96, "black", None, {}),
    ("A2", 97, 288, "split", ("A2L", "A2R"), {"dot": (150, 250), "grade": "night"}),
    ("A3", 289, 360, "title", None, {}),
    ("B1", 361, 504, "full", "B1", {"grade": "dusk"}),
    ("B2", 505, 696, "full", "B2", {"grade": "night"}),
    ("B3", 697, 888, "full", "B3", {"grade": "night"}),
    ("B4a", 889, 984, "full", "B4a", {"grade": "night"}),
    ("B4b", 985, 1080, "full", "B4b", {"grade": "night"}),
    ("B5", 1081, 1200, "full", "B5", {"grade": "night"}),
    ("C1", 1201, 1344, "c1", ("C1F", "C1R"), {"split_at": 1262, "grade": "day"}),
    ("C2", 1345, 1440, "split", ("C2L", "C2R"), {"grade": "night"}),
    ("C3a", 1441, 1488, "full", "C3a", {"grade": "day", "impact": [1452, 1453], "shake": (1452, 1488, 9)}),
    ("C3b", 1489, 1584, "full", "C3b", {"grade": "day", "speed": (1489, 1584, 0.5), "shake": (1489, 1584, 4), "panels": (1546, 1584)}),
    ("C3c", 1585, 1656, "full", "C3c", {"grade": "day", "speed": (1585, 1656, 0.8), "shake": (1585, 1656, 5)}),
    ("C3d", 1657, 1728, "full", "C3d", {"grade": "space"}),
    ("C4", 1729, 1920, "full", "C4", {"grade": "space"}),
    ("D1", 1921, 2160, "full", "D1", {"grade": "space", "impact": [2101, 2102, 2104]}),
    ("D2", 2161, 2400, "full", "D2", {"grade": "space"}),
    ("E1", 2401, 2544, "split", ("E1L", "E1R"), {"dot": (2440, 2520), "grade": "night"}),
    ("E2", 2545, 2688, "split", ("E2L", "E2R"), {"grade": "mixed"}),
    ("E3", 2689, 2880, "split", ("E3L", "E3R"), {"dot": (2740, 2840), "grade": "night"}),
    ("F1", 2881, 3120, "split", ("F1L", "F1R"), {"grade": "mixed"}),
    ("F2", 3121, 3360, "split", ("F2L", "F2R"), {"grade": "night"}),
    ("F3", 3361, 3600, "split", ("F3L", "F3R"), {"grade": "night"}),
    ("F4", 3601, 3840, "split", ("F4L", "F4R"), {"dot": (3650, 3760), "rain_left": True, "haze_right": True, "grade": "night"}),
    ("F5", 3841, 4080, "split", ("F5L", "F5R"), {"grade": "night"}),
    ("G1", 4081, 4272, "split", ("G1L", "G1R"), {"grade": "night"}),
    ("G2", 4273, 4416, "split", ("G2L", "G2R"), {"dot_right_only": (4300, 4400), "grade": "night"}),
    ("G3", 4417, 4560, "split", ("G3L", "G3R"), {"grade": "night"}),
    ("H1", 4561, 5160, "full", "H1", {"grade": "space"}),
    ("I1", 5161, 5352, "split", ("I1L", "I1R"), {"grade": "night", "right_warm": True}),
    ("I2a", 5353, 5472, "full", "I2a", {"grade": "fire", "speed": (5400, 5472, 0.4), "shake": (5400, 5472, 3)}),
    ("I2b", 5473, 5592, "full", "I2b", {"grade": "fire", "speed": (5473, 5592, 1.0), "shake": (5473, 5592, 10),
                                         "impact": [5480, 5481, 5503, 5530, 5531, 5560, 5585]}),
    ("I2c", 5593, 5712, "full", "I2c", {"grade": "space"}),
    ("I3", 5713, 5880, "split", ("I3L", "I3R"), {"grade": "night", "right_warm": True, "streak_cross": (5760, 5880)}),
    ("I4", 5881, 6120, "i4", ("I3L", "I3R", "I4W"), {"burn": (5881, 5935), "grade": "night", "impact": [5881, 5882]}),
    ("J1", 6121, 6312, "full", "J1", {"grade": "night"}),
    ("J2", 6313, 6480, "full", "J2", {"grade": "night"}),
    ("J3", 6481, 6600, "full", "J3", {"grade": "night"}),
    ("K1", 6601, 6840, "k1", ("A2L", "A2R", "K1W"), {"split_offset": 192, "dissolve": (6650, 6710), "grade": "night"}),
    ("L1", 6841, 7200, "credits", None, {}),
]

# divider half-width (px) keyframes (timeline frame, px). 0 = no divider.
DIVIDER = [(1, 3), (2400, 4), (2880, 10), (3360, 40), (3840, 90), (4080, 120), (4272, 120), (5160, 110), (5880, 100)]

# typewriter mission-log + stamps: (start, end, text, where, style)
TEXTS = [
    (395, 490, "HYDERABAD · APRIL 1975", "bl", "stamp"),
    (1360, 1436, "19 APRIL 1975", "tc", "stamp"),
    (1680, 1728, "ARYABHATA  ·  ORBIT 1", "bl", "log"),
    (2180, 2400, "DAY 4.  POWER FAILURE.  EXPERIMENTS HALTED.", "bl", "log"),
    (2250, 2400, "STATUS: SILENT.", "bl2", "log"),
    (2310, 2400, "STILL IN ORBIT.", "bl3", "log"),
    (2410, 2530, "1976", "tc", "stamp"),
    (2890, 3110, "1977", "tc", "stamp"),
    (3130, 3350, "1979", "tc", "stamp"),
    (3370, 3590, "1980", "tc", "stamp"),
    (4200, 4380, "MARCH 1981.  MAINFRAME SILENT.", "bl", "log"),
    (4440, 4560, "STILL IN ORBIT.", "bl", "log"),
    (5170, 5350, "10 FEBRUARY 1992   ·   ORBIT 92,0__   ·   ALTITUDE 120 KM", "bl", "log"),
]

# subtitles (English) for the Hindi lines: (start, end, text). Matched to the audio placement in AUDIO_VO.
SUBS = [   # boundaries measured from the pauses inside each voice clip (post/audio.py places the clips)
    (522, 652, "Next week, our country's first satellite will go up there."),
    (710, 812, "It is always falling toward the Earth…"),
    (816, 922, "but it moves so fast that it misses, every time."),
    (928, 1040, "Always falling toward home… and always missing."),
    (1050, 1150, "Every night when it passes, I'll look up."),
    (1153, 1200, "You look up too."),
    (1204, 1290, "Then we'll both be looking at the same thing."),
    (1760, 1846, "Acquisition of signal. Aryabhata is in orbit."),
    (1878, 1942, "Telemetry nominal. Spin rate stable."),
    (1946, 2000, "X-ray detector on. Day three."),
    (2004, 2048, "Solar panel current dropping."),
    (2052, 2100, "Day four. Power bus vol—"),
    (3172, 3292, "Beta… Abba is fine. The building is very tall now."),
    (3298, 3352, "You look up at night, don't you?"),
    (3902, 4020, "Beta… study hard… look after Ammi…"),
    (4074, 4190, "Beta… forgive me… next year, maybe—"),
    (6362, 6440, "Abba."),
]

# voice placement (clip, start_frame, fx). D1 ends exactly on the 2101 impact frame; G1 is cut by the tape
# click at 4191, the frame the reels in G1L stop.
AUDIO_VO = [
    ("B2", 520, "outdoor"),
    ("B3", 705, "outdoor"),
    ("B4", 1045, "outdoor"),
    ("C4", 1760, "radio"),
    ("D1", 1878, "radio"),
    ("F2", 3170, "tape"),
    ("F5", 3900, "tape_far"),
    ("G1", 4070, "tape_far"),
    ("J2", 6360, "dry"),
]

# H1 orbit counter: from frame, to frame, value range; years
H1_COUNTER = (4600, 5140, 1, 92000)
H1_YEARS = [(4600, 1981), (4700, 1983), (4800, 1985), (4900, 1987), (5000, 1989), (5080, 1991)]

CREDITS = [
    ("title", "ALWAYS FALLING"),
    ("line", "a film by Team FirstCommit"),
    ("gap", ""),
    ("small", "Aryabhata, India's first satellite, was launched on 19 April 1975."),
    ("small", "Its instruments failed after four days; its mainframe stayed alive until March 1981."),
    ("small", "It kept circling until it fell back to Earth on 10 February 1992."),
    ("gap", ""),
    ("small", "The family is fictional. The re-entry seen over Hyderabad is poetic licence."),
    ("gap", ""),
    ("small", "Made in Blender with MPFB (CC0) and NASA imagery · voices: Piper TTS (IIT Madras IndicTTS)"),
    ("small", "AI-assisted production: full declaration in the submission docket"),
    ("gap", ""),
    ("line", "DADC Short Film Festival 2026 · IIT Delhi Abu Dhabi"),
]

# anime FX: manga focus lines (start, end, cx, cy, intensity, colour) and time-jump light sweeps (cut frames)
FOCUS = [
    (5758, 5784, 960, 470, 0.75, (0.0, 0.0, 0.0)),     # I3: the streak appears - both look up
    (5883, 5896, 960, 540, 0.9, (1.0, 0.95, 0.85)),    # I4: the divider burns
    (6121, 6136, 960, 520, 0.55, (0.02, 0.02, 0.08)),  # J1: the son finds his father in the lane
]
SWEEPS = [2401, 2545, 2689, 2881, 3121, 3361, 3601, 3841]

# floating light motes: (start, end, seed, count, colour, x-range or None)
MOTES = [
    (505, 1200, 11, 22, (0.75, 0.95, 0.7), None),          # rooftop promise: a few fireflies
    (2689, 2880, 12, 12, (0.75, 0.95, 0.7), (0, 960)),     # E3: the boy holds the note to the sky
    (6500, 6600, 13, 30, (1.0, 0.8, 0.5), None),           # J3: dust in the warm light from the opened door
    (6601, 6840, 14, 18, (0.75, 0.95, 0.7), None),         # K1: the ending, both on the roof
]

# who is where: manga caption boxes on each side of the split (start, end, left, right)
LABELS = [
    (112, 288, "THE SON", "THE FATHER"),
    (1266, 1344, "HYDERABAD · THE SON", "ABU DHABI · THE FATHER"),
    (1345, 1440, "HYDERABAD · THE SON", "ABU DHABI · THE FATHER"),
    (2401, 4560, "HYDERABAD · THE SON", "ABU DHABI · THE FATHER"),
    (5161, 5352, "HYDERABAD · THE SON, 1992", "THE FATHER"),
    (5713, 5880, "THE SON", "THE FATHER"),
]

# hand-drawn look switches
STYLE = {"ink": True, "boil": True, "paper": True}
