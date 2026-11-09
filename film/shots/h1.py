# H1 (3:10–3:35, 600f): 92,000 ORBITS — the camera pulls back from the silent satellite until the whole Earth is
# wrapped in a cocoon of gold and blue orbit trails (precessing, slowly decaying). Counter + years added in post.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector, Matrix
import af, shot, scene_space as ss, sets_space as sp, orbits

S = shot.Shot("H1", frames=600)
sp.CLOUD.update(scale=6.5, cover=0.55, white="#D6DEF6")
o = ss.setup(sun_dir=(0.9, -0.3, 0.3), latlon=(20.0, 68.0), lights=0.7)
for led in o["leds"]:
    em = [n for n in led.data.materials[0].node_tree.nodes if n.bl_idname == "ShaderNodeEmission"][0]
    af.I(em, "Strength").default_value = 0.0
earth = o["earth"][0]
ec = earth.location.copy()
base = earth.rotation_euler.to_matrix().to_4x4()
R0 = sp.EARTH_R + sp.ALT
rings = orbits.ring_mesh("orbits", 700, R0, sp.EARTH_R * 1.02, incl_deg=50.7, seg=180, width=6.0, base=base)
orbits.trail_circle("first_orbit", ec, R0, (0, 0, 1), (0, -1, 0), 1, 220, depth=0.22)
rings.location = ec
rings.data.materials.append(orbits.ring_material(strength=0.55))
orbits.reveal_modifier(rings, [(1, 0), (150, 0), (220, 4), (290, 40), (370, 200), (450, 480), (530, 700), (600, 700)])
for k in ("location",):
    pass
# satellite tumbles gently at the start
ss.spin(o["sat"], 1, 600, (0.3, 0.2, 0.4), start=(0.2, -0.1, 0.4))
S.cam("cam", keys=[(1, (3.0, -4.0, 1.1), (0.0, 0.0, 0.0), 32.0),
                   (90, (9.0, -15.0, 4.0), (0.0, 0.0, 0.0), 32.0),
                   (210, (420.0, -1500.0, 700.0), (0.0, 0.0, -1400.0), 32.0),
                   (600, (2400.0, -12500.0, 4800.0), (0.0, 0.0, -3280.0), 34.0)])
cam = bpy.context.scene.camera
cam.data.clip_end = 60000.0
S.finish(step=1, bloom=(0.7, 0.9, 0.7))
