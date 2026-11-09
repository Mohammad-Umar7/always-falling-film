# D2 (1:30–1:40, 240f): silent — the dead satellite tumbles slowly toward the Earth's limb as an orbital sunrise breaks.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_space as ss

S = shot.Shot("D2", frames=240)
o = ss.setup(sun_dir=(0.0, 0.918, -0.396), latlon=(12.0, 76.0), lights=0.8, sun_energy=2.5)
for led in o["leds"]:
    m = led.data.materials[0]
    em = [n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeEmission"][0]
    af.I(em, "Strength").default_value = 0.0
# slow tumble (no longer controlled)
ss.spin(o["sat"], 1, 240, (0.35, 0.22, 0.5), start=(math.radians(14), math.radians(-10), 0.3))
o["sat"].location = (0, 0, 0)
o["sat"].keyframe_insert("location", frame=1)
o["sat"].location = (0.0, 6.0, -0.4)
o["sat"].keyframe_insert("location", frame=240)
S.cam("cam", keys=[(1, (-1.4, -7.5, 0.5), (0.0, 30.0, -9.5), 30.0),
                   (240, (-1.2, -6.8, 0.45), (0.0, 30.0, -10.5), 30.0)])
S.finish(step=1, bloom=(0.7, 1.2, 0.8), streaks=(2.0, 0.5, 8))
