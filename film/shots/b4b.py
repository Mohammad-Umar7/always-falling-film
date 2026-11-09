# B4b (0:41-0:45, 96f): the promise. Two-shot from beyond their feet so both faces read upright: father and son turn
# to each other while the father promises "Every night when it passes, I'll look up." (faces carry the beat)
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_b, poses

S = shot.Shot("B4b", frames=96)
H, rigs = scene_b.night_roof(moon_dir=(-0.4, 0.3, 0.86), moon_size=22.0)
fa, boy = rigs["FATHER_75_HOME"], rigs["BOY_75"]
poses.key_sequence(fa, [(1, poses.merge(poses.LIE, {"head": (-4, -20, 0)})), (50, poses.merge(poses.LIE, {"head": (-4, -20, 0)})),
                        (60, poses.merge(poses.LIE, {"head": (-2, -34, 0)})), (96, poses.merge(poses.LIE, {"head": (-2, -34, 0)}))], step=2)
poses.key_sequence(boy, [(1, poses.merge(poses.LIE, {"head": (-4, 30, 0)})), (64, poses.merge(poses.LIE, {"head": (-4, 30, 0)})),
                         (72, poses.merge(poses.LIE, {"head": (-6, 36, 0)})), (96, poses.merge(poses.LIE, {"head": (-6, 36, 0)}))], step=2)
bpy.context.view_layer.update()
hf = fa.matrix_world @ fa.pose.bones["head"].tail
hb = boy.matrix_world @ boy.pose.bones["head"].tail
mid = (hf + hb) / 2
if af.v4():                     # V4: he talks with his head and hand, not just his lips
    import body
    body.speech_gesture(fa, "B4", 61, 96, head=(5.6, 2.0))
S.cam("cam", keys=[(1, tuple(mid + Vector((0.05, 0.95, 1.05))), tuple(mid + Vector((0, 0.16, -0.02))), 40.0),
                   (96, tuple(mid + Vector((0.04, 0.84, 0.95))), tuple(mid + Vector((0, 0.14, -0.02))), 42.0)])
S.finish(step=1)
