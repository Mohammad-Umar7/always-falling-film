import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
import af, sets_hyd
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
time = argv[0] if argv else "night"
af.clear_scene()
af.setup_scene(samples=16)
H = sets_hyd.Hyd(time=time, seed=7, year=1975).build()
H.charpai("hero_charpai", Vector((0.4, 0.6, 0.06)), math.radians(12))
af.compositor(bloom=(0.8, 0.8, 0.6))
out = os.path.join(af.ROOT, "tests")
# view 1: terrace toward the Charminar
cam = af.add_camera("cam1", (2.8, -4.2, 1.45), (-30.0, 120.0, 22.0), lens=24)
af.render_still(os.path.join(out, f"hyd_{time}_terrace.png"))
# view 2: high wide over the rooftops
cam2 = af.add_camera("cam2", (14.0, -26.0, 14.0), (-4.0, 30.0, 0.0), lens=28)
af.render_still(os.path.join(out, f"hyd_{time}_wide.png"))
af.save(os.path.join(out, f"hyd_{time}.blend"))
print("AF: done")
