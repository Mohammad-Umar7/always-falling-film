# I2c (3:53–3:58, 120f): from high orbit — a burning streak tears across the atmosphere toward India's night side,
# breaking into fragments.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_space as ss, sets_space as sp, reentry as rx

S = shot.Shot("I2c", frames=120)
o = ss.setup(sun_dir=(0.1, 0.9, -0.5), latlon=(14.0, 78.0), lights=1.0, sun_visible=False, sun_energy=0.4, sat=False)
ec = Vector((0, 0, -(sp.EARTH_R + sp.ALT)))
R = sp.EARTH_R
# descending path: from ~70 m altitude to the surface over ~1100 m of arc
pts = []
for i in range(120):
    t = i / 119
    ang = math.radians(-12 + 20 * t)
    alt = 70 * (1 - t) ** 1.6 + 2
    p = ec + Vector((math.sin(ang) * 0.3, math.sin(ang), math.cos(ang))) .normalized() * (R + alt)
    pts.append(p)
main, head = rx.streak("streak", pts, 1, 110, depth=(5.0, 0.2), strength=9.0)
for k, off in enumerate([(-0.02, 0.6), (0.025, 0.4), (0.0, 0.25)]):
    sub = []
    for i in range(70, 120):
        t = (i - 70) / 49
        q = pts[i] + Vector((off[0] * 800 * t, 0, -off[1] * 40 * t))
        sub.append(q)
    rx.streak(f"frag{k}", sub, 72 + k * 4, 118, depth=(2.2, 0.1), strength=6.0)
S.cam("cam", keys=[(1, (-900.0, -1800.0, 900.0), (0.0, 300.0, -400.0), 30.0), (120, (-880.0, -1700.0, 860.0), (0.0, 350.0, -420.0), 31.0)])
S.finish(step=1, bloom=(0.55, 1.4, 0.9), streaks=(2.2, 0.3, 6))
