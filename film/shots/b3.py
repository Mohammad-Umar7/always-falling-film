# B3 (0:29–0:37, 192f): POV — the father's finger sweeps and Newton's cannon draws itself in light across the sky.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_b, poses

S = shot.Shot("B3", frames=192)
H, rigs = scene_b.night_roof(moon_dir=(-0.55, 0.45, 0.7), moon_size=22.0)
fa, boy = rigs["FATHER_75_HOME"], rigs["BOY_75"]
# finger sweeps slowly along the arc (shoulder yaw)
p0 = poses.LIE_POINT_L
pA = poses.merge(p0, {"upperarm01.L": (60, 0, -26)})
pB = poses.merge(p0, {"upperarm01.L": (52, 0, 4)})
poses.key_sequence(fa, [(1, pA), (60, pA), (150, pB), (192, pB)], step=2)
poses.apply(boy, poses.merge(poses.LIE, {"head": (-16, -4, 0)}), frame=1)
cam_loc = Vector((-0.06, -0.40, 0.82))
look = Vector((0.15, 0.62, 0.77)).normalized()
S.cam("cam", keys=[(1, tuple(cam_loc), tuple(cam_loc + look * 10), 20.0),
                   (192, tuple(cam_loc + Vector((0, 0.03, 0.02))), tuple(cam_loc + look * 10 + Vector((0, 0, 0.4))), 21.0)])
center = cam_loc + look * 260
curves, mat, em, t_end = scene_b.newton_cannon(center, -look, R=34.0, f0=20, fpd={"earth": 26, "traj": [14, 18, 24, 56]})
# glow fades back into the stars at the end
s_ = af.I(em, "Strength")
s_.default_value = 5.0
s_.keyframe_insert("default_value", frame=150)
s_.default_value = 0.0
s_.keyframe_insert("default_value", frame=192)
S.finish(step=1, bloom=(0.7, 1.1, 0.7))
