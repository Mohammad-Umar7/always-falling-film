import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, sets_space as sp

af.clear_scene()
af.setup_scene(samples=16, w=1920, h=1080)
af.sc = bpy.context.scene
bpy.context.scene.camera = None
sp.space_world()
sun = Vector((0.85, -0.25, 0.35)).normalized()
af.add_sun("sunlight", -sun, "#FFF6E8", energy=4.0, angle=0.6, shadow=False)
bpy.context.scene.eevee.use_raytracing = False
bpy.context.scene.eevee.use_fast_gi = False
rot = sp.face_latlon(20.0, 70.0)
sp.earth(rot=rot)
sat, body, leds = sp.aryabhata((0, 0, 0))
sat.rotation_euler = (math.radians(12), math.radians(-8), math.radians(25))
sp.sun_disc(sun)
cam = af.add_camera("cam", (2.6, -3.4, 0.9), (0.0, 0.0, -0.2), lens=35, clip=(0.05, 30000))
af.compositor(bloom=(0.8, 1.0, 0.7), streaks=(2.5, 0.25, 6))
af.render_still(os.path.join(af.ROOT, "tests", "space_close.png"))
cam2 = af.add_camera("cam2", (0.0, -700.0, 600.0), (0.0, 400.0, -900.0), lens=30, clip=(0.05, 30000))
af.render_still(os.path.join(af.ROOT, "tests", "space_earth.png"))
print("AF: done")
