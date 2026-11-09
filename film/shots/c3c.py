# C3c (1:06–1:09, 72f): climbing hard — trail of smoke below, sky deepening; camera tracks from below.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_launch as sl, sets_space as sp

S = shot.Shot("C3c", frames=72)
rocket = sl.setup()
white, warm = sl.smoke_mats()
sl.plume(rocket, 1, 2, length=26.0)
keys = [(1, 260.0), (72, 620.0)]
for f, z in keys:
    rocket.location = (0, 0, z)
    rocket.keyframe_insert("location", frame=f)
af.set_interp(rocket, "LINEAR")
sl.trail_puffs("trail", 120.0, 612.0, -40, 72, white, step=2.6, r=(2.5, 9.0), spread=2.0)          # dense, billowing plume
sl.trail_puffs("trailb", 124.0, 612.0, -40, 72, white, step=3.4, r=(1.8, 6.5), seed=11, spread=3.2)
cam = S.cam("cam", keys=[(1, (60.0, -80.0, 200.0), (0.0, 0.0, 262.0), 38.0), (72, (60.0, -80.0, 520.0), (0.0, 0.0, 628.0), 38.0)])
S.shake(cam, 1, 72, strength=0.012, scale=1.4)
# sky darkens with altitude: animate world colour strength subtly via exposure
sc = bpy.context.scene
sc.view_settings.exposure = 0.0
sc.view_settings.keyframe_insert("exposure", frame=1)
sc.view_settings.exposure = -0.35
sc.view_settings.keyframe_insert("exposure", frame=72)
S.finish(step=1, bloom=(0.85, 1.0, 0.7))
