import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, sets_hyd, poses

af.clear_scene()
af.setup_scene(samples=16)
H = sets_hyd.Hyd(time="night", seed=7, year=1975)
H.build()
cp = H.charpai("hero_charpai", Vector((0.4, 0.6, 0.06)), math.radians(90))
rigs = poses.load_chars(["FATHER_75_HOME", "BOY_75"], palette=poses.NIGHT_CAST)
fa, boy = rigs["FATHER_75_HOME"], rigs["BOY_75"]
for r, x, y in ((fa, 0.4 - 0.2, 1.42), (boy, 0.4 + 0.24, 0.72)):
    r.rotation_mode = "XYZ"
    r.rotation_euler = (math.radians(-90), 0, math.radians(180))
    r.location = (x, y, 0.655 if r is fa else 0.6)
poses.apply(fa, poses.LIE_POINT_L)
poses.apply(boy, poses.merge(poses.LIE, poses.LIE_TURN_R))
for cam_name, loc, tgt, lens in [("camA", (-0.75, -1.05, 0.98), (0.7, 3.2, 2.9), 22),
                                  ("camB", (0.45, 2.9, 2.6), (0.4, 0.2, 0.4), 30)]:
    cam = af.add_camera(cam_name, loc, tgt, lens=lens)
    af.compositor(bloom=(0.8, 0.8, 0.6))
    af.render_still(os.path.join(af.ROOT, "tests", f"b2_{cam_name}.png"))
af.save(os.path.join(af.ROOT, "tests", "b2_test.blend"))
print("AF: done")
