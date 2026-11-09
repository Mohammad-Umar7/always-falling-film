# back/side views of the working father in walk poses (waistband check)
import bpy, sys, os, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "lib"))
import af, poses
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
name = argv[0] if argv else "FATHER_75_WORK"
poses.CHARS_BLEND = os.path.join(af.ASSETS, "chars_v2.blend")
af.clear_scene()
sc = af.setup_scene(w=1600, h=900, samples=16, f0=1, f1=3)
names = [name + suffix for suffix in ("",)]
rigs = poses.load_chars([name])
r = rigs[name]
af.sky_world([(-1, "#C8D8F0"), (0, "#E8E4DC"), (1, "#90B8E8")], ambient="#B0B8C8", ambient_strength=0.9, stars=None)
af.add_sun("key", (0.35, 0.8, -0.5), "#FFF4E0", energy=3.0, angle=1.0)
out = os.path.join(ROOT, "tests", "face")
for ph in range(4):
    poses.apply(r, poses.merge(poses.STAND, poses.HOLD_SUITCASE_R, poses.walk_poses(ph)), frame=None)
    for yaw, lab in ((180, "back"), (90, "side")):
        r.rotation_euler = (0, 0, math.radians(yaw))
        bpy.context.view_layer.update()
        cam = af.add_camera(f"cam{ph}{lab}", (0, -2.6, 1.0), (0, 0, 0.95), lens=60.0)
        sc.camera = cam
        sc.render.filepath = os.path.join(out, f"waist_{name}_{ph}_{lab}.png")
        bpy.ops.render.render(write_still=True)
print("AF: waist test done")
