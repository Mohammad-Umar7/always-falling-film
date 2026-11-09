# Render an expression sheet for one character: blender -b --factory-startup -P tests/face_test.py -- SON_92 [preset,preset,...]
import bpy, sys, os, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "lib"))
import af, poses, face
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
name = argv[0] if argv else "SON_92"
presets = argv[1].split(",") if len(argv) > 1 else ["neutral", "soft_smile", "smile", "wonder", "awe", "worry", "sad", "sad_closed",
                                                    "bittersweet", "hurt", "teary", "teary_smile", "shame", "shock", "resolve", "open_talk"]
pal = argv[2] if len(argv) > 2 else "NIGHT_CAST"
af.clear_scene()
N = 10 * (len(presets) + 1)
sc = af.setup_scene(w=420, h=420, samples=16, f0=1, f1=N)
rigs = poses.load_chars([name], palette=getattr(poses, pal))
rig = rigs[name]
F = face.Face(rig, auto_blink=False)
for k, pr in enumerate(presets):
    f = 10 * (k + 1)
    if pr == "open_talk":
        F.key(f, {"open": 0.6, "brow_up": 0.2})
    else:
        F.key(f, pr, trans=1)
F.bake(1, N)
poses.apply(rig, poses.STAND, frame=1)
bpy.context.view_layer.update()
eyes = [o for o in rig.children if "_eye_sclera" in o.name]
fc = sum((o.matrix_world.translation for o in eyes), Vector()) / max(1, len(eyes))
fc = sum(((o.matrix_world @ o.data.vertices[0].co) for o in eyes), Vector()) / max(1, len(eyes))
fc.z -= 0.03
af.sky_world([(-1, "#20264A"), (0, "#3A4A86"), (1, "#141A40")], ambient="#4A5A96", ambient_strength=0.9, stars=None)
af.add_sun("key", (0.35, 0.8, -0.5), "#C8D6FF", energy=2.2, angle=1.0)
cam = af.add_camera("cam", fc + Vector((0.06, -0.62, 0.03)), fc, lens=85.0)
sc.camera = cam
out = os.path.join(ROOT, "tests", "face")
os.makedirs(out, exist_ok=True)
for k, pr in enumerate(presets):
    f = 10 * (k + 1)
    sc.frame_set(f)
    sc.render.filepath = os.path.join(out, f"{name}_{k:02d}_{pr}.png")
    bpy.ops.render.render(write_still=True)
print("AF: face test done")
