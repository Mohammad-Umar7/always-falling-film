# I2b (3:48–3:53, 120f): SAKUGA — full plasma; antennas snap away; solar panels tear off and tumble back
# (motion-blur smears); the body becomes a fireball. Impact frames + speed lines added in post.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_space as ss, reentry as rx

S = shot.Shot("I2b_side", frames=120)
o = ss.setup(sun_dir=(0.1, 0.9, -0.45), latlon=(16.5, 78.5), lights=1.0, sun_visible=False, sun_energy=0.5, alt=40.0)
for led in o["leds"]:
    em = [n for n in led.data.materials[0].node_tree.nodes if n.bl_idname == "ShaderNodeEmission"][0]
    af.I(em, "Strength").default_value = 0.0
sat, body = o["sat"], o["body"]
ss.spin(sat, 1, 120, (1.4, 0.8, 1.8), start=(0.5, -0.3, 0.9))
bpy.context.view_layer.update()
shells = rx.sheath("plasma", length=4.5, radius=1.15, layers=3)
for k, (ob, em) in enumerate(shells):
    rx.scale_keys(ob, [(1, 1.0 + 0.1 * k), (60, 1.25 + 0.12 * k), (100, 1.7 + 0.15 * k), (120, 2.1 + 0.2 * k)])
# antennas snap off early
for k, ch in enumerate([c for c in sat.children if c.name.startswith("aryabhata_ant")]):
    mw = ch.matrix_world.copy()
    ch.parent = None
    ch.matrix_world = mw
    ch.keyframe_insert("location", frame=10 + 4 * k)
    ch.keyframe_insert("rotation_euler", frame=10 + 4 * k)
    ch.location = ch.location + Vector((0, 12.0 + 3 * k, (-1) ** k * 1.5))
    ch.rotation_euler = (ch.rotation_euler.x + 6.0, ch.rotation_euler.y + 3.0, ch.rotation_euler.z)
    ch.keyframe_insert("location", frame=34 + 4 * k)
    ch.keyframe_insert("rotation_euler", frame=34 + 4 * k)
# panels tear away
idxs = [i for i, p in enumerate(body.data.polygons) if abs(p.normal.z) < 0.9][:8]
for j, fi in enumerate(idxs):
    rx.tear_panel(f"panel{j}", body, fi, 24 + j * 9, seed=j, dist=16.0, f_end=120)
# the body melts into a fireball
fb, fe = rx.additive_mat("fireball_m", col_front="#FFFFFF", col_back="#FFB04A", strength=4.0, fade=(0.0, 1.4), rim_in=(0.15, 1.0))
ball = af.uv_sphere("fireball", 1.0, (0, 0, 0), fb, 32, 16)
rx.scale_keys(ball, [(1, 0.001), (70, 0.5), (100, 1.3), (120, 1.8)])
rx.scale_keys(body, [(1, 1.0), (80, 0.85), (110, 0.25), (120, 0.01)])
glow = af.add_point("plasma_light", (0, -0.8, 0), "#FFB06A", energy=1200.0, radius=0.6, shadow=False)
rx.sparks("spk", 160, 1, 120, flow=(0, 1, 0), spread=1.4, speed=(2.0, 6.0), seed=5)
cam = S.cam("cam", keys=[(1, (5.6, -1.4, 1.5), (0.0, 1.8, -0.3), 28.0), (60, (5.0, -1.0, 1.3), (0.0, 2.0, -0.3), 26.0),
                         (120, (6.4, -2.0, 1.9), (0.0, 2.2, -0.3), 28.0)])
S.shake(cam, 1, 120, strength=0.03, scale=0.9)
sc = bpy.context.scene
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 1.5
S.finish(step=1, bloom=(0.8, 1.1, 0.8))
