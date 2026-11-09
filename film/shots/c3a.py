# C3a (1:00–1:02, 48f): ignition close-up at the nozzles — flame bursts, smoke explodes outward, shake.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_launch as sl, sets_space as sp

S = shot.Shot("C3a", frames=48)
rocket = sl.setup()
white, warm = sl.smoke_mats()
sl.plume(rocket, 12, 20, length=12.0)
sp.smoke_puffs("puffw", (0, 0, 0.5), n=34, seed=1, mat=white, spread=16.0, frames=(13, 48), up=4.0, ang=(20.0, 250.0))
sp.smoke_puffs("puffo", (0, 0, 0.3), n=18, seed=2, mat=warm, spread=9.0, frames=(12, 40), up=2.5, ang=(30.0, 240.0))
cam = S.cam("cam", keys=[(1, (16.0, -20.0, 2.2), (0.0, 0.0, 3.4), 40.0), (48, (17.0, -21.5, 2.0), (0.0, 0.0, 3.6), 40.0)])
S.shake(cam, 12, 48, strength=0.02, scale=1.6)
S.finish(step=1, bloom=(0.85, 1.0, 0.7))
