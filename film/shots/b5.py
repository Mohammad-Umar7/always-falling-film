# B5 (0:45–0:50, 120f): high wide — two tiny figures on a charpai, the Old City and the Charminar under the stars.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_b, poses

S = shot.Shot("B5", frames=120)
H, rigs = scene_b.night_roof(moon_dir=(-0.25, 0.95, 0.2), moon_size=40.0)
fa, boy = rigs["FATHER_75_HOME"], rigs["BOY_75"]
poses.apply(fa, poses.merge(poses.LIE, {"head": (-8, 10, 0)}), frame=1)
poses.apply(boy, poses.merge(poses.LIE, {"head": (-8, -14, 0)}), frame=1)
S.cam("cam", keys=[(1, (6.0, -18.0, 12.5), (-3.0, 22.0, 4.5), 28.0),
                   (120, (7.0, -21.0, 16.0), (-4.0, 26.0, 7.0), 28.0)])
S.finish(step=1)
