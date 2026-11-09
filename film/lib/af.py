# ALWAYS FALLING — shared Blender helpers (Blender 5.1, EEVEE)
import bpy, bmesh, math, random, os
from mathutils import Vector, Euler, Matrix, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")


# ------------------------------------------------------------------ colour
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexc(h, a=1.0, mul=1.0):
    """sRGB hex -> linear RGBA tuple."""
    if isinstance(h, (tuple, list)):
        return tuple(h) if len(h) == 4 else (h[0], h[1], h[2], a)
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (_lin(r) * mul, _lin(g) * mul, _lin(b) * mul, a)


def mixc(c1, c2, t):
    a, b = hexc(c1), hexc(c2)
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))


# ------------------------------------------------------------------ scene
def clear_scene():
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                 bpy.data.lights, bpy.data.cameras, bpy.data.images, bpy.data.worlds,
                 bpy.data.actions, bpy.data.textures, bpy.data.armatures, bpy.data.metaballs):
        for item in list(coll):
            try:
                coll.remove(item)
            except Exception:
                pass
    for ng in list(bpy.data.node_groups):
        if ng.name.startswith("AF_"):
            bpy.data.node_groups.remove(ng)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


def setup_scene(w=1920, h=1080, fps=24, samples=24, f0=1, f1=1, transparent=False):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.fps = fps
    sc.frame_start, sc.frame_end = f0, f1
    sc.eevee.taa_render_samples = samples
    sc.eevee.use_shadows = True
    # cel look: no screen-space GI / raytraced indirect (their noise flickers across the toon ramp thresholds)
    for attr, val in (("use_raytracing", False), ("use_fast_gi", False)):
        if hasattr(sc.eevee, attr):
            setattr(sc.eevee, attr, val)
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    sc.render.film_transparent = transparent
    sc.render.use_motion_blur = False
    st = sc.render.image_settings
    st.file_format = "PNG"
    st.color_mode = "RGBA" if transparent else "RGB"
    st.color_depth = "8"
    st.compression = 15
    if sc.world is None:
        sc.world = bpy.data.worlds.new("World")
    return sc


def link(ob, coll=None):
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def look_at(ob, target, roll=0.0):
    d = Vector(target) - ob.location
    q = d.to_track_quat("-Z", "Y")
    ob.rotation_euler = q.to_euler()
    if roll:
        ob.rotation_euler.rotate(Euler((0, 0, 0)))
        ob.rotation_mode = "XYZ"
        m = ob.matrix_world.copy()
        ob.rotation_euler = (q @ Quaternion((0, 0, 1), roll)).to_euler()


def add_camera(name, loc, target, lens=35.0, sensor=36.0, clip=(0.1, 20000.0), roll=0.0, set_active=True):
    cam = bpy.data.cameras.new(name)
    cam.lens, cam.sensor_width = lens, sensor
    cam.clip_start, cam.clip_end = clip
    ob = link(bpy.data.objects.new(name, cam))
    ob.location = Vector(loc)
    look_at(ob, target, roll)
    if set_active:
        bpy.context.scene.camera = ob
    return ob


def add_sun(name, direction, color="#FFFFFF", energy=3.0, angle=0.5, shadow=True):
    """direction: vector the light travels along (e.g. (0.3,0.4,-1))."""
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy, ld.color, ld.angle = energy, hexc(color)[:3], math.radians(angle)
    ld.use_shadow = shadow
    ob = link(bpy.data.objects.new(name, ld))
    ob.rotation_euler = Vector(direction).to_track_quat("-Z", "Y").to_euler()
    return ob


def add_point(name, loc, color="#FFB35C", energy=200.0, radius=0.1, shadow=True):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy, ld.color, ld.shadow_soft_size = energy, hexc(color)[:3], radius
    ld.use_shadow = shadow
    ob = link(bpy.data.objects.new(name, ld))
    ob.location = loc
    return ob


def key(ob, path, frame, value=None, interp=None, index=-1):
    if value is not None:
        tgt = ob
        attr = path
        if "." in path:
            *pre, attr = path.split(".")
            for p in pre:
                tgt = getattr(tgt, p)
        if index >= 0:
            getattr(tgt, attr)[index] = value
        else:
            setattr(tgt, attr, value)
    ob.keyframe_insert(data_path=path, frame=frame, index=index)
    if interp:
        ad = ob.animation_data
        if ad and ad.action:
            for fc in _fcurves(ad.action):
                if fc.data_path == path:
                    for kp in fc.keyframe_points:
                        if abs(kp.co.x - frame) < 0.01:
                            kp.interpolation = interp


def _fcurves(action):
    """Blender 5 layered actions: collect fcurves from all channelbags."""
    out = []
    try:
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out.extend(cb.fcurves)
    except Exception:
        pass
    if not out and hasattr(action, "fcurves"):
        try:
            out = list(action.fcurves)
        except Exception:
            pass
    return out


def fcurves_of(ob):
    ad = ob.animation_data
    return _fcurves(ad.action) if ad and ad.action else []


def set_interp(ob, interp="BEZIER", easing=None):
    for fc in fcurves_of(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = interp
            if easing:
                kp.easing = easing


def add_noise_mod(ob, path, index, strength=0.05, scale=20.0, phase=0.0):
    for fc in fcurves_of(ob):
        if fc.data_path == path and fc.array_index == index:
            m = fc.modifiers.new("NOISE")
            m.strength, m.scale, m.phase = strength, scale, phase
            return m


def wiggle(ob, path="rotation_euler", axes=(0, 1, 2), strength=0.03, scale=30.0, seed=0, frame=1):
    """Ensure a key exists, then add noise modifiers (organic sway)."""
    for a in axes:
        ob.keyframe_insert(data_path=path, frame=frame, index=a)
    rnd = random.Random(seed)
    for a in axes:
        add_noise_mod(ob, path, a, strength, scale, rnd.uniform(0, 100))


# ------------------------------------------------------------------ node helpers
def N(nt, typ, loc=(0, 0), **props):
    n = nt.nodes.new(typ)
    n.location = loc
    for k, v in props.items():
        setattr(n, k, v)
    return n


_ALIASES = {"Fac": ("Fac", "Factor"), "Factor": ("Factor", "Fac")}


def I(node, name, typ=None):
    names = _ALIASES.get(name, (name,))
    cands = [s for s in node.inputs if s.name in names and (typ is None or s.type == typ)]
    en = [s for s in cands if s.enabled]
    if en:
        return en[0]
    if cands:
        return cands[0]
    raise KeyError(f"{node.bl_idname}: no input {name!r} ({typ}) in {[ (s.name, s.type) for s in node.inputs]}")


def O(node, name, typ=None):
    names = _ALIASES.get(name, (name,))
    cands = [s for s in node.outputs if s.name in names and (typ is None or s.type == typ)]
    en = [s for s in cands if s.enabled]
    if en:
        return en[0]
    if cands:
        return cands[0]
    raise KeyError(f"{node.bl_idname}: no output {name!r} ({typ}) in {[ (s.name, s.type) for s in node.outputs]}")


def L(nt, a, b):
    nt.links.new(a, b)


def val(nt, v, loc=(0, 0)):
    n = N(nt, "ShaderNodeValue", loc)
    n.outputs[0].default_value = v
    return n.outputs[0]


def math_(nt, op, a, b=None, loc=(0, 0), clamp=False):
    n = N(nt, "ShaderNodeMath", loc, operation=op, use_clamp=clamp)
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            L(nt, x, n.inputs[i])
    return n.outputs[0]


def maprange(nt, x, a, b, c=0.0, d=1.0, loc=(0, 0), clamp=True, interp="LINEAR"):
    n = N(nt, "ShaderNodeMapRange", loc, clamp=clamp, interpolation_type=interp)
    if isinstance(x, (int, float)):
        I(n, "Value").default_value = x
    else:
        L(nt, x, I(n, "Value"))
    I(n, "From Min").default_value = a
    I(n, "From Max").default_value = b
    I(n, "To Min").default_value = c
    I(n, "To Max").default_value = d
    return O(n, "Result")


def ramp(nt, stops, interp="CONSTANT", loc=(0, 0), fac=None):
    n = N(nt, "ShaderNodeValToRGB", loc)
    cr = n.color_ramp
    cr.interpolation = interp
    els = cr.elements
    while len(els) > 1:
        els.remove(els[-1])
    els[0].position = stops[0][0]
    els[0].color = hexc(stops[0][1])
    for p, c in stops[1:]:
        e = els.new(p)
        e.color = hexc(c)
    if fac is not None:
        L(nt, fac, I(n, "Fac"))
    return n


def mixcol(nt, fac, a, b, blend="MIX", loc=(0, 0)):
    n = N(nt, "ShaderNodeMix", loc, data_type="RGBA", blend_type=blend)
    if isinstance(fac, (int, float)):
        I(n, "Factor", "VALUE").default_value = fac
    else:
        L(nt, fac, I(n, "Factor", "VALUE"))
    for nm, x in (("A", a), ("B", b)):
        s = I(n, nm, "RGBA")
        if isinstance(x, (str, tuple, list)):
            s.default_value = hexc(x)
        else:
            L(nt, x, s)
    return O(n, "Result", "RGBA")


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m, m.node_tree


def finish_emission(m, nt, color_sock, strength=1.0, alpha_sock=None, blended=False, loc=(800, 0)):
    out = N(nt, "ShaderNodeOutputMaterial", (loc[0] + 400, loc[1]))
    em = N(nt, "ShaderNodeEmission", loc)
    if isinstance(color_sock, (str, tuple)):
        I(em, "Color").default_value = hexc(color_sock)
    else:
        L(nt, color_sock, I(em, "Color"))
    I(em, "Strength").default_value = strength
    if alpha_sock is None:
        L(nt, O(em, "Emission"), I(out, "Surface"))
    else:
        tr = N(nt, "ShaderNodeBsdfTransparent", (loc[0], loc[1] - 160))
        mx = N(nt, "ShaderNodeMixShader", (loc[0] + 200, loc[1]))
        if isinstance(alpha_sock, (int, float)):
            mx.inputs[0].default_value = alpha_sock
        else:
            L(nt, alpha_sock, mx.inputs[0])
        L(nt, O(tr, "BSDF"), mx.inputs[1])
        L(nt, O(em, "Emission"), mx.inputs[2])
        L(nt, mx.outputs[0], I(out, "Surface"))
        m.surface_render_method = "BLENDED" if blended else "DITHERED"
    return m


# ------------------------------------------------------------------ materials
def flat_mat(name, color, strength=1.0, alpha=None, blended=False):
    m, nt = new_mat(name)
    return finish_emission(m, nt, color, strength, alpha, blended)


def toon_mat(name, base, shadow=None, light=None, band=0.35, light_band=0.8,
             rim=None, rim_th=0.55, rim_strength=1.0, strength=1.0, tex_sock_fn=None):
    """Cel shading: diffuse -> ShaderToRGB -> constant ramp. tex_sock_fn(nt)->colour socket multiplies the result."""
    m, nt = new_mat(name)
    dif = N(nt, "ShaderNodeBsdfDiffuse", (-900, 0))
    s2r = N(nt, "ShaderNodeShaderToRGB", (-700, 0))
    bw = N(nt, "ShaderNodeRGBToBW", (-500, 0))
    L(nt, O(dif, "BSDF"), I(s2r, "Shader"))
    L(nt, O(s2r, "Color"), I(bw, "Color"))
    stops = [(0.0, shadow or mixc(base, "#000000", 0.55)), (band, base)]
    if light:
        stops.append((light_band, light))
    r = ramp(nt, stops, "CONSTANT", (-300, 0), fac=O(bw, "Val"))
    r.name = "TOON_RAMP"
    col = O(r, "Color")
    if tex_sock_fn:
        col = mixcol(nt, 1.0, col, tex_sock_fn(nt), "MULTIPLY", (-100, 200))
    if rim:
        lw = N(nt, "ShaderNodeLayerWeight", (-700, -300))
        I(lw, "Blend").default_value = 0.4
        facing = O(lw, "Facing")
        rmask = math_(nt, "GREATER_THAN", facing, rim_th, (-500, -300))
        lit = math_(nt, "GREATER_THAN", O(bw, "Val"), band * 0.6, (-500, -420))
        both = math_(nt, "MULTIPLY", rmask, lit, (-300, -350))
        both = math_(nt, "MULTIPLY", both, rim_strength, (-150, -350))
        col = mixcol(nt, both, col, rim, "MIX", (100, -100))
    return finish_emission(m, nt, col, strength)


def outline_mat(color="#070B18", name=None):
    nm = name or ("OUTLINE_" + color.strip("#"))
    m = bpy.data.materials.get(nm)
    if m:
        return m
    m = flat_mat(nm, color)
    m.use_backface_culling = True
    try:
        m.use_backface_culling_shadow = True
    except Exception:
        pass
    return m


def add_outline(ob, thickness=0.02, color="#070B18"):
    if ob.type not in ("MESH", "CURVE"):
        return
    om = outline_mat(color)
    ob.data.materials.append(om)
    md = ob.modifiers.new("Outline", "SOLIDIFY")
    sc = max(ob.scale) if max(ob.scale) > 0 else 1.0
    md.thickness = thickness / sc
    md.offset = 1.0
    md.use_flip_normals = True
    md.use_rim = False
    md.material_offset = len(ob.data.materials) - 1
    return md


def assign(ob, mat, slot_clear=True):
    if slot_clear:
        ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


# ------------------------------------------------------------------ world / sky
def sky_world(stops, ambient="#0E1630", ambient_strength=1.0, stars=None, twinkle=True,
              horizon_fade=(0.0, 0.25), milky=None, name="AF_World"):
    """stops: [(elevation z in -1..1, hex)], sky only seen by camera; ambient lights the scene.
    stars: dict(density=0.03, size=0.05, scale=220, bright=4.0, color='#DDE8FF')"""
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new(name)
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    tc = N(nt, "ShaderNodeTexCoord", (-1400, 0))
    dirv = O(tc, "Generated")
    norm = N(nt, "ShaderNodeVectorMath", (-1200, 0), operation="NORMALIZE")
    L(nt, dirv, norm.inputs[0])
    dirv = O(norm, "Vector")
    sep = N(nt, "ShaderNodeSeparateXYZ", (-1000, 0))
    L(nt, dirv, sep.inputs[0])
    z = O(sep, "Z")
    zf = maprange(nt, z, -1.0, 1.0, 0.0, 1.0, (-800, 0))
    r = ramp(nt, [((p + 1) / 2, c) for p, c in stops], "B_SPLINE", (-600, 0), fac=zf)
    sky = O(r, "Color")
    if stars:
        def star_layer(scale, density, size, bright, seed, y):
            vor = N(nt, "ShaderNodeTexVoronoi", (-800, y), voronoi_dimensions="3D", feature="F1")
            I(vor, "Scale").default_value = scale
            I(vor, "Randomness").default_value = 1.0
            mp = N(nt, "ShaderNodeMapping", (-1000, y))
            I(mp, "Location").default_value = (seed * 13.1, seed * 7.7, seed * 3.3)
            L(nt, dirv, I(mp, "Vector"))
            L(nt, O(mp, "Vector"), I(vor, "Vector"))
            d = O(vor, "Distance")
            core = maprange(nt, d, 0.0, size, 1.0, 0.0, (-600, y))
            core = math_(nt, "POWER", core, 2.2, (-450, y))
            colsep = N(nt, "ShaderNodeSeparateColor", (-600, y - 120))
            L(nt, O(vor, "Color"), colsep.inputs[0])
            pick = math_(nt, "GREATER_THAN", O(colsep, "Red"), 1.0 - density, (-450, y - 120))
            b = math_(nt, "MULTIPLY", core, pick, (-300, y))
            vary = maprange(nt, O(colsep, "Green"), 0, 1, 0.35, 1.0, (-450, y - 240))
            b = math_(nt, "MULTIPLY", b, vary, (-150, y))
            return math_(nt, "MULTIPLY", b, bright, (0, y))
        s1 = star_layer(stars.get("scale", 220), stars.get("density", 0.035), stars.get("size", 0.05), stars.get("bright", 4.0), 1, -400)
        s2 = star_layer(stars.get("scale", 220) * 0.35, stars.get("density", 0.035) * 0.5, stars.get("size", 0.05) * 0.9, stars.get("bright", 4.0) * 2.2, 2, -700)
        s = math_(nt, "ADD", s1, s2, (150, -500))
        if twinkle:
            nz = N(nt, "ShaderNodeTexNoise", (-300, -900), noise_dimensions="4D")
            I(nz, "Scale").default_value = 60.0
            L(nt, dirv, I(nz, "Vector"))
            fc = I(nz, "W").driver_add("default_value")
            fc.driver.expression = "frame*0.04"
            tw = maprange(nt, O(nz, "Fac"), 0.3, 0.7, 0.45, 1.25, (-100, -900))
            s = math_(nt, "MULTIPLY", s, tw, (300, -500))
        hz = maprange(nt, z, horizon_fade[0], horizon_fade[1], 0.0, 1.0, (150, -650))
        s = math_(nt, "MULTIPLY", s, hz, (450, -500))
        if milky:
            # milky way band along a tilted great circle
            vm = N(nt, "ShaderNodeVectorMath", (-800, -1100), operation="DOT_PRODUCT")
            L(nt, dirv, vm.inputs[0])
            vm.inputs[1].default_value = Vector(milky.get("axis", (0.3, 0.8, 0.5))).normalized()
            band = math_(nt, "ABSOLUTE", O(vm, "Value"), None, (-600, -1100))
            band = maprange(nt, band, 0.0, milky.get("width", 0.22), 1.0, 0.0, (-450, -1100))
            nz2 = N(nt, "ShaderNodeTexNoise", (-600, -1300))
            I(nz2, "Scale").default_value = 3.5
            I(nz2, "Detail").default_value = 8
            L(nt, dirv, I(nz2, "Vector"))
            mw = math_(nt, "MULTIPLY", band, maprange(nt, O(nz2, "Fac"), 0.4, 0.75, 0, 1, (-450, -1300)), (-250, -1150))
            mw = math_(nt, "MULTIPLY", mw, milky.get("bright", 0.35), (-100, -1150))
            mw = math_(nt, "MULTIPLY", mw, hz, (100, -1150))
            mwc = mixcol(nt, mw, "#000000", milky.get("color", "#9AA8E8"), "MIX", (300, -1150))
            sky = mixcol(nt, 1.0, sky, mwc, "ADD", (500, -200))
        starc = mixcol(nt, math_(nt, "MINIMUM", s, 1.0, (550, -600)), "#000000", stars.get("color", "#DDE8FF"), "MIX", (650, -500))
        # allow >1 brightness for bloom
        starc = mixcol(nt, 1.0, starc, mixcol(nt, math_(nt, "MAXIMUM", math_(nt, "SUBTRACT", s, 1.0), 0.0), "#000000", "#FFFFFF", "MIX"), "ADD", (800, -500))
        sky = mixcol(nt, 1.0, sky, starc, "ADD", (950, -200))
    bg_sky = N(nt, "ShaderNodeBackground", (1150, 100))
    L(nt, sky, I(bg_sky, "Color"))
    bg_amb = N(nt, "ShaderNodeBackground", (1150, -100))
    I(bg_amb, "Color").default_value = hexc(ambient)
    I(bg_amb, "Strength").default_value = ambient_strength
    lp = N(nt, "ShaderNodeLightPath", (1150, 300))
    mx = N(nt, "ShaderNodeMixShader", (1350, 0))
    L(nt, O(lp, "Is Camera Ray"), mx.inputs[0])
    L(nt, O(bg_amb, "Background"), mx.inputs[1])
    L(nt, O(bg_sky, "Background"), mx.inputs[2])
    out = N(nt, "ShaderNodeOutputWorld", (1550, 0))
    L(nt, mx.outputs[0], I(out, "Surface"))
    return w


# ------------------------------------------------------------------ geometry helpers
def mesh_obj(name, verts, faces, mat=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    ob = link(bpy.data.objects.new(name, me))
    if mat:
        me.materials.append(mat)
    return ob


def box(name, size, loc=(0, 0, 0), mat=None, rot=(0, 0, 0), bevel=0.0):
    sx, sy, sz = [s / 2 for s in size]
    v = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
         (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = mesh_obj(name, v, f, mat)
    ob.location = loc
    ob.rotation_euler = rot
    if bevel > 0:
        b = ob.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = 2
    return ob


def plane(name, w, h, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    v = [(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)]
    ob = mesh_obj(name, v, [(0, 1, 2, 3)], mat)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def uv_sphere(name, r=1.0, loc=(0, 0, 0), mat=None, seg=64, rings=32):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r, calc_uvs=True)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    ob.location = loc
    if mat:
        me.materials.append(mat)
    return ob


def ico(name, r=1.0, loc=(0, 0, 0), mat=None, sub=3, smooth=True):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    for f in bm.faces:
        f.smooth = smooth
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    ob.location = loc
    if mat:
        me.materials.append(mat)
    return ob


def cylinder(name, r, h, loc=(0, 0, 0), mat=None, seg=24, r2=None, cap=True):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    ob.location = loc
    if mat:
        me.materials.append(mat)
    return ob


def smooth_shade(ob):
    for p in ob.data.polygons:
        p.use_smooth = True


# ------------------------------------------------------------------ clouds
def cloud_mat(name, cols=("#2B3A6B", "#6C7FB8", "#C9D6FF"), scale=1.4, coverage=0.5, edge=0.025,
              light=(0.05, 0.10, 0.0), seed=0.0, detail=7.0, rough=0.58, distort=0.15,
              aspect=(4.0, 1.0), bottom_flat=0.35, alpha=1.0, strength=1.0, rim=None):
    m, nt = new_mat(name)
    tc = N(nt, "ShaderNodeTexCoord", (-1600, 0))
    sep = N(nt, "ShaderNodeSeparateXYZ", (-1400, 200))
    L(nt, O(tc, "Object"), sep.inputs[0])

    def density(offset, y0):
        mp = N(nt, "ShaderNodeMapping", (-1400, y0))
        I(mp, "Location").default_value = (seed * 17.3 + offset[0], seed * 5.1 + offset[1], seed * 2.9 + offset[2])
        I(mp, "Scale").default_value = (aspect[0], aspect[1], 1.0)
        L(nt, O(tc, "Object"), I(mp, "Vector"))
        nz = N(nt, "ShaderNodeTexNoise", (-1200, y0), noise_dimensions="3D")
        I(nz, "Scale").default_value = scale
        I(nz, "Detail").default_value = detail
        I(nz, "Roughness").default_value = rough
        I(nz, "Distortion").default_value = distort
        L(nt, O(mp, "Vector"), I(nz, "Vector"))
        return O(nz, "Fac")

    d0 = density((0, 0, 0), 0)
    d1 = density(light, -300)
    # shape mask: ellipse falloff + flat bottom
    x2 = math_(nt, "POWER", O(sep, "X"), 2.0, (-1200, 400))
    y2 = math_(nt, "POWER", O(sep, "Y"), 2.0, (-1200, 500))
    rr = math_(nt, "SQRT", math_(nt, "ADD", x2, y2, (-1050, 450)), None, (-900, 450))
    shape = maprange(nt, rr, 0.45, 1.0, 1.0, 0.0, (-750, 450), interp="SMOOTHSTEP")
    bot = maprange(nt, O(sep, "Y"), -0.9, -0.9 + bottom_flat * 2, 0.0, 1.0, (-750, 600), interp="SMOOTHSTEP")
    shape = math_(nt, "MULTIPLY", shape, bot, (-600, 500))
    dd0 = math_(nt, "MULTIPLY", d0, shape, (-800, 0))
    dd1 = math_(nt, "MULTIPLY", d1, shape, (-800, -300))
    a = maprange(nt, dd0, coverage * 0.62, coverage * 0.62 + edge, 0.0, 1.0, (-600, 100))
    a = math_(nt, "MULTIPLY", a, alpha, (-450, 100))
    sh = math_(nt, "SUBTRACT", dd0, dd1, (-600, -150))
    shf = maprange(nt, sh, -0.035, 0.035, 0.0, 1.0, (-450, -150))
    r = ramp(nt, [(0.0, cols[0]), (0.42, cols[1]), (0.78, cols[2])], "CONSTANT", (-300, -150), fac=shf)
    col = O(r, "Color")
    if rim:
        # thin bright edge near the cloud boundary on the lit side
        edge_m = maprange(nt, dd0, coverage * 0.62, coverage * 0.62 + edge * 4, 1.0, 0.0, (-450, -400))
        lit_m = math_(nt, "GREATER_THAN", shf, 0.5, (-450, -520))
        em_ = math_(nt, "MULTIPLY", edge_m, lit_m, (-300, -450))
        col = mixcol(nt, em_, col, rim, "MIX", (-100, -300))
    finish_emission(m, nt, col, strength, a, blended=True, loc=(200, 0))
    m.use_backface_culling = False
    return m


def cloud_card(name, loc, w, h, mat, face=(0, -1, 0)):
    ob = plane(name, 2, 2, loc=loc, mat=mat)
    ob.scale = (w / 2, h / 2, 1)
    q = Vector(face).to_track_quat("Z", "Y")
    ob.rotation_euler = q.to_euler()
    return ob


def billboard_rot(face_dir):
    return Vector(face_dir).to_track_quat("Z", "Y").to_euler()


def cumulus(name, center, size=(60, 30, 22), puffs=26, seed=0, mat=None, flat_bottom=True):
    """Anime cumulus: union of displaced spheres, flat bottom, toon-shaded by the key light."""
    rnd = random.Random(seed)
    sx, sy, sz = size
    bm_ = bmesh.new()
    for i in range(puffs):
        t = rnd.random()
        # mound distribution: bigger puffs near the centre/top
        x = rnd.gauss(0, sx * 0.28)
        y = rnd.gauss(0, sy * 0.25)
        r = (sz * 0.55) * (1.0 - min(1.0, abs(x) / (sx * 0.6))) ** 0.6 * rnd.uniform(0.55, 1.0) + sz * 0.12
        z = r * 0.55 + rnd.uniform(0, sz * 0.35) * (1.0 - abs(x) / (sx * 0.7))
        res = bmesh.ops.create_icosphere(bm_, subdivisions=3, radius=r)
        for v in res["verts"]:
            n = v.co.normalized()
            v.co = v.co * (1 + 0.06 * math.sin(n.x * 9 + i) * math.cos(n.z * 7 + seed)) + Vector((x, y, z))
            if flat_bottom and v.co.z < 0:
                v.co.z *= 0.12
    for f in bm_.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm_.to_mesh(me)
    bm_.free()
    ob = link(bpy.data.objects.new(name, me))
    ob.location = Vector(center)
    if mat:
        me.materials.append(mat)
    return ob


def moon(name, loc, size, phase=0.38, tilt=0.12, col_dark="#7FA2E0", col_lit="#FFF4D6", glow=0.35, cam_dir=None):
    """Crescent moon card with halo; billboarded toward cam_dir (vector from moon to camera)."""
    mm, nt = new_mat(name)
    tc = N(nt, "ShaderNodeTexCoord")
    sep = N(nt, "ShaderNodeSeparateXYZ")
    L(nt, O(tc, "Object"), sep.inputs[0])
    r1 = math_(nt, "SQRT", math_(nt, "ADD", math_(nt, "POWER", O(sep, "X"), 2), math_(nt, "POWER", O(sep, "Y"), 2)))
    dx = math_(nt, "SUBTRACT", O(sep, "X"), phase)
    r2 = math_(nt, "SQRT", math_(nt, "ADD", math_(nt, "POWER", dx, 2), math_(nt, "POWER", math_(nt, "SUBTRACT", O(sep, "Y"), tilt), 2)))
    disc = maprange(nt, r1, 0.40, 0.412, 1, 0)
    cut = maprange(nt, r2, 0.36, 0.372, 0, 1)
    cres = math_(nt, "MULTIPLY", disc, cut)
    halo = maprange(nt, r1, 0.4, 1.0, glow, 0.0, interp="SMOOTHSTEP")
    a = math_(nt, "MAXIMUM", cres, halo)
    colm = mixcol(nt, cres, col_dark, col_lit)
    st = maprange(nt, cres, 0, 1, 1.0, 6.0)
    finish_emission(mm, nt, colm, 1.0, a, blended=True)
    em = [n for n in nt.nodes if n.bl_idname == "ShaderNodeEmission"][0]
    L(nt, st, I(em, "Strength"))
    ob = plane(name, 2, 2, loc, mat=mm)
    ob.scale = (size, size, 1)
    if cam_dir is not None:
        ob.rotation_euler = billboard_rot(cam_dir)
    return ob


# ------------------------------------------------------------------ vegetation
def palm(name, loc, height=9.0, lean=(0.25, 0.05), bend=0.12, fronds=15, frond_len=3.8,
         seed=1, trunk_mat=None, frond_mat=None, outline=None, sway=True):
    rnd = random.Random(seed)
    loc = Vector(loc)
    lean = Vector((lean[0], lean[1], 0.0))
    side = Vector((-lean.y, lean.x, 0)).normalized() if lean.length > 1e-6 else Vector((1, 0, 0))
    cu = bpy.data.curves.new(name + "_trunk", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.17
    cu.bevel_resolution = 2
    cu.resolution_u = 10
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER")
    ts = [0.0, 0.3, 0.65, 1.0]
    sp.bezier_points.add(len(ts) - 1)
    top = None
    for bp, t in zip(sp.bezier_points, ts):
        off = lean * (t ** 1.7) * height + side * math.sin(t * math.pi) * bend * height * 0.3
        p = Vector((off.x, off.y, t * height))
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
        bp.radius = 1.05 - 0.45 * t
        top = p
    trunk = link(bpy.data.objects.new(name + "_trunk", cu))
    trunk.location = loc
    if trunk_mat:
        cu.materials.append(trunk_mat)
    # crown
    bm = bmesh.new()
    up = Vector((0, 0, 1))
    for f in range(fronds):
        az = f / fronds * 2 * math.pi + rnd.uniform(-0.25, 0.25)
        hd = Vector((math.cos(az), math.sin(az), 0))
        elev = rnd.uniform(-0.15, 0.85)
        Lf = frond_len * rnd.uniform(0.75, 1.15)
        droop = rnd.uniform(0.55, 1.1)

        def rach(s):
            return hd * (s * Lf * math.cos(elev) * 0.95) + up * (Lf * (math.sin(elev) * s - droop * 0.5 * s * s))

        nl = 30
        for k in range(nl):
            s = (k + 1) / (nl + 1)
            p = rach(s)
            tg = (rach(min(1, s + 0.01)) - rach(max(0, s - 0.01))).normalized()
            sd = tg.cross(up)
            if sd.length < 1e-4:
                sd = Vector((1, 0, 0))
            sd.normalize()
            lw = 0.95 * (math.sin(math.pi * min(1.0, s * 1.15)) ** 0.7) * (0.55 + 0.45 * rnd.random())
            for sg in (-1, 1):
                ang = math.radians(rnd.uniform(35, 55))
                ldir = (sd * sg * math.cos(ang) + tg * math.sin(ang) - up * rnd.uniform(0.25, 0.7)).normalized()
                tip = p + ldir * lw
                wv = tg * 0.035
                v1 = bm.verts.new(p - wv)
                v2 = bm.verts.new(p + wv)
                v3 = bm.verts.new(tip + wv * 0.4 - up * 0.02)
                v4 = bm.verts.new(tip - wv * 0.4)
                bm.faces.new((v1, v2, v3, v4))
        # rachis strip
        prev = None
        for k in range(nl + 2):
            s = k / (nl + 1)
            p = rach(s)
            a_ = bm.verts.new(p + Vector((0, 0, 0.03)))
            b_ = bm.verts.new(p - Vector((0, 0, 0.03)))
            if prev:
                bm.faces.new((prev[0], prev[1], b_, a_))
            prev = (a_, b_)
    me = bpy.data.meshes.new(name + "_crown")
    bm.to_mesh(me)
    bm.free()
    crown = link(bpy.data.objects.new(name + "_crown", me))
    crown.location = loc + top
    if frond_mat:
        me.materials.append(frond_mat)
    if outline:
        add_outline(crown, outline[0], outline[1])
    if sway:
        wiggle(crown, "rotation_euler", (0, 1, 2), strength=0.035, scale=55, seed=seed)
    return trunk, crown


def tree_blob(name, loc, radius=3.0, blobs=9, seed=0, mat=None, trunk_mat=None, trunk_h=2.5, outline=None, squash=0.8):
    rnd = random.Random(seed)
    bm = bmesh.new()
    for i in range(blobs):
        r = radius * rnd.uniform(0.45, 0.75)
        c = Vector((rnd.uniform(-1, 1) * radius * 0.6, rnd.uniform(-1, 1) * radius * 0.6, rnd.uniform(0, 1) * radius * 0.6 * squash))
        res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
        for v in res["verts"]:
            n = v.co.normalized()
            v.co = v.co * (1 + 0.18 * math.sin(n.x * 7 + seed) * math.cos(n.y * 6 + i)) + c
            v.co.z *= squash
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    ob.location = Vector(loc) + Vector((0, 0, trunk_h + radius * 0.4))
    if mat:
        me.materials.append(mat)
    if outline:
        add_outline(ob, outline[0], outline[1])
    tr = None
    if trunk_mat:
        tr = cylinder(name + "_trunk", radius * 0.09, trunk_h + radius * 0.4, Vector(loc) + Vector((0, 0, (trunk_h + radius * 0.4) / 2)), trunk_mat, 10, r2=radius * 0.06)
    return ob, tr


def treeline(name, x0, x1, y, z0, height=8.0, rough=3.0, seed=0, mat=None, palms=0.5, step=0.6):
    """Jagged silhouette strip (vertical) with palm-like spikes, for distant layers."""
    rnd = random.Random(seed)
    verts, faces = [], []
    xs = []
    x = x0
    while x < x1:
        xs.append(x)
        x += step * rnd.uniform(0.6, 1.4)
    tops = []
    for i, x in enumerate(xs):
        hgt = height + rough * (math.sin(x * 0.07 + seed) * 0.6 + math.sin(x * 0.23 + seed * 2) * 0.3 + rnd.uniform(-0.3, 0.3))
        tops.append(hgt)
    for i, x in enumerate(xs):
        verts.append((x, y, z0))
        verts.append((x, y, z0 + tops[i]))
    for i in range(len(xs) - 1):
        a = i * 2
        faces.append((a, a + 2, a + 3, a + 1))
    ob = mesh_obj(name, verts, faces, mat)
    # palm spikes on top
    bm = bmesh.new()
    nps = int((x1 - x0) / 9 * palms)
    for k in range(nps):
        px = rnd.uniform(x0, x1)
        i = min(range(len(xs)), key=lambda j: abs(xs[j] - px))
        ph = tops[i] + rnd.uniform(2.0, 7.0)
        base = Vector((px, y, z0 + tops[i] - 1))
        topv = Vector((px + rnd.uniform(-1.2, 1.2), y, z0 + ph))
        # trunk
        tw = 0.18
        vs = [bm.verts.new(base + Vector((-tw, 0, 0))), bm.verts.new(base + Vector((tw, 0, 0))),
              bm.verts.new(topv + Vector((tw * 0.7, 0, 0))), bm.verts.new(topv + Vector((-tw * 0.7, 0, 0)))]
        bm.faces.new(vs)
        for f in range(9):
            ang = f / 9 * math.pi * 2 + rnd.uniform(-0.2, 0.2)
            ln = rnd.uniform(2.0, 3.4)
            d = Vector((math.cos(ang), 0, math.sin(ang) * 0.6 - 0.25)).normalized()
            mid = topv + d * ln * 0.5 + Vector((0, 0, 0.35))
            tip = topv + d * ln + Vector((0, 0, -0.5))
            nrm = Vector((-d.z, 0, d.x)) * 0.16
            vs = [bm.verts.new(topv), bm.verts.new(mid + nrm), bm.verts.new(tip), bm.verts.new(mid - nrm)]
            bm.faces.new(vs)
    me2 = bpy.data.meshes.new(name + "_palms")
    bm.to_mesh(me2)
    bm.free()
    ob2 = link(bpy.data.objects.new(name + "_palms", me2))
    if mat:
        me2.materials.append(mat)
    return ob, ob2


# ------------------------------------------------------------------ compositor
def compositor(bloom=(0.85, 0.6, 0.55), streaks=None, dispersion=0.0, kuwahara=0, fog=None):
    """bloom=(threshold, strength, size); returns node group."""
    sc = bpy.context.scene
    ng = bpy.data.node_groups.new("AF_Comp", "CompositorNodeTree")
    ng.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = ng.nodes.new("CompositorNodeRLayers")
    rl.location = (-600, 0)
    cur = rl.outputs["Image"]
    x = -350
    if kuwahara:
        k = ng.nodes.new("CompositorNodeKuwahara")
        k.location = (x, 0)
        x += 220
        I(k, "Size").default_value = kuwahara
        ng.links.new(cur, I(k, "Image"))
        cur = O(k, "Image")
    if bloom:
        g = ng.nodes.new("CompositorNodeGlare")
        g.location = (x, 0)
        x += 220
        I(g, "Type").default_value = "Bloom"
        I(g, "Quality").default_value = "High"
        I(g, "Threshold").default_value = bloom[0]
        I(g, "Strength").default_value = bloom[1]
        I(g, "Size").default_value = bloom[2]
        ng.links.new(cur, I(g, "Image"))
        cur = O(g, "Image")
    if streaks:
        g = ng.nodes.new("CompositorNodeGlare")
        g.location = (x, 0)
        x += 220
        I(g, "Type").default_value = "Streaks"
        I(g, "Threshold").default_value = streaks[0]
        I(g, "Strength").default_value = streaks[1]
        I(g, "Streaks").default_value = int(streaks[2]) if len(streaks) > 2 else 4
        ng.links.new(cur, I(g, "Image"))
        cur = O(g, "Image")
    if dispersion:
        ld = ng.nodes.new("CompositorNodeLensdist")
        ld.location = (x, 0)
        x += 220
        I(ld, "Dispersion").default_value = dispersion
        ng.links.new(cur, I(ld, "Image"))
        cur = O(ld, "Image")
    out = ng.nodes.new("NodeGroupOutput")
    out.location = (x + 100, 0)
    ng.links.new(cur, out.inputs[0])
    sc.compositing_node_group = ng
    try:
        sc.render.use_compositing = True
    except Exception:
        pass
    return ng


# ------------------------------------------------------------------ render
def render_still(path, frame=None):
    sc = bpy.context.scene
    if frame is not None:
        sc.frame_set(frame)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def render_anim(outdir, f0=None, f1=None, step=1):
    sc = bpy.context.scene
    if f0 is not None:
        sc.frame_start = f0
    if f1 is not None:
        sc.frame_end = f1
    sc.frame_step = step
    os.makedirs(outdir, exist_ok=True)
    sc.render.filepath = os.path.join(outdir, "####")
    sc.render.use_overwrite = False
    sc.render.use_placeholder = True
    bpy.ops.render.render(animation=True)


def soften_toon(width=0.02):
    """Give every CONSTANT cel ramp (node TOON_RAMP) a narrow linear edge at each band boundary. Flat surfaces whose
    lighting sits right at a threshold then read as one smooth tone instead of TAA-dithered salt-and-pepper speckle."""
    n = 0
    for m in bpy.data.materials:
        if not m.node_tree:
            continue
        for nd in m.node_tree.nodes:
            if nd.bl_idname != "ShaderNodeValToRGB" or nd.color_ramp.interpolation != "CONSTANT":
                continue
            if not (nd.name.startswith("TOON_RAMP") or nd.label.startswith("TOON_RAMP")):
                continue
            cr = nd.color_ramp
            st = sorted([(e.position, tuple(e.color)) for e in cr.elements])
            if len(st) < 2 or len(st) * 2 > 30:
                continue
            new = [st[0]]
            for (p0, c0), (p1, c1) in zip(st[:-1], st[1:]):
                new.append((max(p0, p1 - width), c0))
                new.append((min(1.0, p1 + width), c1))
            while len(cr.elements) > 1:
                cr.elements.remove(cr.elements[-1])
            cr.elements[0].position, cr.elements[0].color = new[0][0], new[0][1]
            for pos, col in new[1:]:
                e = cr.elements.new(pos)
                e.color = col
            cr.interpolation = "LINEAR"
            n += 1
    return n


def save(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
