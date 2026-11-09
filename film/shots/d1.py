# D1 (1:20–1:30, 240f): tight on Aryabhata over the sunlit Earth, status lights blinking with the telemetry —
# at frame 181 everything dies mid-word.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_space as ss

S = shot.Shot("D1", frames=240)
o = ss.setup(sun_dir=(0.8, -0.35, 0.45), latlon=(22.0, 64.0), lights=0.6)
ss.spin(o["sat"], 1, 240, (0.0, 0.0, 1.1), start=(math.radians(10), math.radians(-8), 0.0))
ss.blink(o["leds"], ["110110", "101010", "111000"], 1, 240, step=3, die_at=181)
S.cam("cam", keys=[(1, (2.1, -2.6, 0.75), (0.0, 0.0, 0.05), 38.0),
                   (180, (1.75, -2.2, 0.68), (0.0, 0.0, 0.05), 40.0),
                   (181, (1.75, -2.2, 0.68), (0.0, 0.0, 0.05), 40.0),
                   (240, (1.95, -2.45, 0.72), (0.0, 0.0, 0.05), 40.0)])
S.finish(step=1, bloom=(0.75, 1.0, 0.7), streaks=(2.0, 0.35, 6))
