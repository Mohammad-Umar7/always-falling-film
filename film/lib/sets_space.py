# ALWAYS FALLING — space set: anime Earth, Aryabhata, sun, stars; Kosmos-3M launch
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Euler
import af
from af import hexc, N, I, O, L, mixcol, math_, maprange, ramp, new_mat, finish_emission

EARTH_R = 3000.0          # scaled Earth (altitude/radius ratio kept ~ real for 600 km orbit)
ALT = 280.0
DL = os.path.join(af.ASSETS, "dl")
DAY_TEX = os.path.join(af.ASSETS, "earth_day_poster.png")      # posterised cel map (matches the 92,000-orbit montage)
CLOUD = {"scale": 6.5, "cover": 0.55, "white": "#D6DEF6"}
NIGHT_TEX = os.path.join(af.ASSETS, "earth_night_clean.png")


def space_world(stars_bright=5.0, milky=True):
    af.sky_world([(-1.0, "#01020A"), (0.0, "#02030C"), (1.0, "#02030E")], ambient="#0A1030", ambient_strength=0.35,
                 stars=dict(density=0.09, size=0.07, scale=300, bright=stars_bright, color="#E8EEFF"),
                 milky=dict(axis=(0.2, 0.5, 0.84), width=0.24, bright=0.5, color="#8E9CE6") if milky else None,
                 horizon_fade=(-1.0, -0.99))


def _img(path, colorspace="sRGB"):
    im = bpy.data.images.load(path, check_existing=True)
    try:
        im.colorspace_settings.name = colorspace
    except Exception:
        pass
    return im


def face_latlon(lat, lon, north=(0, 1, 0), up=(0, 0, 1)):
    """Euler rotation for the Earth object so geographic (lat, lon) faces `up`, north toward `north`."""
    la, lo = math.radians(lat), math.radians(lon)
    d = Vector((math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)))
    q1 = d.rotation_difference(Vector(up))
    n_local = Vector((0, 0, 1))
    n_world = q1 @ n_local
    n_world = (n_world - Vector(up) * n_world.dot(Vector(up))).normalized()
    tgt = Vector(north)
    ang = math.atan2(n_world.cross(tgt).dot(Vector(up)), n_world.dot(tgt))
    q2 = __import__("mathutils").Quaternion(Vector(up), ang)
    return (q2 @ q1).to_euler()


def earth(center=(0, 0, -(EARTH_R + ALT)), rot=(0, 0, 0), sun_dir=(1, 0, 0), lights=1.0, clouds=True, name="earth"):
    """Anime Earth: posterised day map, night lights on the dark side, toon cloud shell, atmosphere rim."""
    m, nt = new_mat(name + "_mat")
    tc = N(nt, "ShaderNodeTexCoord")
    nrm = N(nt, "ShaderNodeVectorMath", operation="NORMALIZE")
    L(nt, O(tc, "Object"), nrm.inputs[0])
    sx = N(nt, "ShaderNodeSeparateXYZ")
    L(nt, O(nrm, "Vector"), sx.inputs[0])
    lon = math_(nt, "ARCTAN2", O(sx, "Y"), O(sx, "X"))
    u = math_(nt, "ADD", math_(nt, "DIVIDE", lon, 2 * math.pi), 0.5)
    lat = math_(nt, "ARCSINE", O(sx, "Z"))
    v = math_(nt, "ADD", math_(nt, "DIVIDE", lat, math.pi), 0.5)
    uv = N(nt, "ShaderNodeCombineXYZ")
    L(nt, u, uv.inputs[0])
    L(nt, v, uv.inputs[1])
    day = N(nt, "ShaderNodeTexImage")
    day.image = _img(DAY_TEX)
    day.interpolation = "Linear"
    L(nt, O(uv, "Vector"), I(day, "Vector"))
    night = N(nt, "ShaderNodeTexImage")
    night.image = _img(NIGHT_TEX)
    L(nt, O(uv, "Vector"), I(night, "Vector"))
    # stylise day colours: saturate, then step each channel (keeps real geography, reads painted)
    hs = N(nt, "ShaderNodeHueSaturation")
    I(hs, "Saturation").default_value = 1.15
    I(hs, "Value").default_value = 1.12
    L(nt, O(day, "Color"), I(hs, "Color"))
    sep = N(nt, "ShaderNodeSeparateColor")
    L(nt, O(hs, "Color"), sep.inputs[0])
    comb = N(nt, "ShaderNodeCombineColor")
    for k, ch in enumerate(("Red", "Green", "Blue")):
        L(nt, O(sep, ch), comb.inputs[k])
    blue_dom = math_(nt, "SUBTRACT", O(sep, "Blue"), math_(nt, "MAXIMUM", O(sep, "Red"), O(sep, "Green")))
    ocean = maprange(nt, blue_dom, 0.0, 0.08, 0, 1)
    bwo = N(nt, "ShaderNodeRGBToBW")
    L(nt, O(day, "Color"), I(bwo, "Color"))
    oc_r = ramp(nt, [(0.0, "#0E3A84"), (0.2, "#1B5CB4")], "LINEAR", fac=O(bwo, "Val"))
    albedo = mixcol(nt, math_(nt, "MULTIPLY", ocean, 0.75), O(comb, "Color"), O(oc_r, "Color"))
    # toon light: diffuse -> shader to rgb -> bands
    dif = N(nt, "ShaderNodeBsdfDiffuse")
    s2r = N(nt, "ShaderNodeShaderToRGB")
    L(nt, O(dif, "BSDF"), I(s2r, "Shader"))
    lb = N(nt, "ShaderNodeRGBToBW")
    L(nt, O(s2r, "Color"), I(lb, "Color"))
    lit = O(lb, "Val")
    band = ramp(nt, [(0.0, "#000000"), (0.03, "#2A2A48"), (0.12, "#9A9AB8"), (0.3, "#FFFFFF")], "LINEAR", fac=lit)
    shaded = mixcol(nt, 1.0, albedo, O(band, "Color"), "MULTIPLY")
    # terminator warm band
    term = maprange(nt, lit, 0.02, 0.12, 1.0, 0.0)
    term2 = maprange(nt, lit, 0.0, 0.02, 0.0, 1.0)
    tmask = math_(nt, "MULTIPLY", term, term2)
    shaded = mixcol(nt, math_(nt, "MULTIPLY", tmask, 0.55), shaded, "#FF8A4A")
    if clouds:
        cnz = N(nt, "ShaderNodeTexNoise", noise_dimensions="3D")
        I(cnz, "Scale").default_value = CLOUD["scale"]
        I(cnz, "Detail").default_value = 5.0
        I(cnz, "Roughness").default_value = 0.55
        I(cnz, "Distortion").default_value = 1.4
        L(nt, O(nrm, "Vector"), I(cnz, "Vector"))
        cov = maprange(nt, O(cnz, "Fac"), 0.60, 0.64, 0.0, CLOUD["cover"])
        ccol = ramp(nt, [(0.0, "#0A0E20"), (0.04, "#4E5684"), (0.14, "#C8D2F4"), (0.3, CLOUD["white"])], "LINEAR", fac=lit)
        shaded = mixcol(nt, cov, shaded, O(ccol, "Color"))
    ntint = maprange(nt, lit, 0.0, 0.14, 0.9, 0.0)
    shaded = mixcol(nt, ntint, shaded, "#050A1C")
    # night lights on the dark side
    nbw = N(nt, "ShaderNodeRGBToBW")
    L(nt, O(night, "Color"), I(nbw, "Color"))
    city = maprange(nt, O(nbw, "Val"), 0.34, 0.7, 0.0, 1.0)
    dark = maprange(nt, lit, 0.0, 0.06, 1.0, 0.0)
    cmask = math_(nt, "MULTIPLY", math_(nt, "MULTIPLY", city, dark), lights)
    city_col = mixcol(nt, cmask, "#000000", "#FFC46A")
    col = mixcol(nt, 1.0, shaded, city_col, "ADD")
    em = N(nt, "ShaderNodeEmission")
    L(nt, col, I(em, "Color"))
    I(em, "Strength").default_value = 1.0
    out = N(nt, "ShaderNodeOutputMaterial")
    L(nt, O(em, "Emission"), I(out, "Surface"))
    e = af.uv_sphere(name, EARTH_R, center, m, 256, 128)
    e.rotation_euler = rot
    objs = [e]
    # atmosphere rim (fresnel glow, transparent centre)
    am, ant = new_mat(name + "_atmo")
    lw = N(ant, "ShaderNodeLayerWeight")
    I(lw, "Blend").default_value = 0.25
    fr = maprange(ant, O(lw, "Facing"), 0.55, 1.0, 0.0, 1.0, interp="SMOOTHSTEP")
    finish_emission(am, ant, "#6FD3FF", 2.2, fr, blended=True)
    am.use_backface_culling = True
    a = af.uv_sphere(name + "_atmo", EARTH_R * 1.025, center, am, 128, 64)
    a.visible_shadow = False
    e.visible_shadow = False
    objs.append(a)
    return objs


def rhombicuboctahedron(scale=1.0):
    s2 = 1 + math.sqrt(2)
    pts = set()
    for a in (1, -1):
        for b in (1, -1):
            for c in (s2, -s2):
                for perm in ((a, b, c), (a, c, b), (c, a, b)):
                    pts.add(perm)
    bm_ = bmesh.new()
    for p in pts:
        bm_.verts.new(Vector(p) * scale)
    bmesh.ops.convex_hull(bm_, input=bm_.verts)
    bmesh.ops.dissolve_limit(bm_, angle_limit=math.radians(1.0), verts=bm_.verts, edges=bm_.edges)
    return bm_


def cell_mat(name="solar_cells"):
    """Solar cells: dark blue with silver grid, toon bands + anime glint."""
    def tex(nt):
        tc = N(nt, "ShaderNodeTexCoord")
        mp = N(nt, "ShaderNodeMapping")
        I(mp, "Scale").default_value = (9.0, 9.0, 9.0)
        L(nt, O(tc, "Object"), I(mp, "Vector"))
        br = N(nt, "ShaderNodeTexBrick")
        br.offset = 0.0
        I(br, "Color1").default_value = (1, 1, 1, 1)
        I(br, "Color2").default_value = (0.82, 0.86, 1.0, 1)
        I(br, "Mortar").default_value = (3.5, 3.6, 4.0, 1)
        I(br, "Mortar Size").default_value = 0.035
        I(br, "Brick Width").default_value = 0.5
        I(br, "Row Height").default_value = 0.5
        L(nt, O(mp, "Vector"), I(br, "Vector"))
        return O(br, "Color")
    return af.toon_mat(name, "#1B2A6B", shadow="#0A1030", light="#4A6AD0", band=0.25, light_band=0.7, rim="#9FC0FF", rim_th=0.62, tex_sock_fn=tex)


def aryabhata(loc=(0, 0, 0), name="aryabhata", lights=True):
    root = bpy.data.objects.new(name, None)
    af.link(root)
    root.location = loc
    bm_ = rhombicuboctahedron(0.25)
    me = bpy.data.meshes.new(name + "_body")
    bm_.to_mesh(me)
    bm_.free()
    body = af.link(bpy.data.objects.new(name + "_body", me))
    body.scale = (1, 1, 0.82)
    cells = cell_mat(name + "_cells")
    foil = af.toon_mat(name + "_foil", "#D9A440", shadow="#6A4418", light="#FFE29A", band=0.25, light_band=0.7, rim="#FFF2C8", rim_th=0.6)
    me.materials.append(cells)
    me.materials.append(foil)
    for p in me.polygons:
        if abs(p.normal.z) > 0.95:
            p.material_index = 1
    for p in me.polygons:
        p.use_smooth = False
    body.parent = root
    af.add_outline(body, 0.012, "#05060E")
    frame_ob = body.copy()
    frame_ob.data = body.data.copy()
    frame_ob.name = name + "_frame"
    af.link(frame_ob)
    for md in list(frame_ob.modifiers):
        frame_ob.modifiers.remove(md)
    wf = frame_ob.modifiers.new("frame", "WIREFRAME")
    wf.thickness = 0.022
    wf.use_replace = True
    wf.use_even_offset = True
    frame_ob.data.materials.clear()
    frame_ob.data.materials.append(af.toon_mat(name + "_framemetal", "#A8AEBE", shadow="#3A3E50", light="#F4F6FF", band=0.3, light_band=0.7))
    frame_ob.parent = root
    metal = af.toon_mat(name + "_metal", "#B8BCC8", shadow="#4A4E5E", light="#F2F4FA", band=0.3, light_band=0.75)
    parts = []
    # antennas: four whips from the lower ring, angled outward/down
    for k in range(4):
        a = math.radians(45 + 90 * k)
        base = Vector((math.cos(a) * 0.42, math.sin(a) * 0.42, -0.36))
        d = Vector((math.cos(a) * 0.55, math.sin(a) * 0.55, -0.83)).normalized()
        ant = af.cylinder(f"{name}_ant{k}", 0.009, 0.95, base + d * 0.475, metal, 6)
        ant.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        ant.parent = root
        parts.append(ant)
    # top: small sensor dome + stub mast
    dome = af.uv_sphere(name + "_dome", 0.09, (0, 0, 0.6), metal, 16, 8)
    dome.parent = root
    mast = af.cylinder(name + "_mast", 0.012, 0.25, (0, 0, 0.72), metal, 6)
    mast.parent = root
    st = []
    if lights:
        for k, c in enumerate(("#FF4040", "#40FF7A", "#FFC040")):
            a = math.radians(20 + 120 * k)
            lm = af.flat_mat(f"{name}_led{k}", c, strength=8.0)
            led = af.ico(f"{name}_led{k}", 0.022, (math.cos(a) * 0.37, math.sin(a) * 0.37, 0.50), lm, sub=1)
            led.parent = root
            st.append(led)
    return root, body, st


def sun_disc(direction, dist=8000.0, size=260.0, name="sun"):
    d = Vector(direction).normalized()
    return af.moon(name, d * dist, size, phase=5.0, tilt=0.0, col_dark="#FFE9B0", col_lit="#FFFFFF", glow=0.9, cam_dir=-d)


# ------------------------------------------------------------------ launch
def kosmos3m(loc=(0, 0, 0), name="kosmos"):
    """Kosmos-3M (11K65M): ~32 m, 2.4 m diameter, two stages, payload fairing."""
    root = bpy.data.objects.new(name, None)
    af.link(root)
    root.location = loc
    white = af.toon_mat(name + "_white", "#E8E6E0", shadow="#8A8C9E", light="#FFFFFF", band=0.32, light_band=0.78, rim="#FFFFFF")
    grey = af.toon_mat(name + "_grey", "#7E8A84", shadow="#3A423E", light="#AEBAB2", band=0.32, light_band=0.78)
    dark = af.toon_mat(name + "_dark", "#2C2E36", shadow="#121318", light="#4A4C58", band=0.32)
    parts = []
    r = 1.2
    parts.append(af.cylinder(name + "_s1", r, 22.0, (0, 0, 11.0 + 2.0), white, 32))
    for z in (5.0, 14.0, 21.0):
        parts.append(af.cylinder(f"{name}_band{z}", r * 1.01, 0.8, (0, 0, z), grey, 32))
    parts.append(af.cylinder(name + "_inter", r, 1.6, (0, 0, 24.8), dark, 32))
    parts.append(af.cylinder(name + "_s2", r, 4.6, (0, 0, 27.9), white, 32))
    parts.append(af.cylinder(name + "_fair", r * 1.04, 3.0, (0, 0, 31.7), white, 32))
    cone = af.cylinder(name + "_cone", r * 1.04, 3.2, (0, 0, 34.8), white, 32, r2=0.12)
    parts.append(cone)
    # four nozzles
    for k in range(4):
        a = math.radians(45 + 90 * k)
        nz = af.cylinder(f"{name}_noz{k}", 0.32, 1.6, (math.cos(a) * 0.55, math.sin(a) * 0.55, 1.2), dark, 16, r2=0.48)
        parts.append(nz)
    for p in parts:
        p.parent = root
        af.add_outline(p, 0.05, "#141018")
    return root


def launch_pad(loc=(0, 0, 0), name="pad"):
    steel = af.toon_mat(name + "_steel", "#6A6A72", shadow="#2C2C36", light="#9A9AA6", band=0.32, light_band=0.78)
    conc = af.toon_mat(name + "_conc", "#9E9A90", shadow="#55546A", light="#CFCAC0", band=0.32, light_band=0.78)
    parts = [af.box(name + "_deck", (16, 16, 2.0), (0, 0, -1.0), conc)]
    # flame trench hole (dark)
    parts.append(af.plane(name + "_trench", 5, 5, (0, 0, 0.01), mat=af.flat_mat(name + "_hole", "#0A0A10")))
    # umbilical tower: lattice-ish box tower with cross bars
    tx = 5.2
    for z in range(0, 36, 3):
        parts.append(af.box(f"{name}_ring{z}", (2.6, 2.6, 0.25), (tx, 0, z + 1.5), steel))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(af.box(f"{name}_leg{sx}{sy}", (0.25, 0.25, 36), (tx + sx * 1.2, sy * 1.2, 18), steel))
    for z in (12, 22, 30):
        parts.append(af.box(f"{name}_arm{z}", (3.0, 0.3, 0.3), (tx - 2.6, 0, z), steel))
    for p in parts:
        af.add_outline(p, 0.04, "#141018")
    return parts


def smoke_puffs(name, origin, n=40, seed=1, mat=None, spread=18.0, frames=(1, 120), up=6.0, ang=(0.0, 360.0)):
    """Anime smoke: toon spheres that grow and drift outward from the pad over time."""
    rnd = random.Random(seed)
    o = Vector(origin)
    puffs = []
    for i in range(n):
        a_ = math.radians(rnd.uniform(*ang))
        d = Vector((math.cos(a_), math.sin(a_), 0))
        f_start = frames[0] + int(rnd.uniform(0, 0.4) * (frames[1] - frames[0]))
        r_end = rnd.uniform(3.0, 7.5)
        p = af.ico(f"{name}{i}", 1.0, o, mat, sub=3)
        p.scale = (0.01, 0.01, 0.01)
        p.keyframe_insert("scale", frame=f_start)
        p.keyframe_insert("location", frame=f_start)
        p.scale = (r_end, r_end, r_end * 0.85)
        p.location = o + d * rnd.uniform(0.6, 1.0) * spread + Vector((0, 0, rnd.uniform(0.5, up)))
        p.keyframe_insert("scale", frame=frames[1])
        p.keyframe_insert("location", frame=frames[1])
        for fc in af.fcurves_of(p):
            for kp in fc.keyframe_points:
                kp.interpolation = "EXPO"
                kp.easing = "EASE_OUT"
        puffs.append(p)
    return puffs


def flame(name, origin, length=14.0, radius=1.6):
    """Engine plume: layered emissive cones (white core -> yellow -> orange), pointing down."""
    objs = []
    for k, (col, rr, ll, st) in enumerate([("#FFFFFF", 0.45, 0.45, 12.0), ("#FFE27A", 0.75, 0.75, 7.0), ("#FF8A3A", 1.0, 1.0, 4.0)]):
        m = af.flat_mat(f"{name}_m{k}", col, strength=st, alpha=0.9 if k else 1.0, blended=True)
        c = af.cylinder(f"{name}{k}", radius * rr, length * ll, Vector(origin) - Vector((0, 0, length * ll / 2)), m, 24, r2=radius * rr * 0.15)
        c.rotation_euler = (math.radians(180), 0, 0)
        c.location = Vector(origin) - Vector((0, 0, length * ll / 2))
        objs.append(c)
    return objs
