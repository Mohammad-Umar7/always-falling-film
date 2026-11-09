# B4b (0:41-0:45, 96f): the promise. Two-shot from beyond their feet so both faces read upright: father and son turn
# to each other; the boy's small hand settles on his father's hand resting on his chest while he promises
# "Every night when it passes, I'll look up."
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_b, poses

S = shot.Shot("B4b", frames=96)
H, rigs = scene_b.night_roof(moon_dir=(-0.4, 0.3, 0.86), moon_size=22.0)
fa, boy = rigs["FATHER_75_HOME"], rigs["BOY_75"]
HAND_CHEST_R = {"upperarm01.R": (26, 0, 24), "lowerarm01.R": (96, 0, 0), "lowerarm02.R": (0, 40, 0)}
poses.key_sequence(fa, [(1, poses.merge(poses.LIE, HAND_CHEST_R, {"head": (-4, 22, 0)})), (50, poses.merge(poses.LIE, HAND_CHEST_R, {"head": (-4, 22, 0)})),
                        (60, poses.merge(poses.LIE, HAND_CHEST_R, {"head": (-2, 34, 0)})), (96, poses.merge(poses.LIE, HAND_CHEST_R, {"head": (-2, 34, 0)}))], step=2)
poses.apply(boy, poses.merge(poses.LIE, {"head": (-4, 34, 0)}), frame=1)
bpy.context.view_layer.update()
hand = fa.matrix_world @ fa.pose.bones["lowerarm02.R"].tail
eb = scene_b.ik_arm(boy, "L", hand)
rest = boy.matrix_world @ boy.pose.bones["lowerarm02.L"].tail
tgt = hand + Vector((0.03, 0.0, 0.035))
for f, p in [(1, rest), (34, rest), (40, rest.lerp(tgt, 0.5) + Vector((0, 0, 0.05))), (46, tgt), (96, tgt)]:
    eb.location = p
    eb.keyframe_insert("location", frame=f)
af.set_interp(eb, "CONSTANT")
bpy.context.view_layer.update()
hf = fa.matrix_world @ fa.pose.bones["head"].tail
hb = boy.matrix_world @ boy.pose.bones["head"].tail
mid = (hf + hb) / 2
S.cam("cam", keys=[(1, tuple(mid + Vector((0.05, 0.95, 1.05))), tuple(mid + Vector((0, 0.16, -0.02))), 40.0),
                   (96, tuple(mid + Vector((0.04, 0.84, 0.95))), tuple(mid + Vector((0, 0.14, -0.02))), 42.0)])
S.finish(step=1)
