# turnaround of the rebuilt cast (chars_v2): blender -b --factory-startup -P tests/boy_test.py -- BOY_75,BOY_81
import bpy, sys, os, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "lib"))
import af, poses, face
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
names = (argv[0] if argv else "BOY_75,BOY_81").split(",")
poses.CHARS_BLEND = os.path.join(af.ASSETS, "chars_v2.blend")
af.clear_scene()
sc = af.setup_scene(w=1600, h=900, samples=16, f0=1, f1=3)
rigs = poses.load_chars(names, palette=poses.NIGHT_CAST)
x = 0.0
for k, n in enumerate(names):
    r = rigs[n]
    F = face.Face(r, auto_blink=False)
    F.key(1, "soft_smile")
    F.bake(1, 3)
    for j, yaw in enumerate((0, 180, 90)):
        pass
af.sky_world([(-1, "#20264A"), (0, "#3A4A86"), (1, "#141A40")], ambient="#4A5A96", ambient_strength=0.9, stars=None)
af.add_sun("key", (0.35, 0.8, -0.5), "#C8D6FF", energy=2.2, angle=1.0)
out = os.path.join(ROOT, "tests", "face")
os.makedirs(out, exist_ok=True)
for yaw, lab in ((0, "front"), (180, "back"), (90, "side")):
    for k, n in enumerate(names):
        r = rigs[n]
        r.location = (k * 0.9 - 0.45 * (len(names) - 1), 0, 0)
        poses.apply(r, poses.STAND, frame=None)
        r.rotation_euler = (0, 0, math.radians(yaw))
    bpy.context.view_layer.update()
    cam = af.add_camera("cam_" + lab, (0, -4.2, 0.85), (0, 0, 0.75), lens=50.0)
    sc.camera = cam
    sc.frame_set(1)
    sc.render.filepath = os.path.join(out, f"turn_{lab}.png")
    bpy.ops.render.render(write_still=True)
print("AF: turnaround done")
