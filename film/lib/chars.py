# ALWAYS FALLING — character builder (run in the live Blender with MPFB enabled)
import bpy, bmesh, math, random
from mathutils import Vector
from bl_ext.blender_org.mpfb.services.humanservice import HumanService
from bl_ext.blender_org.mpfb.services.targetservice import TargetService

UPPER_CORE = {"spine01", "spine02", "spine03", "spine04", "spine05", "breast.L", "breast.R",
              "clavicle.L", "clavicle.R", "shoulder01.L", "shoulder01.R"}
UPPER_ARM = {"upperarm01.L", "upperarm01.R", "upperarm02.L", "upperarm02.R"}
LOWER_ARM = {"lowerarm01.L", "lowerarm01.R", "lowerarm02.L", "lowerarm02.R"}
LEGS = {"pelvis.L", "pelvis.R", "upperleg01.L", "upperleg01.R", "upperleg02.L", "upperleg02.R",
        "lowerleg01.L", "lowerleg01.R", "lowerleg02.L", "lowerleg02.R"}


def age_val(years):
    if years < 11:
        return (years - 1) / 10 * 0.1875
    if years < 25:
        return 0.1875 + (years - 11) / 14 * 0.3125
    return 0.5 + (years - 25) / 65 * 0.5


def make_human(name, age, weight=0.5, muscle=0.5, height=0.45, prop=0.55, gender=1.0, race=(0.3, 0.2, 0.5)):
    md = TargetService.get_default_macro_info_dict()
    md.update(gender=gender, age=age_val(age), muscle=muscle, weight=weight, height=height, proportions=prop)
    md["race"] = {"african": race[0], "asian": race[1], "caucasian": race[2]}
    bm = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True,
                                   feet_on_ground=True, scale=0.1, macro_detail_dict=md)
    bm.name = name + "_body"
    rig = HumanService.add_builtin_rig(bm, "default", import_weights=True)
    rig.name = name
    rig.data.name = name + "_arm"
    bake_shape_keys(bm)
    return bm, rig


def bake_shape_keys(ob):
    """Bake the current shape-key mix (MPFB age/weight/etc. targets) into the mesh and drop the keys."""
    me = ob.data
    if not me.shape_keys:
        return
    kb = me.shape_keys.key_blocks
    co = [Vector(p.co) for p in kb[0].data]
    for k in kb[1:]:
        if k.mute or k.value == 0.0:
            continue
        rel = k.relative_key
        kd, rd = k.data, rel.data
        w = k.value
        for i in range(len(co)):
            co[i] += (kd[i].co - rd[i].co) * w
    ob.shape_key_clear()
    for v, c in zip(me.vertices, co):
        v.co = c
    me.update()


def group_centroid(ob, gname):
    idx = ob.vertex_groups[gname].index
    pts = [ob.matrix_world @ v.co for v in ob.data.vertices if any(g.group == idx and g.weight > 0.5 for g in v.groups)]
    if not pts:
        return None
    c = Vector()
    for p in pts:
        c += p
    return c / len(pts)


def group_bounds(ob, gname):
    idx = ob.vertex_groups[gname].index
    pts = [ob.matrix_world @ v.co for v in ob.data.vertices if any(g.group == idx and g.weight > 0.5 for g in v.groups)]
    xs, ys, zs = zip(*pts)
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def _dominant_fn(ob, bones):
    vg = {g.index: g.name for g in ob.vertex_groups}

    def dom(v):
        best, bw = None, 0.0
        for g in v.groups:
            n = vg[g.group]
            if n in bones and g.weight > bw:
                best, bw = n, g.weight
        return best
    return dom


def garment(body, rig, name, helper, keep, inflate=0.012, smooth_iter=6, smooth_fac=0.6, material=None):
    """keep(v_world_co, dominant_bone) -> bool. Builds a separate rigged object from helper geometry."""
    ob = body.copy()
    ob.data = body.data.copy()
    ob.name = ob.data.name = name
    for c in body.users_collection:
        c.objects.link(ob)
    bones = set(b.name for b in rig.data.bones)
    dom = _dominant_fn(ob, bones)
    hidx = ob.vertex_groups[helper].index
    mw = ob.matrix_world
    keep_idx = set()
    for v in ob.data.vertices:
        inh = any(g.group == hidx and g.weight > 0.5 for g in v.groups)
        if inh and keep(mw @ v.co, dom(v)):
            keep_idx.add(v.index)
    bm_ = bmesh.new()
    bm_.from_mesh(ob.data)
    bm_.verts.ensure_lookup_table()
    dead = [v for v in bm_.verts if v.index not in keep_idx]
    bmesh.ops.delete(bm_, geom=dead, context="VERTS")
    bm_.to_mesh(ob.data)
    bm_.free()
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    sm = ob.modifiers.new("Smooth", "SMOOTH")
    sm.factor, sm.iterations = smooth_fac, smooth_iter
    dp = ob.modifiers.new("Inflate", "DISPLACE")
    dp.direction, dp.strength, dp.mid_level = "NORMAL", inflate, 0.0
    am = ob.modifiers.new("Armature", "ARMATURE")
    am.object = rig
    ob.parent = rig
    ob.data.materials.clear()
    if material:
        ob.data.materials.append(material)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def body_setup(body, rig, skin_mat=None):
    body.data.materials.clear()
    if skin_mat:
        body.data.materials.append(skin_mat)
    for p in body.data.polygons:
        p.use_smooth = True
    return body


def ref_heights(body):
    """Useful world-space heights from joint helper groups."""
    h = {}
    for k, g in [("knee", "joint-l-knee"), ("ankle", "joint-l-ankle"), ("pelvis", "joint-pelvis"),
                 ("neck", "joint-neck"), ("head", "joint-head"), ("elbow", "joint-l-elbow"),
                 ("eye", "joint-l-eye"), ("mouth", "joint-mouth"), ("shoulder", "joint-l-shoulder")]:
        c = group_centroid(body, g)
        h[k] = c
    eb = group_bounds(body, "ears")
    h["ear_zmin"], h["ear_zmax"] = eb[2]
    return h


# ---------------------------------------------------------------- wardrobe
def kurta(body, rig, name, mat, length="knee", sleeves="full", inflate=0.014):
    H = ref_heights(body)
    knee_z = H["knee"].z
    hem = knee_z + (0.02 if length == "knee" else 0.18)
    bones_ok = set(UPPER_CORE) | {"neck01"} | UPPER_ARM | (LOWER_ARM if sleeves == "full" else set())
    top = garment(body, rig, name + "_top", "helper-tights",
                  lambda co, d: d in bones_ok or (d in LEGS and co.z > H["pelvis"].z - 0.05),
                  inflate=inflate, material=mat)
    skirt = garment(body, rig, name + "_skirt", "helper-skirt",
                    lambda co, d: co.z > hem, inflate=inflate * 0.6, smooth_iter=3, material=mat)
    return [top, skirt]


def shirt(body, rig, name, mat, sleeves="half", tuck=True, inflate=0.011):
    H = ref_heights(body)
    bones_ok = set(UPPER_CORE) | {"neck01"} | UPPER_ARM | (LOWER_ARM if sleeves == "full" else set())
    waist = H["pelvis"].z + (0.06 if tuck else -0.07)
    ob = garment(body, rig, name, "helper-tights",
                 lambda co, d: (d in bones_ok and co.z > waist) or (d in LEGS and co.z > waist),
                 inflate=inflate, material=mat)
    if not tuck:
        flatten_lower_boundary(ob, band=0.06)
    return ob


def _smooth01(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def loosen_legs(ob, rig, r_top=0.098, r_hem=0.085, t0=0.10, t1=0.32):
    """Straight-cut trouser legs: push each vertex out to a smooth radius profile around the leg's bone axis
    (thigh -> ankle), so the cloth hangs instead of clinging to knees, calves and seat."""
    bpy.context.view_layer.update()
    mw = ob.matrix_world
    mwi = mw.inverted()
    legs = {}
    for side in ("L", "R"):
        A = rig.matrix_world @ rig.data.bones[f"upperleg01.{side}"].head_local
        B = rig.matrix_world @ rig.data.bones[f"lowerleg02.{side}"].tail_local
        legs[side] = (A, B)
    cx = (legs["L"][0].x + legs["R"][0].x) / 2
    for v in ob.data.vertices:
        p = mw @ v.co
        side = "L" if p.x > cx else "R"
        A, B = legs[side]
        ax = B - A
        Lax = ax.length
        axn = ax / Lax
        t = (p - A).dot(axn) / Lax
        if t < t0:
            continue
        q = A + axn * (min(1.0, t) * Lax)
        rv = p - q
        rv -= axn * rv.dot(axn)
        r = rv.length
        if r < 1e-6:
            continue
        R = r_top + (r_hem - r_top) * min(1.0, max(0.0, t))
        w = _smooth01(t0, t1, t)
        newr = r + (max(r, R) - r) * w
        v.co = mwi @ (p + rv / r * (newr - r))
    ob.data.update()


def flatten_lower_boundary(ob, band=0.05):
    """Straighten ragged hems: boundary vertices near the lowest boundary height snap to one level."""
    b = bmesh.new()
    b.from_mesh(ob.data)
    bv = [v for v in b.verts if any(e.is_boundary for e in v.link_edges)]
    if not bv:
        b.free()
        return
    zmin = min(v.co.z for v in bv)
    sel = [v for v in bv if v.co.z < zmin + band]
    if sel:
        zs = sorted(v.co.z for v in sel)
        zm = zs[len(zs) // 2]
        for v in sel:
            v.co.z = zm
    b.to_mesh(ob.data)
    b.free()


def flatten_leg_hems(ob, band=0.05):
    """Per-leg version (two hem loops on trousers/shorts)."""
    b = bmesh.new()
    b.from_mesh(ob.data)
    bv = [v for v in b.verts if any(e.is_boundary for e in v.link_edges)]
    if bv:
        zmin = min(v.co.z for v in bv)
        cx = sum(v.co.x for v in b.verts) / len(b.verts)
        for side in (1, -1):
            sel = [v for v in bv if v.co.z < zmin + band and (v.co.x - cx) * side > 0]
            if sel:
                zs = sorted(v.co.z for v in sel)
                zm = zs[len(zs) // 2]
                for v in sel:
                    v.co.z = zm
    b.to_mesh(ob.data)
    b.free()


def trousers(body, rig, name, mat, length="full", inflate=0.018, r_top=0.098, r_hem=0.085, belt_mat=None):
    H = ref_heights(body)
    hem = H["ankle"].z + 0.03 if length == "full" else H["knee"].z + 0.10
    top = H["pelvis"].z + 0.14
    ob = garment(body, rig, name, "helper-tights",
                 lambda co, d: (d in LEGS or d in ("spine05", "spine04", "spine03")) and hem < co.z < top,
                 inflate=inflate, smooth_iter=10, smooth_fac=0.8, material=mat)
    s = (H["head"].z / 1.52)
    loosen_legs(ob, rig, r_top=r_top * s, r_hem=r_hem * s)
    flatten_leg_hems(ob)
    if belt_mat is not None:
        belt = garment(body, rig, name + "_belt", "helper-tights",
                       lambda co, d: (d in LEGS or d in ("spine05", "spine04", "spine03")) and top - 0.04 < co.z < top,
                       inflate=inflate + 0.006, smooth_iter=6, smooth_fac=0.8, material=belt_mat)
        return ob, belt
    return ob


def vest(body, rig, name, mat, inflate=0.022):
    """sleeveless V-neck sweater over a shirt"""
    H = ref_heights(body)
    waist = H["pelvis"].z + 0.02
    vz0 = H["shoulder"].z - 0.17

    def keep(co, d):
        if d not in UPPER_CORE or co.z < waist:
            return False
        if d in ("shoulder01.L", "shoulder01.R"):
            return False
        if co.y < 0 and co.z > vz0 and abs(co.x) < (co.z - vz0) * 0.55:
            return False
        return True
    return garment(body, rig, name, "helper-tights", keep, inflate=inflate, material=mat)


def hair(body, rig, name, mat, style="70s", inflate=0.008):
    H = ref_heights(body)
    ear_lo, ear_hi = H["ear_zmin"], H["ear_zmax"]
    hy = H["head"].y          # MPFB humans face -Y; +Y is the back of the head

    def keep(co, d):
        back = co.y > hy + 0.01
        if style == "70s":       # full, covers top half of ears, to the nape
            if back:
                return co.z > H["neck"].z + 0.02
            return co.z > ear_lo + (ear_hi - ear_lo) * 0.45
        if style == "boy":
            if back:
                return co.z > H["neck"].z + 0.05
            return co.z > ear_hi - 0.01
        if style == "short":
            if back:
                return co.z > ear_lo + 0.01
            return co.z > ear_hi
        return True
    return garment(body, rig, name, "helper-hair", keep, inflate=inflate, smooth_iter=4, smooth_fac=0.5, material=mat)


def eyes(body, rig, name, mat):
    ob = garment(body, rig, name, "helper-l-eye", lambda co, d: True, inflate=0.0, smooth_iter=0, material=mat)
    ob2 = garment(body, rig, name + "R", "helper-r-eye", lambda co, d: True, inflate=0.0, smooth_iter=0, material=mat)
    return [ob, ob2]


def moustache(body, rig, name, mat, width=0.05, thick=0.008, droop=0.012):
    """Small tapered curve strokes above the upper lip, parented to the head bone."""
    H = ref_heights(body)
    m = H["mouth"]
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = thick
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    for sgn in (-1, 1):
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        pts = [Vector((0.0, -0.002, 0.012)), Vector((sgn * width * 0.55, 0.0, 0.010)), Vector((sgn * width, 0.012, -droop))]
        for bp, p, r in zip(sp.bezier_points, pts, (1.0, 0.9, 0.25)):
            bp.co = p
            bp.handle_left_type = bp.handle_right_type = "AUTO"
            bp.radius = r
    ob = bpy.data.objects.new(name, cu)
    for c in body.users_collection:
        c.objects.link(ob)
    # find front of face: mouth centroid is inside the head; push forward to the lip surface
    lip_front = min((body.matrix_world @ v.co).y for v in body.data.vertices
                    if abs((body.matrix_world @ v.co).x) < 0.01 and abs((body.matrix_world @ v.co).z - m.z) < 0.02)
    ob.location = Vector((m.x, lip_front - 0.004, m.z + 0.014))
    ob.parent = rig
    ob.parent_type = "BONE"
    ob.parent_bone = "head"
    # keep world position after bone parenting
    bpy.context.view_layer.update()
    pb = rig.pose.bones["head"]
    mat_bone = rig.matrix_world @ pb.matrix
    tail_off = Vector((0, pb.length, 0))
    ob.matrix_parent_inverse = (mat_bone @ __import__("mathutils").Matrix.Translation(tail_off)).inverted()
    if mat:
        cu.materials.append(mat)
    return ob


# ---------------------------------------------------------------- v2: shells cut from the body surface
def body_region(body, rig, name, keep, inflate=0.01, smooth_iter=4, smooth_fac=0.5, material=None, solid=0.0):
    """Copy of the body skin restricted to keep(co, dominant_bone); inflated outward (hair shell, brows...)."""
    ob = garment(body, rig, name, "body", keep, inflate=inflate, smooth_iter=smooth_iter, smooth_fac=smooth_fac, material=material)
    if solid:
        so = ob.modifiers.new("Thick", "SOLIDIFY")
        so.thickness, so.offset = solid, 1.0
        # move before armature so thickness is in rest space
        while ob.modifiers.find("Thick") > ob.modifiers.find("Armature"):
            bpy.ops.object.modifier_move_up({"object": ob}, modifier="Thick") if False else None
            break
    return ob


def head_frame(body):
    H = ref_heights(body)
    c = H["head"].copy()
    e = H["eye"].copy()
    return H, c, e


def hair_shell(body, rig, name, mat, hairline=0.050, side_frac=0.45, nape=0.03, inflate=0.013, exclude_ears=True):
    H, c, e = head_frame(body)
    ear_mid = H["ear_zmin"] + (H["ear_zmax"] - H["ear_zmin"]) * side_frac
    ears_idx = body.vertex_groups["ears"].index

    def keep(co, d):
        if d not in ("head", "neck03", "neck02"):
            return False
        if co.y < c.y - 0.055:                       # front of head / face
            return co.z > e.z + hairline
        if co.y < c.y + 0.0:                         # temples / sides
            return co.z > max(ear_mid, e.z + hairline * 0.55) if abs(co.x) > 0.05 else co.z > e.z + hairline
        return co.z > H["neck"].z + nape             # back
    ob = garment(body, rig, name, "body", keep, inflate=inflate, smooth_iter=6, smooth_fac=0.7, material=mat)
    if exclude_ears:
        # drop ear verts that slipped in
        import bmesh as _bm
        vg_ears = ob.vertex_groups.get("ears")
        if vg_ears:
            b = _bm.new()
            b.from_mesh(ob.data)
            dl = b.verts.layers.deform.active
            dead = [v for v in b.verts if dl and vg_ears.index in v[dl] and v[dl][vg_ears.index] > 0.3]
            _bm.ops.delete(b, geom=dead, context="VERTS")
            b.to_mesh(ob.data)
            b.free()
    return ob


def _bvh_of(ob):
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    eo = ob.evaluated_get(dg)
    me = eo.to_mesh()
    verts = [eo.matrix_world @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    eo.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys), verts


def hair_locks(body, rig, shell, name, mat, style="70s", count=70, seed=3, part_x=0.03,
               length=(0.07, 0.14), width=(0.018, 0.03), lift=0.003, fringe=12, fringe_len=(0.09, 0.15),
               fringe_dir=-1.0, thickness=0.0035):
    """Flat tapered ribbon locks hugging the hair shell (anime hair). Parented to the head bone."""
    bpy.context.view_layer.update()
    H, c, e = head_frame(body)
    tree, sverts = _bvh_of(shell)
    rnd = random.Random(seed)
    bm_ = bmesh.new()

    def flow(p):
        top = p.z > c.z + 0.06
        if style in ("70s", "side"):
            sx = 1.0 if p.x > part_x else -1.0
            d = Vector((sx * 0.9, 0.35, -0.25 if top else -1.0))
        elif style == "boy":
            d = Vector((p.x - c.x, (p.y - c.y) * 0.6, -0.9)) + Vector((0, 0, 0.0))
        else:
            d = Vector((p.x - c.x, p.y - c.y, -0.6))
        return d.normalized()

    def grow(p0, d0, L, w0, sweep=None):
        pts, ws = [], []
        p = p0.copy()
        d = d0.copy()
        n_steps = 8
        step = L / n_steps
        for k in range(n_steps + 1):
            loc, nrm, idx, dist = tree.find_nearest(p)
            if loc is None:
                break
            nrm = (loc - c).normalized() if nrm is None else nrm
            if nrm.dot(loc - c) < 0:
                nrm = -nrm
            t = k / n_steps
            pp = loc + nrm * (lift + 0.006 * t)
            pts.append((pp, nrm))
            ws.append(w0 * (1.0 - t) ** 0.8 + 0.0015)
            dd = (sweep(pp) if sweep else flow(pp))
            d = (d * 0.6 + dd * 0.4)
            d = (d - nrm * d.dot(nrm)).normalized()
            p = pp + d * step
        if len(pts) < 3:
            return
        prev = None
        for i, (pp, nrm) in enumerate(pts):
            if i < len(pts) - 1:
                fwd = (pts[i + 1][0] - pp).normalized()
            s = nrm.cross(fwd).normalized()
            a = bm_.verts.new(pp + s * ws[i] * 0.5)
            b = bm_.verts.new(pp - s * ws[i] * 0.5)
            if prev:
                bm_.faces.new((prev[0], prev[1], b, a))
            prev = (a, b)

    # main locks: roots sampled on the upper shell
    roots = [v for v in sverts if v.z > c.z - 0.02]
    for i in range(count):
        p0 = rnd.choice(roots)
        L = rnd.uniform(*length)
        w0 = rnd.uniform(*width)
        grow(p0, flow(p0), L, w0)
    # fringe: front-top roots sweeping sideways across the forehead
    front = [v for v in sverts if v.y < c.y - 0.04 and v.z > e.z + 0.05]
    for i in range(fringe if front else 0):
        p0 = rnd.choice(front)
        L = rnd.uniform(*fringe_len)
        w0 = rnd.uniform(width[0] * 1.1, width[1] * 1.2)
        grow(p0, Vector((fringe_dir, -0.15, -0.35)).normalized(), L, w0,
             sweep=lambda pp: Vector((fringe_dir, -0.1, -0.55)).normalized())
    me = bpy.data.meshes.new(name)
    bm_.to_mesh(me)
    bm_.free()
    ob = bpy.data.objects.new(name, me)
    for col in body.users_collection:
        col.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    if mat:
        me.materials.append(mat)
    so = ob.modifiers.new("Thick", "SOLIDIFY")
    so.thickness, so.offset = thickness, 1.0
    _parent_to_bone(ob, rig, "head")
    return ob


def _parent_to_bone(ob, rig, bone):
    from mathutils import Matrix
    mw = ob.matrix_world.copy()
    ob.parent = rig
    ob.parent_type = "BONE"
    ob.parent_bone = bone
    bpy.context.view_layer.update()
    pb = rig.pose.bones[bone]
    ob.matrix_parent_inverse = (rig.matrix_world @ pb.matrix @ Matrix.Translation(Vector((0, pb.length, 0)))).inverted()
    ob.matrix_world = mw


def brows(body, rig, name, mat, thick=0.0075, lift=0.002, arch=0.004, inner=0.012, outer=0.052, z_off=0.024):
    H, c, e = head_frame(body)
    ex = abs(e.x)

    def keep(co, d):
        if d != "head" or co.y > c.y - 0.06:
            return False
        ax = abs(co.x)
        if not (inner < ax < outer):
            return False
        t = (ax - inner) / (outer - inner)
        zc = e.z + z_off + arch * math.sin(t * math.pi) - 0.006 * t
        th = thick * (1.0 - 0.55 * t)
        return abs(co.z - zc) < th * 0.5
    return garment(body, rig, name, "body", keep, inflate=lift, smooth_iter=1, smooth_fac=0.3, material=mat)


def moustache2(body, rig, name, mat, width=0.030, z0=0.008, z1=0.020, droop=0.010, lift=0.0035):
    H, c, e = head_frame(body)
    m = H["mouth"]

    def keep(co, d):
        if co.y > c.y - 0.07:
            return False
        ax = abs(co.x)
        if ax > width:
            return False
        t = ax / width
        zb = m.z + z0 - droop * t * t
        zt = m.z + z1 - (z1 - z0) * 0.55 * t * t
        return zb < co.z < zt
    return garment(body, rig, name, "body", keep, inflate=lift, smooth_iter=1, smooth_fac=0.3, material=mat)


def face_ribbons(body, rig, name, mat, strokes, lift=0.0018, thickness=0.0022):
    """strokes: list of [(x, z, width), ...] in world space on the face; ray-cast from the front onto the skin."""
    bpy.context.view_layer.update()
    H, c, e = head_frame(body)
    tree, _ = _bvh_of(body)
    bm_ = bmesh.new()
    for stroke in strokes:
        pts = []
        for (x, z, w) in stroke:
            hit = tree.ray_cast(Vector((x, c.y - 0.4, z)), Vector((0, 1, 0)))
            if hit[0] is None:
                continue
            loc, nrm = hit[0], hit[1]
            if nrm.y > 0:
                nrm = -nrm
            pts.append((loc + nrm * lift, nrm, w))
        prev = None
        for i, (p, n, w) in enumerate(pts):
            fwd = (pts[min(i + 1, len(pts) - 1)][0] - pts[max(i - 1, 0)][0]).normalized()
            s = n.cross(fwd).normalized()
            a = bm_.verts.new(p + s * w * 0.5)
            b = bm_.verts.new(p - s * w * 0.5)
            if prev:
                bm_.faces.new((prev[0], prev[1], b, a))
            prev = (a, b)
    me = bpy.data.meshes.new(name)
    bm_.to_mesh(me)
    bm_.free()
    ob = bpy.data.objects.new(name, me)
    for col in body.users_collection:
        col.objects.link(ob)
    if mat:
        me.materials.append(mat)
    so = ob.modifiers.new("Thick", "SOLIDIFY")
    so.thickness, so.offset = thickness, 1.0
    _parent_to_bone(ob, rig, "head")
    return ob


def brow_strokes(body, inner=0.011, outer=0.054, z_off=0.025, arch=0.0055, w_in=0.0105, w_out=0.0035, n=10):
    H, c, e = head_frame(body)
    out = []
    for sgn in (-1, 1):
        st = []
        for k in range(n):
            t = k / (n - 1)
            x = c.x + sgn * (inner + t * (outer - inner))
            z = e.z + z_off + arch * math.sin(min(1.0, t * 1.15) * math.pi) - 0.005 * t
            w = w_in * (1 - t) + w_out * t
            st.append((x, z, w))
        out.append(st)
    return out


def moustache_strokes(body, width=0.033, z_top=0.019, droop=0.011, w_c=0.0125, w_e=0.005, n=9):
    H, c, e = head_frame(body)
    lip_top = group_bounds(body, "lips")[2][1]
    out = []
    for sgn in (-1, 1):
        st = []
        for k in range(n):
            t = k / (n - 1)
            x = c.x + sgn * (0.001 + t * width)
            z = lip_top + 0.0085 + (z_top - 0.019) - droop * t * t - 0.003 * t
            w = w_c * (1 - t) + w_e * t
            st.append((x, z, w))
        out.append(st)
    return out


def eye_decals(body, rig, name, white_mat, iris_mat, hl_mat, w=0.030, h=0.0125, iris_r=0.0058, look=(0.0, 0.0), z_adj=0.0, lash_mat=None):
    """Anime eyes: almond sclera + iris + highlight, ray-cast onto the eyelids, parented to the head bone."""
    bpy.context.view_layer.update()
    H, c, e = head_frame(body)
    tree, _ = _bvh_of(body)
    le = group_centroid(body, "joint-l-eye")
    re = group_centroid(body, "joint-r-eye")
    objs = []
    for side, ec in (("L", le), ("R", re)):
        hit = tree.ray_cast(Vector((ec.x, c.y - 0.4, ec.z + z_adj)), Vector((0, 1, 0)))
        if hit[0] is None:
            continue
        p0, n0 = hit[0], hit[1]
        if n0.y > 0:
            n0 = -n0
        # local frame on the face: u = outward (temple direction), v = up
        out_dir = 1.0 if ec.x > c.x else -1.0
        u = Vector((out_dir, 0, 0))
        u = (u - n0 * u.dot(n0)).normalized()
        v = n0.cross(u).normalized()
        if v.z < 0:
            v = -v

        def disc(nm, center, rx, ry, lift, mat, seg=20, almond=False):
            bm_ = bmesh.new()
            cv = bm_.verts.new(center + n0 * lift)
            ring = []
            for k in range(seg):
                a = 2 * math.pi * k / seg
                x = math.cos(a) * rx
                y = math.sin(a) * ry
                if almond:
                    y *= (1.0 - 0.35 * (x / rx) ** 2)
                    y += (0.0025 if y > 0 else 0.0) * (1 - (x / rx) ** 2)
                    x *= (1.0 + 0.12 * (1 if x * out_dir > 0 else 0))
                ring.append(bm_.verts.new(center + u * x + v * y + n0 * lift))
            for k in range(seg):
                bm_.faces.new((cv, ring[k], ring[(k + 1) % seg]))
            me = bpy.data.meshes.new(nm)
            bm_.to_mesh(me)
            bm_.free()
            ob = bpy.data.objects.new(nm, me)
            for col in body.users_collection:
                col.objects.link(ob)
            me.materials.append(mat)
            _parent_to_bone(ob, rig, "head")
            objs.append(ob)
            return ob
        disc(f"{name}_sclera{side}", p0, w / 2, h / 2, 0.0016, white_mat, almond=True)
        ic = p0 + u * look[0] * out_dir + v * look[1]
        disc(f"{name}_iris{side}", ic, iris_r, iris_r * 1.05, 0.0021, iris_mat)
        disc(f"{name}_hl{side}", ic + u * (-iris_r * 0.35 * out_dir) + v * (iris_r * 0.45), iris_r * 0.32, iris_r * 0.32, 0.0026, hl_mat, seg=10)
        # upper lash line: thin dark stroke along the top of the almond, thicker at the outer corner
        if lash_mat is not None:
            bm_ = bmesh.new()
            prev = None
            n_ = 14
            for k in range(n_ + 1):
                t = k / n_
                x = (-1 + 2 * t) * (w / 2) * 1.08
                y = (h / 2) * (1.0 - 0.35 * (x / (w / 2)) ** 2) + 0.0018 * (1 - (x / (w / 2)) ** 2)
                outer = (x * out_dir) > 0
                th = 0.0011 + (0.0016 * max(0.0, x * out_dir / (w / 2)))
                pc = p0 + u * x + v * y + n0 * 0.0028
                a = bm_.verts.new(pc + v * th)
                b = bm_.verts.new(pc - v * th * 0.4)
                if prev:
                    bm_.faces.new((prev[0], prev[1], b, a))
                prev = (a, b)
            me = bpy.data.meshes.new(f"{name}_lash{side}")
            bm_.to_mesh(me)
            bm_.free()
            ob = bpy.data.objects.new(f"{name}_lash{side}", me)
            for col in body.users_collection:
                col.objects.link(ob)
            me.materials.append(lash_mat)
            _parent_to_bone(ob, rig, "head")
            objs.append(ob)
    return objs


def neckline(garment_ob, body, depth=0.02, slit=0.11, slit_w=0.012):
    """Trim a top garment at the neck and cut a front placket slit (kurta)."""
    H, c, e = head_frame(body)
    nz = H["neck"].z - depth
    b = bmesh.new()
    b.from_mesh(garment_ob.data)
    mw = garment_ob.matrix_world
    dead = []
    for v in b.verts:
        co = mw @ v.co
        if co.z > nz:
            dead.append(v)
        elif slit and co.y < c.y - 0.02 and abs(co.x) < slit_w and co.z > nz - slit:
            dead.append(v)
    bmesh.ops.delete(b, geom=dead, context="VERTS")
    b.to_mesh(garment_ob.data)
    b.free()


def add_subsurf(ob, levels=1):
    am = ob.modifiers.get("Armature")
    ss = ob.modifiers.new("Subsurf", "SUBSURF")
    ss.levels = ss.render_levels = levels
    return ss


def outline_all(objs, thickness=0.004, color="#0A0710"):
    import af
    for ob in objs:
        if ob.type == "MESH":
            af.add_outline(ob, thickness, color)
