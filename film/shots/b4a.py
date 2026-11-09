# B4a (0:37–0:41, 96f): from the sky's point of view, straight down at both faces — they turn to look at each other.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_b, poses

S = shot.Shot("B4a", frames=96)
H, rigs = scene_b.night_roof(moon_dir=(-0.4, 0.3, 0.86), moon_size=22.0)
fa, boy = rigs["FATHER_75_HOME"], rigs["BOY_75"]
up_b = poses.merge(poses.LIE, {"head": (-8, -2, 0)})
to_fa = poses.merge(poses.LIE, {"head": (-4, 34, 0)})
up_f = poses.merge(poses.LIE, {"head": (-6, 2, 0)})
to_b = poses.merge(poses.LIE, {"head": (-2, -32, 0)})
poses.key_sequence(boy, [(1, up_b), (14, up_b), (26, to_fa), (96, to_fa)], step=2)
poses.key_sequence(fa, [(1, up_f), (40, up_f), (54, to_b), (96, to_b)], step=2)
if af.v4():                     # V4: his explanation runs on into this shot (B3's clip started at timeline 705)
    import body
    body.speech_gesture(fa, "B3", 705 - 889 + 1, 96, head=(5.6, 2.0))
S.cam_up("cam", [(1, (0.42, -0.08, 1.80), (0.42, -0.08, 0.6), 40.0), (96, (0.42, -0.08, 1.68), (0.42, -0.08, 0.6), 40.0)], up=(0, -1, 0))
S.finish(step=1)
