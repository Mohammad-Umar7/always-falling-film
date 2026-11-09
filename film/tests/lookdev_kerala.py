import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import importlib, af
importlib.reload(af)
from af import *
import bpy
from mathutils import Vector

clear_scene()
sc = setup_scene(samples=16)

# ---- sky: Kerala night
sky_world([(-1.0, "#0B2236"), (-0.02, "#1B5672"), (0.06, "#1E4E73"), (0.2, "#14335E"),
           (0.45, "#0C1D45"), (1.0, "#050A22")],
          ambient="#1A2A55", ambient_strength=0.6,
          stars=dict(density=0.05, size=0.06, scale=260, bright=3.0, color="#E4ECFF"),
          milky=dict(axis=(0.35, 0.75, 0.55), width=0.2, bright=0.25, color="#8EA2E6"),
          horizon_fade=(0.02, 0.22))

# ---- moonlight
add_sun("Moon_key", (-0.55, 0.6, -0.45), "#A9C8FF", energy=2.2, angle=1.0)

# ---- materials
concrete = toon_mat("concrete", "#43557A", shadow="#1F2945", light="#7C93BF", band=0.3, light_band=0.72, rim="#B9D0FF", rim_th=0.6)
wall_m = toon_mat("wall", "#4F6390", shadow="#232E50", light="#8FA6D6", band=0.3, light_band=0.75)
palm_dark = toon_mat("palm_frond", "#0E2A33", shadow="#061219", light="#1E4B52", band=0.35, light_band=0.85, rim="#5E8FB0", rim_th=0.7)
trunk_m = toon_mat("palm_trunk", "#1B2A3A", shadow="#0A121C", light="#33475F", band=0.35)
tl_far = flat_mat("treeline_far", "#13344E")
tl_mid = flat_mat("treeline_mid", "#0B2236")
fig_m = flat_mat("figure", "#04080F")
win_m = flat_mat("window_warm", "#FFB35C", strength=3.0)

# ---- terrace
box("slab", (10, 8, 0.25), (0, 0, -0.125), concrete)
for i, (sz, lc) in enumerate([((10, 0.2, 0.95), (0, 3.9, 0.475)), ((10, 0.2, 0.95), (0, -3.9, 0.475)),
                               ((0.2, 8, 0.95), (4.9, 0, 0.475)), ((0.2, 8, 0.95), (-4.9, 0, 0.475))]):
    p = box(f"parapet{i}", sz, lc, concrete)
    add_outline(p, 0.02, "#060B18")
house = box("house", (10, 8, 6), (0, 0, -3.25), wall_m)
stair = box("stair_room", (2.4, 2.4, 2.4), (-3.5, 2.6, 1.2), wall_m)
add_outline(stair, 0.025, "#060B18")

# ---- placeholder figure (son) standing at parapet looking up
body = cylinder("fig_body", 0.22, 1.2, (1.0, 3.2, 0.85), fig_m, 16)
head = uv_sphere("fig_head", 0.13, (1.0, 3.2, 1.62), fig_m, 16, 8)

# ---- palms
for i, (x, y, h, lx, ly) in enumerate([(-9, 9, 11, 0.12, -0.1), (8, 12, 12.5, -0.15, 0.05), (14, 6, 10, -0.2, 0.0),
                                       (-14, 14, 13, 0.18, 0.02), (3, 18, 14, 0.05, -0.05), (-4, 22, 12, -0.08, 0.0),
                                       (20, 20, 13, -0.12, 0.0)]):
    palm(f"palm{i}", (x, y, -6), h + 6, (lx, ly), 0.12, 15, 3.8, seed=i + 3, trunk_mat=trunk_m, frond_mat=palm_dark)

treeline("tl_far", -120, 120, 140, -6, 10, 4, seed=2, mat=tl_far, palms=1.2)
treeline("tl_mid", -90, 90, 70, -6, 8, 3, seed=5, mat=tl_mid, palms=1.6)

# distant windows
import random
rnd = random.Random(4)
for k in range(14):
    plane(f"win{k}", 0.6, 0.8, (rnd.uniform(-40, 40), 66, rnd.uniform(-3, 1)), (math.radians(90), 0, 0), win_m)

# ---- clouds near horizon
cm = cloud_mat("cloud_night", cols=("#16264A", "#2F4A7E", "#7F9DD6"), scale=1.3, coverage=0.5,
               light=(0.06, 0.12, 0), aspect=(5.0, 1.4), rim="#C8DAFF", seed=1.0)
cloud_card("cloudA", (-60, 400, 40), 260, 70, cm)
cm2 = cloud_mat("cloud_night2", cols=("#16264A", "#2F4A7E", "#7F9DD6"), scale=1.1, coverage=0.48,
                light=(0.06, 0.12, 0), aspect=(4.0, 1.2), rim="#C8DAFF", seed=4.0)
cloud_card("cloudB", (120, 420, 70), 220, 60, cm2)

# ---- moon (crescent) as emissive card
mm, nt = new_mat("moon")
tc = N(nt, "ShaderNodeTexCoord")
sep = N(nt, "ShaderNodeSeparateXYZ")
L(nt, O(tc, "Object"), sep.inputs[0])
r1 = math_(nt, "SQRT", math_(nt, "ADD", math_(nt, "POWER", O(sep, "X"), 2), math_(nt, "POWER", O(sep, "Y"), 2)))
dx = math_(nt, "SUBTRACT", O(sep, "X"), 0.38)
r2 = math_(nt, "SQRT", math_(nt, "ADD", math_(nt, "POWER", dx, 2), math_(nt, "POWER", math_(nt, "SUBTRACT", O(sep, "Y"), 0.12), 2)))
disc = maprange(nt, r1, 0.40, 0.415, 1, 0)
cut = maprange(nt, r2, 0.36, 0.375, 0, 1)
cres = math_(nt, "MULTIPLY", disc, cut)
glow = maprange(nt, r1, 0.4, 1.0, 0.35, 0.0, interp="SMOOTHSTEP")
a = math_(nt, "MAXIMUM", cres, glow)
colm = mixcol(nt, cres, "#7FA2E0", "#FFF4D6")
st = maprange(nt, cres, 0, 1, 1.0, 6.0)
finish_emission(mm, nt, colm, 1.0, a, blended=True)
nt_em = [n for n in nt.nodes if n.bl_idname == "ShaderNodeEmission"][0]
L(nt, st, I(nt_em, "Strength"))
moon = plane("moon", 2, 2, (-120, 380, 220), mat=mm)
moon.scale = (26, 26, 1)
moon.rotation_euler = billboard_rot((120, -380, -220))

cam = add_camera("cam", (2.6, -3.0, 1.35), (0.0, 30.0, 9.0), lens=28)
compositor(bloom=(0.8, 0.9, 0.6))

render_still(os.path.join(af.ROOT, "tests", "lookdev_kerala.png"), 1)
save(os.path.join(af.ROOT, "tests", "lookdev_kerala.blend"))
