ROOT = __file__.rsplit("tests", 1)[0]
p = ROOT + "lib/poses.py"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert a in s, "MISSING: " + a[:90]
    s = s.replace(a, b, 1)


rep('''# ------------------------------------------------------------------ apply / key
def reset(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"''', '''# ------------------------------------------------------------------ apply / key
_FACE = ("jaw", "special0", "oris", "levator", "risorius", "orbicularis", "temporalis", "tongue")


def is_face_bone(n):
    """face bones belong to lib/face.py; body poses never reset or key them"""
    return n.startswith(_FACE) or n in ("eye.L", "eye.R")


def reset(rig):
    for pb in rig.pose.bones:
        if is_face_bone(pb.name):
            continue
        pb.rotation_mode = "XYZ"''')
rep('''    if frame is not None:
        for pb in rig.pose.bones:
            pb.keyframe_insert("rotation_euler", frame=frame)''', '''    if frame is not None:
        for pb in rig.pose.bones:
            if is_face_bone(pb.name):
                continue
            pb.keyframe_insert("rotation_euler", frame=frame)''')
open(p, "w", encoding="utf-8").write(s)
import ast
ast.parse(s)
print("poses patched")
