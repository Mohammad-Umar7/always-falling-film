# Sequence B helpers: 1975 rooftop night with father + boy on the charpai
import bpy, math, random
from mathutils import Vector
import af, sets_hyd, poses

CHARPAI = Vector((0.4, 0.6, 0.06))


def night_roof(year=1975, moon_dir=(0.25, 0.55, 0.8), cast=("FATHER_75_HOME", "BOY_75"), lying=True, clouds=True, seed=7, moon_size=21.0):
    H = sets_hyd.Hyd(time="night", seed=seed, year=year)
    H.build(dressing=False)
    H.sky_dressing(moon_dir=moon_dir, clouds=clouds, moon_size=moon_size)
    # key light comes from the moon
    key = bpy.data.objects.get("key")
    if key:
        key.rotation_euler = (-Vector(moon_dir)).to_track_quat("-Z", "Y").to_euler()
    H.charpai("hero_charpai", CHARPAI, math.radians(90))
    rigs = poses.load_chars(list(cast), palette=poses.NIGHT_CAST)
    if lying:
        fa = rigs.get("FATHER_75_HOME")
        boy = rigs.get("BOY_75")
        if fa:
            lie(fa, CHARPAI.x - 0.2, 1.42, 0.655)
        if boy:
            lie(boy, CHARPAI.x + 0.24, 0.72, 0.60)
    return H, rigs


def lie(rig, x, y, z):
    rig.rotation_mode = "XYZ"
    rig.rotation_euler = (math.radians(-90), 0, math.radians(180))
    rig.location = (x, y, z)


def ik_arm(rig, side, target_loc, pole=None, chain=4):
    """IK on lowerarm02.<side> to an empty; returns the empty (animate its location)."""
    e = bpy.data.objects.new(f"{rig.name}_ik_{side}", None)
    af.link(e)
    e.location = target_loc
    pb = rig.pose.bones[f"lowerarm02.{side}"]
    c = pb.constraints.new("IK")
    c.target = e
    c.chain_count = chain
    c.use_tail = True
    if pole is not None:
        p = bpy.data.objects.new(f"{rig.name}_pole_{side}", None)
        af.link(p)
        p.location = pole
        c.pole_target = p
        c.pole_angle = math.radians(-90)
    return e


def newton_cannon(center, facing, R=42.0, n_traj=(0.55, 0.72, 0.86, 1.0), color="#FFE7B0", width=0.55, f0=1, fpd=None):
    """Draw Newton's cannon in the sky: Earth circle, mountain, trajectories (true inverse-square gravity).
    center: sky point; facing: vector from the diagram toward the camera. fpd: dict of draw timings."""
    fpd = fpd or {}
    # local 2D frame on a plane facing the camera
    nrm = Vector(facing).normalized()
    up = Vector((0, 0, 1))
    u = up.cross(nrm).normalized()
    if u.length < 1e-4:
        u = Vector((1, 0, 0))
    v = nrm.cross(u).normalized()
    C = Vector(center)

    def P(x, y):
        return C + u * x + v * y

    mat, nt = af.new_mat("newton_glow")
    em = af.N(nt, "ShaderNodeEmission")
    af.I(em, "Color").default_value = af.hexc(color)
    af.I(em, "Strength").default_value = 4.0
    out = af.N(nt, "ShaderNodeOutputMaterial")
    af.L(nt, af.O(em, "Emission"), af.I(out, "Surface"))
    curves = []

    def make_curve(name, pts, t0, t1):
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = width
        cu.bevel_resolution = 2
        cu.use_fill_caps = True
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (p.x, p.y, p.z, 1)
        cu.bevel_factor_mapping_end = "SPLINE"
        cu.materials.append(mat)
        ob = af.link(bpy.data.objects.new(name, cu))
        cu.bevel_factor_end = 0.0
        cu.keyframe_insert("bevel_factor_end", frame=t0)
        cu.bevel_factor_end = 1.0
        cu.keyframe_insert("bevel_factor_end", frame=t1)
        if cu.animation_data and cu.animation_data.action:
            for fc in af._fcurves(cu.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "SINE"
                    kp.easing = "EASE_IN_OUT"
        curves.append(ob)
        return ob

    # earth circle
    circ = [P(R * math.cos(a), R * math.sin(a)) for a in [i / 96 * 2 * math.pi + math.pi / 2 for i in range(97)]]
    make_curve("newton_earth", circ, f0, f0 + fpd.get("earth", 30))
    # mountain
    mh = R * 0.22
    mt = [P(-R * 0.12, R * 0.99), P(0, R + mh), P(R * 0.12, R * 0.99)]
    t = f0 + fpd.get("earth", 30)
    make_curve("newton_mountain", mt, t, t + 10)
    t += 12
    # trajectories under inverse-square gravity, launched horizontally from the summit
    r0 = R + mh
    GM = 1.0
    vc = math.sqrt(GM / r0)
    for k, fac in enumerate(n_traj):
        x, y = 0.0, r0
        vx, vy = vc * fac, 0.0
        pts = [P(x, y)]
        dt = 0.02 * r0 / vc / 40
        ang = 0.0
        for step in range(20000):
            r = math.hypot(x, y)
            ax, ay = -GM * x / r ** 3, -GM * y / r ** 3
            vx += ax * dt
            vy += ay * dt
            x += vx * dt
            y += vy * dt
            if step % 20 == 0:
                pts.append(P(x, y))
            if math.hypot(x, y) <= R:
                pts.append(P(x, y))
                break
            ang = math.atan2(x, y) % (2 * math.pi)
            if fac >= 0.999 and step > 200 and abs(ang) < 0.01:
                pts.append(P(0, r0))
                break
        dur = fpd.get("traj", [16, 22, 28, 48])[k]
        make_curve(f"newton_traj{k}", pts, t, t + dur)
        t += int(dur * 0.65)
    # ball (glowing dot) riding the final orbit
    return curves, mat, em, t


def stars_fade(em_node, f_on, f_off, strength=4.0):
    s = af.I(em_node, "Strength")
    s.default_value = strength
    s.keyframe_insert("default_value", frame=f_on)
    s.default_value = 0.0
    s.keyframe_insert("default_value", frame=f_off)
