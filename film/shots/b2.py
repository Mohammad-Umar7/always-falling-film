# B2 (0:21–0:29, 192f): POV from behind the father's head — his arm rises and points at the sky.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_b, poses

S = shot.Shot("B2", frames=192)
H, rigs = scene_b.night_roof(moon_dir=(0.16, 0.52, 0.84), moon_size=26.0)
fa, boy = rigs["FATHER_75_HOME"], rigs["BOY_75"]
poses.key_sequence(fa, [(1, poses.LIE), (36, poses.LIE), (52, poses.LIE_POINT_L), (192, poses.LIE_POINT_L)], step=2)
poses.key_sequence(boy, [(1, poses.merge(poses.LIE, {"head": (-4, -24, 0)})), (78, poses.merge(poses.LIE, {"head": (-4, -24, 0)})),
                         (90, poses.merge(poses.LIE, {"head": (-16, -4, 0)})), (192, poses.merge(poses.LIE, {"head": (-16, -4, 0)}))], step=3)
S.cam("cam", keys=[(1, (-0.08, -0.42, 0.80), (0.55, 3.6, 5.6), 17.0),
                   (192, (-0.07, -0.38, 0.82), (0.55, 3.5, 5.8), 18.5)])
S.finish(step=1)
