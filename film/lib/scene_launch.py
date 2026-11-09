# Launch day at Kapustin Yar (19 April 1975, daylight): steppe, pad, Kosmos-3M, anime smoke and flame
import bpy, math, random
from mathutils import Vector
import af, sets_space as sp


def setup(sun_dir=(0.55, -0.6, 0.58)):
    sc = bpy.context.scene
    sc.eevee.use_raytracing = False
    af.sky_world([(-1.0, "#7FA4C8"), (0.0, "#DCEBFA"), (0.06, "#A9CDF2"), (0.3, "#5F9BE0"), (1.0, "#2A62C4")],
                 ambient="#9AB4D8", ambient_strength=0.8, stars=None)
    sd = Vector(sun_dir).normalized()
    af.add_sun("sun", -sd, "#FFF4E2", energy=3.6, angle=0.8)
    ground = af.toon_mat("steppe", "#C2B47E", shadow="#7E7A86", light="#E4D8A4", band=0.3, light_band=0.8)
    af.plane("ground", 9000, 9000, (0, 0, 0), mat=ground)
    hills = af.flat_mat("hills", "#9DB4CC")
    af.treeline("hills_far", -3000, 3000, 2600, 0, 60, 30, seed=4, mat=hills, palms=0.0, step=40)
    hills2 = af.flat_mat("hills2", "#AFC2D4")
    af.treeline("hills_far2", -3000, 3000, -2600, 0, 50, 25, seed=7, mat=hills2, palms=0.0, step=40)
    cm = af.toon_mat("cloud_day", "#F4F6FC", shadow="#AEB8D8", light="#FFFFFF", band=0.3, light_band=0.8, rim="#FFFFFF")
    rnd = random.Random(2)
    for i in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(900, 1800)
        cl = af.cumulus(f"dcloud{i}", (math.cos(a) * d, math.sin(a) * d, rnd.uniform(220, 380)),
                        size=(rnd.uniform(160, 300), rnd.uniform(80, 120), rnd.uniform(60, 100)), puffs=28, seed=i, mat=cm)
        cl.rotation_euler = (0, 0, a + math.pi / 2)
    pad = sp.launch_pad((0, 0, 0))
    rocket = sp.kosmos3m((0, 0, 0.6))
    return rocket


def smoke_mats():
    white = af.toon_mat("smoke_white", "#ECEAE6", shadow="#A2A2B8", light="#FFFFFF", band=0.32, light_band=0.78)
    warm = af.toon_mat("smoke_warm", "#F2C49A", shadow="#B0708A", light="#FFE8C8", band=0.32, light_band=0.78)
    return white, warm


def plume(rocket, f_ignite, f_full, name="plume", length=16.0):
    objs = sp.flame(name, (0, 0, 0.4), length=length, radius=1.5)
    root = bpy.data.objects.new(name + "_root", None)
    af.link(root)
    root.parent = rocket
    for o in objs:
        o.parent = root
    root.scale = (0.01, 0.01, 0.01)
    root.keyframe_insert("scale", frame=f_ignite - 1)
    root.scale = (1.0, 1.0, 0.6)
    root.keyframe_insert("scale", frame=f_ignite + 2)
    root.scale = (1.0, 1.0, 1.0)
    root.keyframe_insert("scale", frame=f_full)
    # flicker
    for a in range(3):
        add = af.add_noise_mod(root, "scale", a, strength=0.12 if a == 2 else 0.06, scale=1.5, phase=a * 10)
    gm = af.flat_mat(name + "_glow", "#FFF2B0", strength=18.0)
    g = af.uv_sphere(name + "_glowball", 1.0, (0, 0, 0.5), gm, 24, 12)
    g.parent = rocket
    g.scale = (0.001, 0.001, 0.001)
    g.keyframe_insert("scale", frame=f_ignite - 1)
    g.scale = (2.4, 2.4, 1.1)
    g.keyframe_insert("scale", frame=f_ignite + 1)
    g.scale = (1.8, 1.8, 0.8)
    g.keyframe_insert("scale", frame=f_full)
    af.add_noise_mod(g, "scale", 0, 0.15, 1.2)
    af.add_noise_mod(g, "scale", 1, 0.15, 1.2, 7)
    li = af.add_point(name + "_light", (0, 0, -3), "#FF9A3A", energy=0.0, radius=2.0, shadow=False)
    li.parent = rocket
    li.data.energy = 0.0
    li.data.keyframe_insert("energy", frame=f_ignite - 1)
    li.data.energy = 4.0e5
    li.data.keyframe_insert("energy", frame=f_ignite + 1)
    return root


def trail(name, top_z_keys, mat, radius=(1.4, 9.0)):
    """Smoke trail tube from the ground up to the rocket; top follows keys [(frame, z)]."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.0
    cu.bevel_resolution = 4
    sp_ = cu.splines.new("POLY")
    n = 40
    sp_.points.add(n - 1)
    zmax = max(z for _, z in top_z_keys)
    for i in range(n):
        t = i / (n - 1)
        z = t * zmax
        sp_.points[i].co = (math.sin(t * 7) * 3.0 * t, math.cos(t * 5) * 2.0 * t, z, 1)
        sp_.points[i].radius = radius[1] * (1 - t) ** 1.2 + radius[0]
    cu.materials.append(mat)
    ob = af.link(bpy.data.objects.new(name, cu))
    cu.bevel_factor_mapping_end = "SPLINE"
    for f, z in top_z_keys:
        cu.bevel_factor_end = max(0.0, min(1.0, z / zmax))
        cu.keyframe_insert("bevel_factor_end", frame=f)
    return ob


def trail_puffs(name, z0, z1, f0, f1, mat, step=5.0, r=(2.0, 7.0), seed=3):
    """Cel smoke puffs left behind the climbing rocket: puff at height z appears when the rocket passes it."""
    rnd = random.Random(seed)
    z = z0
    out = []
    while z < z1:
        t = (z - z0) / (z1 - z0)
        f = int(f0 + t * (f1 - f0))
        p = af.ico(f"{name}{len(out)}", 1.0, (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), z), mat, sub=3)
        p.scale = (0.0001, 0.0001, 0.0001)
        p.keyframe_insert("scale", frame=max(1, f - 1))
        rr = r[0] + (r[1] - r[0]) * (1 - t) * rnd.uniform(0.7, 1.0)
        p.scale = (rr * 0.6, rr * 0.6, rr * 0.8)
        p.keyframe_insert("scale", frame=f + 4)
        p.scale = (rr, rr, rr * 1.2)
        p.keyframe_insert("scale", frame=f + 40)
        for fc in af.fcurves_of(p):
            for kp in fc.keyframe_points:
                kp.interpolation = "EXPO"
                kp.easing = "EASE_OUT"
        out.append(p)
        z += step * rnd.uniform(0.7, 1.2)
    return out
