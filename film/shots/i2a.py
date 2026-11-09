# I2a (3:43–3:48, 120f): Feb 1992, orbit decayed — skimming the upper atmosphere over India's night side,
# the air begins to glow around the dead satellite; sparks start peeling back; shake builds.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_space as ss, reentry as rx

S = shot.Shot("I2a", frames=120)
o = ss.setup(sun_dir=(0.1, 0.9, -0.45), latlon=(16.0, 79.0), lights=1.0, sun_visible=False, sun_energy=0.5, alt=55.0,
             rim=((0.0, -0.4, -0.9), "#FF8A4A", 0.0))
for led in o["leds"]:
    em = [n for n in led.data.materials[0].node_tree.nodes if n.bl_idname == "ShaderNodeEmission"][0]
    af.I(em, "Strength").default_value = 0.0
sat = o["sat"]
ss.spin(sat, 1, 120, (0.6, 0.3, 0.8), start=(0.3, -0.2, 0.5))
shells = rx.sheath("plasma", length=3.2, radius=1.0, layers=3)
for k, (ob, em) in enumerate(shells):
    rx.scale_keys(ob, [(1, 0.001), (35, 0.25 + 0.05 * k), (80, 0.6 + 0.1 * k), (120, 0.95 + 0.1 * k)])
glow = af.add_point("plasma_light", (0, -0.8, 0), "#FF9A4A", energy=0.0, radius=0.6, shadow=False)
glow.data.keyframe_insert("energy", frame=30)
glow.data.energy = 900.0
glow.data.keyframe_insert("energy", frame=120)
rx.sparks("spk", 60, 50, 120, flow=(0, 1, 0), spread=0.9, speed=(1.0, 3.0), seed=2)
cam = S.cam("cam", keys=[(1, (4.4, -4.0, 1.1), (0.0, 0.9, -0.1), 30.0), (120, (3.8, -3.4, 0.95), (0.0, 1.1, -0.1), 30.0)])
S.shake(cam, 40, 120, strength=0.01, scale=1.2)
S.finish(step=1, bloom=(0.8, 1.0, 0.7))
