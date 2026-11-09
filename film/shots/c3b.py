# C3b (1:02–1:06, 96f): low wide — the rocket rises out of a billowing smoke cloud, camera tilts up with it.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_launch as sl, sets_space as sp

S = shot.Shot("C3b", frames=96)
rocket = sl.setup()
white, warm = sl.smoke_mats()
sl.plume(rocket, 1, 4, length=18.0)
sp.smoke_puffs("puffw", (0, 0, 0.5), n=60, seed=3, mat=white, spread=46.0, frames=(1, 96), up=14.0)
sp.smoke_puffs("puffo", (0, 0, 0.5), n=20, seed=4, mat=warm, spread=18.0, frames=(1, 70), up=6.0)
for f, z in ((1, 0.6), (30, 3.5), (60, 16.0), (96, 48.0)):
    rocket.location = (0, 0, z)
    rocket.keyframe_insert("location", frame=f)
af.set_interp(rocket, "BEZIER")
cam = S.cam("cam", keys=[(1, (70.0, -95.0, 3.0), (0.0, 0.0, 16.0), 34.0), (96, (68.0, -92.0, 3.0), (0.0, 0.0, 52.0), 34.0)])
S.shake(cam, 1, 96, strength=0.008, scale=2.0)
S.finish(step=1, bloom=(0.85, 1.0, 0.7))
