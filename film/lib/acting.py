# ALWAYS FALLING - the acting sheet. Facial expressions per shot, keyed to the story beats (shot-local frames).
# Timeline -> local frame: local = timeline_frame - sequence_start + 1. Voice clips are placed exactly as in
# post/timeline.py AUDIO_VO, so lip-sync lines up with the mix.
#   entry: character -> (keys, lips)   keys: [(frame, preset_or_dict[, transition_frames])]   lips: [(clip, start)]
import os
import af

UP = {"look_y": 0.65}


def m(*ds, **kw):
    out = {}
    for d in ds:
        out.update(d)
    out.update(kw)
    return out


WARM = {"smile": 0.38, "squint": 0.18, "brow_up": 0.12}
PRESET_WONDER = {"wide": 0.55, "brow_up": 0.55, "open": 0.14, "smile": 0.18, "look_y": 0.5}
PRESET_SMILE = {"smile": 0.8, "squint": 0.55, "brow_up": 0.15}
PRESET_SOFT = {"smile": 0.42, "squint": 0.25, "brow_up": 0.12}
PRESET_AWE = {"wide": 0.85, "brow_up": 0.85, "open": 0.3, "look_y": 0.6}
LOOKUP_SOFT = m(UP, brow_up=0.25, smile=0.15)

SHEET = {
    # --- 1975: the rooftop and the promise
    "B1": {"FATHER_75_HOME": ([(1, WARM)], []), "BOY_75": ([(1, m(WARM, smile=0.5))], [])},
    "B4a": {  # straight down from the sky: the father finishes the thesis; the boy turns to him
        "FATHER_75_HOME": ([(1, m(WARM, UP)), (40, m(WARM, UP, smile=0.32)), (66, m(UP, smile=0.22, brow_sad=0.32, lid_sad=0.15))],
                           [("B3", 705 - 889 + 1)]),
        "BOY_75": ([(1, m(PRESET_WONDER, sparkle=0.85)), (24, m(brow_up=0.35, wide=0.25, look_x=0.7, sparkle=0.5)), (70, m(brow_up=0.2, brow_sad=0.25, look_x=0.7))], []),
    },
    "B4b": {  # the promise: "...and always missing." -> "Every night when it passes, I'll look up."
        "FATHER_75_HOME": ([(1, m(smile=0.2, brow_sad=0.4, lid_sad=0.2, look_x=-0.7)), (58, m(WARM, look_x=-0.7, smile=0.5, squint=0.3))],
                           [("B3", 705 - 985 + 1), ("B4", 1045 - 985 + 1)]),
        "BOY_75": ([(1, m(brow_sad=0.45, lid_sad=0.15, look_x=0.75)), (66, m(look_x=0.75, smile=0.35, brow_up=0.35, wide=0.2, sparkle=0.8)),
                    (86, m(look_x=0.75, smile=0.6, squint=0.3, brow_up=0.2, sparkle=0.6))], []),
    },
    # --- departure and the first nights
    "C2L": {"BOY_75": ([(1, m(UP, brow_up=0.35, wide=0.2))], [])},
    "C2R": {"FATHER_75_WORK": ([(1, m(UP, brow_sad=0.35, smile=0.12))], [])},
    # --- letters, the note, the dot
    "E1L": {"BOY_75": ([(1, m(UP, brow_up=0.3))], [])},
    "E1R": {"FATHER_75_WORK": ([(1, m(look_y=-0.7, brow_sad=0.3, smile=0.25)), (70, m(look_y=-0.7, smile=0.45, squint=0.2, brow_sad=0.2))], [])},
    "E2R": {"FATHER_75_WORK": ([(1, m(smile=0.3, look_y=-0.4))], [])},
    "E3L": {"BOY_75": ([(1, "wonder"), (92, m(UP, smile=0.85, squint=0.5, brow_up=0.3)), (160, m(UP, smile=0.55, squint=0.3))], [])},
    "E3R": {"FATHER_75_WORK": ([(1, m(UP, smile=0.3, brow_sad=0.25)), (80, m(UP, smile=0.45, squint=0.2, brow_sad=0.2))], [])},
    # --- the years
    "F1L": {"BOY_79": ([(1, m(brow_down=0.25, look_y=-0.6)), (100, m(UP, brow_up=0.4, wide=0.25, sparkle=1.0)),
                        (116, m(UP, smile=0.6, squint=0.3, brow_up=0.25, sparkle=0.8)), (160, m(look_y=-0.6, brow_down=0.15, smile=0.2))], [])},
    "F1R": {"FATHER_75_WORK": ([(1, m(brow_down=0.25, frown=0.2, blink=0.15))], [])},
    "F2L": {"BOY_79": ([(1, m(brow_up=0.25, look_y=-0.2)), (56, m(PRESET_SMILE, sparkle=0.7)), (118, m(smile=0.95, squint=0.6, brow_up=0.15, sparkle=0.6)),
                        (178, m(UP, smile=0.6, brow_up=0.35, sparkle=0.8)), (232, m(PRESET_SOFT, sparkle=0.3))], []),
            },
    "F2R": {"FATHER_75_WORK": ([(1, m(smile=0.25, brow_sad=0.3)), (50, m(smile=0.45, squint=0.2, brow_sad=0.35, lid_sad=0.2)),
                                (185, m(smile=0.2, brow_sad=0.6, lid_sad=0.4, tears=0.45)), (225, m(brow_sad=0.6, tears=0.5, blink=0.3))],
                               [("F2", 3170 - 3121 + 1)])},
    "F4L": {"BOY_79": ([(1, m(UP, brow_up=0.2))], [])},
    "F4R": {"FATHER_75_WORK": ([(1, m(UP, brow_sad=0.3))], [])},
    "F5L": {"BOY_81": ([(1, "numb"), (64, m(smile=0.22, look_y=-0.3, brow_sad=0.2)), (190, m(brow_sad=0.45, look_y=-0.5, blink=0.25, frown=0.2))], [])},
    "F5R": {"FATHER_75_WORK": ([(1, m(brow_sad=0.55, lid_sad=0.3, blink=0.35, frown=0.3, look_y=-0.6))], [])},
    # --- the last tape: "Beta... forgive me... next year, maybe-"  CLICK (local 111), the head drops (120-140)
    "G1L": {"BOY_81": ([(1, m(brow_up=0.3, smile=0.2, look_y=-0.2)), (28, m(brow_sad=0.5, lid_sad=0.2)),
                        (62, m(brow_sad=0.8, lid_sad=0.4, frown=0.35)), (94, m(brow_sad=0.85, lid_sad=0.45, frown=0.5, tears=0.45)),
                        (112, m(brow_sad=0.75, brow_down=0.3, frown=0.75, tears=0.65, lid_angry=0.1), 2),
                        (134, m(brow_sad=0.9, blink=0.8, frown=0.6, tears=0.6))], [])},
    "G2R": {"FATHER_75_WORK": ([(1, m(UP, brow_up=0.2, smile=0.15)), (60, m(UP, smile=0.3)), (128, m(UP, brow_sad=0.45, lid_sad=0.3))], [])},
    "G3R": {"FATHER_75_WORK": ([(1, m(UP, brow_sad=0.4))], [])},
    # --- 1992
    "I1L": {"SON_92": ([(1, m(blink=0.35, look_y=-0.6, frown=0.15, brow_sad=0.2))], [])},
    "I1R": {"FATHER_92": ([(1, m(brow_sad=0.45, lid_sad=0.3, look_y=-0.3)), (120, m(brow_sad=0.5, frown=0.3, look_y=0.1))], [])},
    "I3L": {"SON_92": ([(1, m(blink=0.35, look_y=-0.6, frown=0.15)), (46, "shock", 2), (90, m(PRESET_AWE, sparkle=1.0)),
                        (140, m(UP, wide=0.6, brow_up=0.6, brow_sad=0.35, open=0.15, tears=0.35, sparkle=0.8))], [])},
    "I3R": {"FATHER_92": ([(1, m(brow_sad=0.4, look_y=-0.3)), (38, "shock", 2), (80, m(PRESET_AWE, sparkle=1.0)),
                           (130, m(UP, wide=0.4, brow_sad=0.6, tears=0.65, smile=0.25, sparkle=0.8))], [], [("L", 132)])},
    "I4W": {"SON_92": ([(1, m(wide=0.6, brow_up=0.5, look_y=-0.9)), (120, m(brow_sad=0.7, tears=0.6, look_y=-0.9))], []),
            "FATHER_92": ([(1, m(UP, wide=0.4, brow_sad=0.4)), (120, m(UP, brow_sad=0.8, lid_sad=0.35, tears=1.0, smile=0.5, squint=0.2))], [])},
    "J1": {"FATHER_92": ([(1, m(look_y=0.9, brow_sad=0.6, tears=0.75, open=0.05)), (84, m(brow_sad=0.6, blink=0.45, look_y=-1.0, frown=0.35, tears=0.6)),
                          (150, m(brow_sad=0.75, blink=0.5, look_y=-0.9, tears=0.6, frown=0.3))], [])},
    "J2": {"SON_92": ([(1, m(brow_sad=0.7, tears=0.6, look_y=-0.8, wide=0.2)), (40, m(brow_sad=1.0, lid_sad=0.4, tears=1.0, look_y=-0.8)),
                       (92, m(brow_sad=0.8, tears=1.0, smile=0.45, squint=0.2, look_y=-0.8, sparkle=0.6)), (140, m(sparkle=0.7, brow_sad=0.8, lid_sad=0.35,
                                                                                                            tears=1.0, smile=0.55, squint=0.25, look_y=-0.8))],
                      [("J2", 6360 - 6313 + 1)], [("R", 98)])},
    "J3": {"FATHER_92": ([(1, m(brow_sad=0.5, frown=0.2, tears=0.4)), (84, m(brow_up=0.4, wide=0.3, tears=0.6, open=0.1)),
                          (104, m(brow_sad=0.8, lid_sad=0.35, tears=1.0, smile=0.5, squint=0.2, sparkle=0.6))], [], [("R", 98)])},
    "K1W": {"SON_92": ([(1, m(UP, smile=0.5, tears=0.3))], []), "FATHER_92": ([(1, m(UP, smile=0.55, squint=0.25))], [])},
    "A2L": {"SON_92": ([(1, m(UP, smile=0.5, tears=0.3))], []), "FATHER_92": ([(1, m(UP, smile=0.55, squint=0.25))], [])},
    "A2R": {"SON_92": ([(1, m(UP, smile=0.5, tears=0.3))], []), "FATHER_92": ([(1, m(UP, smile=0.55, squint=0.25))], [])},
}
GAIN = {"J2": 1.4}


def apply(sid):
    import face
    plan = SHEET.get(sid)
    if not plan:
        return
    for name, entry in plan.items():
        keys, lips = entry[0], entry[1]
        drops = entry[2] if len(entry) > 2 else []
        F = face.REGISTRY.get(name)
        if F is None:
            continue
        for side, f in drops:
            F.tear_drop(side, f)
        for k in keys:
            if len(k) == 3:
                F.key(k[0], k[1], trans=k[2])
            else:
                F.key(k[0], k[1])
        for clip, start in lips:
            F.lipsync(os.path.join(af.ROOT, "audio", "vo", clip + ".wav"), start, gain=GAIN.get(sid, 1.0))
    print("AF: acting applied", sid, list(plan))
