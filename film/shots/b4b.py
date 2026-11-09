# B4b (0:41–0:45, 96f): the promise, seen from the sky — the father's hand rests on his chest; the boy's small hand
# reaches over and settles on it, little finger hooking his.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_b, poses

S = shot.Shot("B4b", frames=96)
H, rigs = scene_b.night_roof(moon_dir=(-0.4, 0.3, 0.86), moon_size=22.0)
fa, boy = rigs["FATHER_75_HOME"], rigs["BOY_75"]
HAND_CHEST_R = {"upperarm01.R": (26, 0, 24), "lowerarm01.R": (96, 0, 0), "lowerarm02.R": (0, 40, 0)}
poses.apply(fa, poses.merge(poses.LIE, poses.PINKY_R, HAND_CHEST_R, {"head": (-2, 30, 0)}), frame=1)
poses.apply(boy, poses.merge(poses.LIE, poses.PINKY_L, {"head": (-4, 34, 0)}), frame=1)
bpy.context.view_layer.update()
pb = fa.pose.bones["lowerarm02.R"]
hand = fa.matrix_world @ pb.tail
print("AF: father hand", tuple(round(x, 3) for x in hand))
eb = scene_b.ik_arm(boy, "L", hand)
rest = boy.matrix_world @ boy.pose.bones["lowerarm02.L"].tail
tgt = hand + Vector((0.035, 0.01, 0.03))
for f, p in [(1, rest), (22, rest), (30, rest.lerp(tgt, 0.5) + Vector((0, 0, 0.04))), (38, tgt), (62, tgt), (66, tgt + Vector((0, 0.012, 0.01))),
             (70, tgt), (74, tgt + Vector((0, 0.012, 0.01))), (78, tgt), (96, tgt)]:
    eb.location = p
    eb.keyframe_insert("location", frame=f)
af.set_interp(eb, "CONSTANT")
c = hand + Vector((0.05, 0.02, 0.0))
S.cam_up("cam", [(1, tuple(c + Vector((0, 0, 0.62))), tuple(c), 42.0), (96, tuple(c + Vector((0, 0, 0.55))), tuple(c), 42.0)], up=(0, -1, 0))
S.finish(step=1)
