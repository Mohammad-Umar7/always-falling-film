# ALWAYS FALLING — pose library for MPFB "default" rig (local Euler XYZ degrees)
# Axes found numerically: upperarm Z- (L) / Z+ (R) lowers arm; upperarm X+ swings forward;
# lowerarm X+ bends elbow; upperleg X- = hip flexion (leg forward); lowerleg X+ = knee bend;
# spine/neck/head X- = lean/tilt back (look up); head Y = turn (yaw).
import bpy, math, os
import af

CHARS_BLEND = os.path.join(af.ASSETS, "chars.blend")

FINGERS = ["finger2", "finger3", "finger4", "finger5"]


def _fing(side, curl, thumb=None, skip=()):
    d = {}
    for f in FINGERS:
        if f in skip:
            continue
        for seg in (1, 2, 3):
            d[f"{f}-{seg}.{side}"] = (curl * (0.8 if seg == 1 else 1.0), 0, 0)
    if thumb is not None:
        d[f"finger1-2.{side}"] = (thumb, 0, 0)
        d[f"finger1-3.{side}"] = (thumb, 0, 0)
    return d


def merge(*ds):
    out = {}
    for d in ds:
        out.update(d)
    return out


ARMS_DOWN = {"upperarm01.L": (-4, 0, -40), "upperarm01.R": (-4, 0, 40), "lowerarm01.L": (10, 0, 0), "lowerarm01.R": (10, 0, 0),
             "upperarm02.L": (0, 0, -6), "upperarm02.R": (0, 0, 6)}
HANDS_RELAX = merge(_fing("L", 18, 10), _fing("R", 18, 10))
FIST_L = _fing("L", 75, 35)
FIST_R = _fing("R", 75, 35)
POINT_L = _fing("L", 80, 40, skip=("finger2",))
LOOK_UP = {"spine02": (-6, 0, 0), "neck01": (-16, 0, 0), "neck02": (-8, 0, 0), "head": (-22, 0, 0)}
LOOK_UP_HIGH = {"spine02": (-10, 0, 0), "spine01": (-6, 0, 0), "neck01": (-22, 0, 0), "neck02": (-12, 0, 0), "head": (-28, 0, 0)}
LOOK_DOWN = {"neck01": (14, 0, 0), "head": (16, 0, 0)}

STAND = merge(ARMS_DOWN, HANDS_RELAX)
STAND_LOOK_UP = merge(STAND, LOOK_UP)
STAND_LOOK_UP_HIGH = merge(STAND, LOOK_UP_HIGH)

PINKY_L = merge(_fing("L", 85, 45, skip=("finger5",)), {"finger5-1.L": (5, 0, 0), "finger5-2.L": (40, 0, 0), "finger5-3.L": (40, 0, 0)})
PINKY_R = merge(_fing("R", 85, 45, skip=("finger5",)), {"finger5-1.R": (5, 0, 0), "finger5-2.R": (40, 0, 0), "finger5-3.R": (40, 0, 0)})

# lying on the back (rig rotated -90 deg about X so the face points up)
LIE = merge(ARMS_DOWN, HANDS_RELAX, {"neck01": (14, 0, 0), "head": (-4, 0, 0),
                                     "upperarm01.L": (-6, 0, -43), "upperarm01.R": (-6, 0, 43)})
LIE_POINT_L = merge(LIE, POINT_L, {"upperarm01.L": (60, 0, -12), "upperarm02.L": (0, 0, 0), "lowerarm01.L": (6, 0, 0),
                                   "clavicle.L": (0, 0, 8)})
LIE_HAND_ON_CHEST_L = merge(LIE, {"upperarm01.L": (28, 0, -30), "lowerarm01.L": (110, 0, 0)})
LIE_TURN_R = {"head": (-4, 22, 0)}
LIE_TURN_L = {"head": (-4, -22, 0)}

SIT = merge(STAND, {"upperleg01.L": (-88, 0, 0), "upperleg01.R": (-88, 0, 0), "lowerleg01.L": (88, 0, 0), "lowerleg01.R": (88, 0, 0),
                    "upperarm01.L": (18, 0, -40), "upperarm01.R": (18, 0, 40), "lowerarm01.L": (30, 0, 0), "lowerarm01.R": (30, 0, 0)})
SIT_LOOK_UP = merge(SIT, LOOK_UP)
HOLD_SUITCASE_R = merge(FIST_R, {"upperarm01.R": (0, 0, 42), "lowerarm01.R": (4, 0, 0)})


def walk_poses(phase):
    """4-key stepped walk (anime on twos/threes). phase 0..3"""
    sw = [(-24, 14, 6, 28), (0, 0, 40, 6), (14, -24, 28, 6), (0, 0, 6, 40)][phase]
    ulL, ulR, llL, llR = sw[0], sw[1], sw[2], sw[3]
    arm = [18, 0, -18, 0][phase]
    return {"upperleg01.L": (ulL, 0, 0), "upperleg01.R": (ulR, 0, 0), "lowerleg01.L": (llL, 0, 0), "lowerleg01.R": (llR, 0, 0),
            "upperarm01.L": (arm, 0, -40), "spine03": (4, 0, [3, 0, -3, 0][phase])}


# ------------------------------------------------------------------ apply / key
def reset(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)


def apply(rig, pose, frame=None, interp="CONSTANT", reset_first=True):
    if reset_first:
        reset(rig)
    for bn, (x, y, z) in pose.items():
        pb = rig.pose.bones.get(bn)
        if pb is None:
            continue
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (math.radians(x), math.radians(y), math.radians(z))
    if frame is not None:
        for pb in rig.pose.bones:
            pb.keyframe_insert("rotation_euler", frame=frame)
        if interp:
            for fc in af.fcurves_of(rig):
                for kp in fc.keyframe_points:
                    if abs(kp.co.x - frame) < 0.01:
                        kp.interpolation = interp


def blend(a, b, t):
    keys = set(a) | set(b)
    out = {}
    for k in keys:
        va = a.get(k, (0, 0, 0))
        vb = b.get(k, (0, 0, 0))
        out[k] = tuple(va[i] * (1 - t) + vb[i] * t for i in range(3))
    return out


def key_sequence(rig, seq, step=2):
    """seq: list of (frame, pose). Inserts stepped (CONSTANT) keys every `step` frames, interpolating poses between
    keyframes with ease-in-out, so motion reads as hand-timed anime on twos/threes."""
    for (f0, p0), (f1, p1) in zip(seq[:-1], seq[1:]):
        f = f0
        while f < f1:
            t = (f - f0) / max(1, (f1 - f0))
            t = t * t * (3 - 2 * t)
            apply(rig, blend(p0, p1, t), frame=f)
            f += step
    apply(rig, seq[-1][1], frame=seq[-1][0])


# ------------------------------------------------------------------ cast loading
def load_chars(names, palette=None):
    """Append character collections from chars.blend; returns {name: rig}."""
    with bpy.data.libraries.load(CHARS_BLEND, link=False) as (src, dst):
        dst.collections = [n for n in names if n in src.collections]
    rigs = {}
    for col in dst.collections:
        bpy.context.scene.collection.children.link(col)
        for o in col.objects:
            if o.type == "ARMATURE":
                rigs[col.name] = o
                o.location = (0, 0, 0)
    if palette:
        retint(palette)
    return rigs


def retint(palette):
    """palette: {material_name_prefix: (base, shadow, light[, rim])} retunes TOON_RAMP colours."""
    for m in bpy.data.materials:
        for pre, cols in palette.items():
            if m.name == pre or m.name.startswith(pre + "."):
                if not m.node_tree:
                    continue
                r = m.node_tree.nodes.get("TOON_RAMP")
                if r is None:
                    # flat (eyes): set emission colour
                    for n in m.node_tree.nodes:
                        if n.bl_idname == "ShaderNodeEmission":
                            n.inputs["Color"].default_value = af.hexc(cols[0])
                    continue
                els = r.color_ramp.elements
                order = [cols[1], cols[0], cols[2]]
                for e, c in zip(els, order):
                    e.color = af.hexc(c)
                if len(cols) > 3:
                    for n in m.node_tree.nodes:
                        if n.bl_idname == "ShaderNodeMix" and n.data_type == "RGBA" and n.blend_type == "MIX":
                            for s in n.inputs:
                                if s.name == "B" and s.type == "RGBA" and not s.is_linked:
                                    s.default_value = af.hexc(cols[3])


NIGHT_CAST = {
    "SKIN": ("#9A6A7E", "#3E2A50", "#D49CA6", "#A8E0FF"),
    "SKIN_BOY": ("#A07082", "#402C52", "#DAA2AC", "#A8E0FF"),
    "HAIR": ("#16163A", "#08081C", "#3A4280", "#8FD0FF"),
    "HAIR_GREY": ("#58587A", "#2A2A44", "#9A9ACC", "#BFE6FF"),
    "EYE": ("#0A0810",),
    "CLOTH_WHITE": ("#B4C0F0", "#5A5CA0", "#EEF2FF"),
    "CLOTH_SHIRT_WORK": ("#5A86C8", "#283E78", "#8EB6F0"),
    "CLOTH_TROUSER": ("#2E2C50", "#141428", "#4A4878"),
    "CLOTH_VEST": ("#8A2A54", "#3E1028", "#C04A7A"),
    "CLOTH_SHIRT_92": ("#9AA8D8", "#4A5288", "#CAD4F8"),
    "CLOTH_SHIRT_BOY": ("#A8B6EA", "#4C5690", "#DCE6FF"),
    "CLOTH_SHORTS": ("#24407A", "#10203E", "#3E64A8"),
    "CLOTH_SHIRT_SON": ("#2E8AA6", "#143E56", "#5EC0DA"),
    "CLOTH_TROUSER_SON": ("#22223E", "#0E0E1E", "#3A3A62"),
    "CLOTH_BELT": ("#140C10", "#060406", "#2A1A20"),
    "EYE_WHITE": ("#8E96C8", "#4A4E7A", "#B6BEE8"),
    "EYE_IRIS": ("#100A0C",),
    "EYE_LASH": ("#08060A",),
}
