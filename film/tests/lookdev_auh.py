import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, scene_auh, poses

af.clear_scene()
af.setup_scene(samples=16, w=960, h=1080)
A = scene_auh.construction()
rigs = poses.load_chars(["FATHER_75_WORK"], palette=scene_auh.SUNSET_CAST)
fa = rigs["FATHER_75_WORK"]
fa.location = scene_auh.SCAFFOLD_PLANK
fa.rotation_euler = (0, 0, math.radians(10))
poses.apply(fa, poses.merge(poses.STAND, {"head": (-4, 0, 0), "upperarm01.R": (30, 0, 30), "lowerarm01.R": (60, 0, 0)}))
af.add_camera("cam", (1.6, -4.6, 7.4), (-2.0, -40.0, 9.0), lens=28)
af.compositor(bloom=(0.85, 0.9, 0.7))
af.render_still(os.path.join(af.ROOT, "tests", "auh_sunset.png"))
af.clear_scene()
af.setup_scene(samples=16, w=960, h=1080)
A = scene_auh.camp_roof()
rigs = poses.load_chars(["FATHER_75_WORK"], palette=scene_auh.NIGHT_CAST)
fa = rigs["FATHER_75_WORK"]
fa.location = (0.0, -2.0, 6.6)
fa.rotation_euler = (0, 0, math.radians(180))
poses.apply(fa, poses.STAND_LOOK_UP_HIGH)
af.moon("moon_auh", Vector((0.2, 0.9, 0.55)).normalized() * 400, 16.0, cam_dir=-Vector((0.2, 0.9, 0.55)))
af.add_camera("cam", (1.8, -4.6, 7.5), (-0.6, 12.0, 12.5), lens=26)
af.compositor(bloom=(0.8, 0.9, 0.7))
af.render_still(os.path.join(af.ROOT, "tests", "auh_night.png"))
print("AF: done")
