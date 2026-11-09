# Re-entry FX: plasma sheath, sparks, tearing panels, streak
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler
import af


def additive_mat(name, col_front="#FFFFFF", col_back="#FF5A2A", strength=6.0, along="Y", fade=(0.0, 1.0), alpha_scale=1.0, rim_in=(0.35, 1.0)):
    """Emission+transparent (additive). Colour/alpha ramp along object-space axis (front=-1 .. back=+1)."""
    m, nt = af.new_mat(name)
    tc = af.N(nt, "ShaderNodeTexCoord")
    sep = af.N(nt, "ShaderNodeSeparateXYZ")
    af.L(nt, af.O(tc, "Object"), sep.inputs[0])
    t = af.maprange(nt, af.O(sep, along), -1.0, 1.0, 0.0, 1.0)
    cr = af.ramp(nt, [(0.0, col_front), (0.35, "#FFD27A"), (0.7, col_back), (1.0, "#8A1E6A")], "LINEAR", fac=t)
    lw = af.N(nt, "ShaderNodeLayerWeight")
    af.I(lw, "Blend").default_value = 0.3
    rim = af.maprange(nt, af.O(lw, "Facing"), rim_in[0], rim_in[1], 0.0, 1.0, interp="SMOOTHSTEP")
    fall = af.maprange(nt, t, fade[0], fade[1], 1.0, 0.0)
    a = af.math_(nt, "MULTIPLY", rim, fall)
    a = af.math_(nt, "MULTIPLY", a, alpha_scale)
    em = af.N(nt, "ShaderNodeEmission")
    af.L(nt, af.O(cr, "Color"), af.I(em, "Color"))
    s = af.math_(nt, "MULTIPLY", a, strength)
    af.L(nt, s, af.I(em, "Strength"))
    tr = af.N(nt, "ShaderNodeBsdfTransparent")
    add = af.N(nt, "ShaderNodeAddShader")
    af.L(nt, af.O(tr, "BSDF"), add.inputs[0])
    af.L(nt, af.O(em, "Emission"), add.inputs[1])
    out = af.N(nt, "ShaderNodeOutputMaterial")
    af.L(nt, add.outputs[0], af.I(out, "Surface"))
    m.surface_render_method = "BLENDED"
    m.use_backface_culling = False
    return m, em


def sheath(name, length=4.0, radius=1.1, layers=3, flow=(0, 1, 0)):
    """Teardrop plasma shells around the satellite, tail pointing along `flow` (+Y by default)."""
    shells = []
    for k in range(layers):
        me = bpy.data.meshes.new(f"{name}{k}")
        bm_ = bmesh.new()
        bmesh.ops.create_uvsphere(bm_, u_segments=48, v_segments=24, radius=1.0)
        for v in bm_.verts:
            y = v.co.y
            if y > 0:
                v.co.y = y * (length * (1 + 0.35 * k)) / radius
                sh = 1.0 - 0.75 * min(1.0, v.co.y / (length * (1 + 0.35 * k) / radius))
                v.co.x *= sh
                v.co.z *= sh
        for f in bm_.faces:
            f.smooth = True
        bm_.to_mesh(me)
        bm_.free()
        ob = af.link(bpy.data.objects.new(f"{name}{k}", me))
        ob.scale = (radius * (1 + 0.25 * k),) * 3
        m, em = additive_mat(f"{name}_m{k}", strength=[3.2, 2.0, 1.2][k % 3], fade=(0.05, 1.0), alpha_scale=[0.9, 0.6, 0.45][k % 3])
        me.materials.append(m)
        # turbulent wobble
        tex = bpy.data.textures.new(f"{name}_tex{k}", "CLOUDS")
        tex.noise_scale = 0.6
        dp = ob.modifiers.new("turb", "DISPLACE")
        dp.texture = tex
        dp.strength = 0.18 + 0.1 * k
        dp.texture_coords = "OBJECT"
        drv = bpy.data.objects.new(f"{name}_texcoord{k}", None)
        af.link(drv)
        dp.texture_coords_object = drv
        drv.location = (0, 0, 0)
        drv.keyframe_insert("location", frame=1)
        drv.location = (0, -60.0 * (1 + k * 0.4), 0)
        drv.keyframe_insert("location", frame=360)
        af.set_interp(drv, "LINEAR")
        shells.append((ob, em))
    return shells


def ramp_strength(em_node, keys):
    s = af.I(em_node, "Strength") if em_node.inputs["Strength"].is_linked is False else None
    return s


def scale_keys(ob, keys, interp="BEZIER"):
    for f, sc in keys:
        ob.scale = sc if isinstance(sc, (tuple, list)) else (sc, sc, sc)
        ob.keyframe_insert("scale", frame=f)
    af.set_interp(ob, interp)


def sparks(name, n, f0, f1, origin=(0, 0, 0), flow=(0, 1, 0), spread=1.2, speed=(1.5, 4.0), seed=1, col="#FFD27A"):
    """Glowing streak sparks peeling back from the satellite, re-spawning (keyframed, linear)."""
    rnd = random.Random(seed)
    m = af.flat_mat(name + "_m", col, strength=10.0)
    fl = Vector(flow).normalized()
    obs = []
    for i in range(n):
        s = af.uv_sphere(f"{name}{i}", 0.03, origin, m, 8, 4)
        s.scale = (0.6, 4.0, 0.6)
        life = rnd.randint(6, 14)
        f = f0 + rnd.randint(0, life)
        while f < f1:
            st = Vector(origin) + Vector((rnd.uniform(-spread, spread), rnd.uniform(-0.3, 0.5), rnd.uniform(-spread, spread)))
            en = st + fl * rnd.uniform(*speed) * life * 0.5 + Vector((rnd.uniform(-0.5, 0.5), 0, rnd.uniform(-0.5, 0.5)))
            s.location = st
            s.keyframe_insert("location", frame=f)
            s.location = en
            s.keyframe_insert("location", frame=f + life - 1)
            f += life
        for fc in af.fcurves_of(s):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
        obs.append(s)
    return obs


def tear_panel(name, src_body, face_index, f_break, flow=(0, 1, 0), seed=1, spin=(8.0, 5.0, 3.0), dist=14.0, f_end=360):
    """Duplicate one face of the satellite body as a plate; at f_break it rips away backward, tumbling."""
    rnd = random.Random(seed)
    me = src_body.data
    poly = me.polygons[face_index]
    verts = [src_body.matrix_world @ me.vertices[i].co for i in poly.vertices]
    c = sum(verts, Vector()) / len(verts)
    local = [v - c for v in verts]
    pm = bpy.data.meshes.new(name)
    pm.from_pydata([tuple(v) for v in local], [], [tuple(range(len(local)))])
    ob = af.link(bpy.data.objects.new(name, pm))
    ob.location = c
    for mt in me.materials:
        pm.materials.append(mt)
    so = ob.modifiers.new("t", "SOLIDIFY")
    so.thickness = 0.02
    ob.keyframe_insert("location", frame=f_break)
    ob.keyframe_insert("rotation_euler", frame=f_break)
    fl = Vector(flow).normalized()
    side = (c - Vector((0, 0, 0))).normalized()
    ob.location = c + fl * dist + side * rnd.uniform(1.0, 3.0)
    ob.rotation_euler = (math.radians(spin[0] * 60) * rnd.uniform(0.5, 1), math.radians(spin[1] * 60) * rnd.uniform(0.5, 1), math.radians(spin[2] * 60))
    ob.keyframe_insert("location", frame=min(f_end, f_break + 30))
    ob.keyframe_insert("rotation_euler", frame=min(f_end, f_break + 30))
    for fc in af.fcurves_of(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = "QUAD"
            kp.easing = "EASE_IN"
    return ob


def streak(name, pts, f0, f1, depth=(1.6, 0.05), color_head="#FFFFFF", color_tail="#FF6A2A", strength=8.0):
    """Long glowing trail along pts, drawn over time; the head is a glowing ball riding the front."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = depth[0]
    cu.bevel_resolution = 3
    sp_ = cu.splines.new("POLY")
    sp_.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp_.points[i].co = (p.x, p.y, p.z, 1)
        t = i / (len(pts) - 1)
        sp_.points[i].radius = 0.15 + 0.85 * t
    m, nt = af.new_mat(name + "_m")
    em = af.N(nt, "ShaderNodeEmission")
    af.I(em, "Color").default_value = af.hexc(color_tail)
    af.I(em, "Strength").default_value = strength
    out = af.N(nt, "ShaderNodeOutputMaterial")
    af.L(nt, af.O(em, "Emission"), af.I(out, "Surface"))
    cu.materials.append(m)
    ob = af.link(bpy.data.objects.new(name, cu))
    cu.bevel_factor_mapping_end = "SPLINE"
    cu.bevel_factor_end = 0.0
    cu.keyframe_insert("bevel_factor_end", frame=f0)
    cu.bevel_factor_end = 1.0
    cu.keyframe_insert("bevel_factor_end", frame=f1)
    hm = af.flat_mat(name + "_head", color_head, strength=strength * 3)
    head = af.uv_sphere(name + "_ball", depth[0] * 2.2, pts[0], hm, 16, 8)
    for f in range(f0, f1 + 1, 2):
        t = (f - f0) / max(1, (f1 - f0))
        idx = min(len(pts) - 1, int(t * (len(pts) - 1)))
        head.location = pts[idx]
        head.keyframe_insert("location", frame=f)
    return ob, head
