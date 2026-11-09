import bpy, sys, os, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "lib"))
import af, poses
from mathutils import Vector
poses.CHARS_BLEND = os.path.join(af.ASSETS, "chars_v2.blend")
af.clear_scene()
sc = af.setup_scene(w=900, h=900, samples=16, f0=1, f1=2)
rigs = poses.load_chars(["BOY_75"], palette=poses.NIGHT_CAST)
r = rigs["BOY_75"]
poses.apply(r, poses.STAND_LOOK_UP_HIGH, frame=None)
af.sky_world([(-1, "#20264A"), (0, "#3A4A86"), (1, "#141A40")], ambient="#4A5A96", ambient_strength=0.9, stars=None)
af.add_sun("key", (0.35, -0.8, -0.5), "#C8D6FF", energy=2.2, angle=1.0)
out = os.path.join(ROOT, "tests", "face")
for yaw, lab in ((180, "back"), (150, "back34")):
    r.rotation_euler = (0, 0, math.radians(yaw))
    bpy.context.view_layer.update()
    cam = af.add_camera("cam" + lab, (0, -2.6, 0.62), (0, 0, 0.6), lens=55.0)
    sc.camera = cam
    sc.render.filepath = os.path.join(out, f"boy75_{lab}.png")
    bpy.ops.render.render(write_still=True)
print("AF: back test done")
