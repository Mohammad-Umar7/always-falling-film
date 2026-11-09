# C4 (1:12–1:20, 192f): night pass over India — city lights below, dawn glow on the limb, satellite blinking; telemetry begins.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_space as ss

S = shot.Shot("C4", frames=192)
o = ss.setup(sun_dir=(0.05, 0.9, -0.44), latlon=(17.4, 72.5), lights=1.0, sun_visible=False, sun_energy=0.6)
ss.spin(o["sat"], 1, 192, (0.0, 0.0, 1.0), start=(math.radians(8), math.radians(-6), 0.4))
ss.blink(o["leds"], ["110110", "100100", "111000"], 1, 192, step=4)
# satellite glides; camera tracks slightly behind/above, Earth's night side below
S.cam("cam", keys=[(1, (-3.4, -4.6, 1.5), (0.4, 3.0, -1.2), 30.0),
                   (192, (-2.9, -4.0, 1.25), (0.6, 3.6, -1.4), 32.0)])
for k, ob in enumerate([o["sat"]]):
    ob.location = (0, 0, 0)
    ob.keyframe_insert("location", frame=1)
    ob.location = (0.6, 1.2, -0.05)
    ob.keyframe_insert("location", frame=192)
S.finish(step=1, bloom=(0.6, 1.0, 0.7), streaks=(2.0, 0.3, 6))
