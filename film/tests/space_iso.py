import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, sets_space as sp
af.clear_scene()
af.setup_scene(samples=16, w=960, h=540)
bpy.context.scene.eevee.use_raytracing = False
bpy.context.scene.eevee.use_fast_gi = False
sp.space_world()
sun = Vector((0.85, -0.25, 0.35)).normalized()
af.add_sun("sunlight", -sun, "#FFF6E8", energy=4.0, angle=0.6, shadow=False)
objs = sp.earth(rot=sp.face_latlon(20.0, 70.0))
cam2 = af.add_camera("cam2", (0.0, -700.0, 600.0), (0.0, 400.0, -900.0), lens=30, clip=(0.05, 30000))
for tag, hide in (("all", []), ("noclouds", ["earth_clouds"]), ("noatmo", ["earth_atmo"]), ("bare", ["earth_clouds", "earth_atmo"])):
    for o in objs:
        o.hide_render = o.name in hide
    af.render_still(os.path.join(af.ROOT, "tests", f"iso_{tag}.png"))
bpy.context.scene.eevee.taa_render_samples = 64
for o in objs: o.hide_render = o.name in ["earth_clouds", "earth_atmo"]
af.render_still(os.path.join(af.ROOT, "tests", "iso_bare64.png"))
