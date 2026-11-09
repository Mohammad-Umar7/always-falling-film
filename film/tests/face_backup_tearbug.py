# ALWAYS FALLING - facial expressions for the MPFB cast.
#
# Anime faces here are decals parented to the head bone (eye sclera/iris/highlight/lash per eye, brow ribbons,
# moustache) on top of the MPFB body, whose "default" rig carries real face bones. Expressions therefore mix:
#   * shape keys generated on the decals at load time, in rig space at the rest pose (blink, squint, wide,
#     sad/angry lids, look direction, brow up/down/sad/angry, moustache follows the mouth, tears),
#   * face-bone rotations for the mouth (smile / frown / jaw open), measured numerically on the rig:
#       jaw X+  opens (lower lip ~13 mm at open=1 on an adult)
#       oris04 X-, oris03 X-, levator02 X-, risorius02 X+  lift the corners (~10 mm at smile=1)
#   * a dark mouth interior + upper-teeth strip parented to the head, revealed when the jaw opens,
#   * lip flap driven by the voice clip's loudness, and automatic blinks.
#
#   F = face.Face(rig)
#   F.key(1, "listen"); F.key(60, "soft_smile"); F.key(130, {"brow_sad": .8, "tears": 1})
#   F.lipsync(wav, start_frame=40)          # local shot frame where the clip starts
#   F.bake(1, n_frames)
import bpy, math, wave, random
import numpy as np
from mathutils import Vector, Matrix
import af

FACE_PREFIX = ("jaw", "special0", "oris", "levator", "risorius", "orbicularis", "temporalis", "tongue")


def is_face_bone(n):
    return n.startswith(FACE_PREFIX) or n in ("eye.L", "eye.R")


def _base(name):
    head, _, tail = name.rpartition(".")
    return head if head and tail.isdigit() else name


CONTROLS = ("blink", "squint", "wide", "lid_sad", "lid_angry", "look_x", "look_y",
            "brow_up", "brow_down", "brow_sad", "brow_angry", "smile", "frown", "open", "tears", "sparkle")

PRESETS = {
    "neutral": {},
    "listen": {"brow_up": 0.25, "wide": 0.15},
    "soft_smile": {"smile": 0.42, "squint": 0.25, "brow_up": 0.12},
    "smile": {"smile": 0.8, "squint": 0.55, "brow_up": 0.15},
    "proud": {"smile": 0.55, "squint": 0.3, "brow_up": 0.2, "look_y": -0.2},
    "wonder": {"wide": 0.55, "brow_up": 0.55, "open": 0.14, "smile": 0.18, "look_y": 0.5},
    "awe": {"wide": 0.85, "brow_up": 0.85, "open": 0.3, "look_y": 0.6},
    "shock": {"wide": 1.0, "brow_up": 1.0, "open": 0.5},
    "worry": {"brow_sad": 0.7, "lid_sad": 0.4, "frown": 0.3},
    "sad": {"brow_sad": 0.9, "lid_sad": 0.55, "blink": 0.3, "frown": 0.5, "look_y": -0.5},
    "sad_closed": {"brow_sad": 0.9, "lid_sad": 0.3, "blink": 1.0, "frown": 0.55},
    "bittersweet": {"smile": 0.32, "brow_sad": 0.6, "lid_sad": 0.4, "squint": 0.12},
    "hurt": {"brow_sad": 0.65, "brow_down": 0.25, "frown": 0.7, "lid_angry": 0.1, "blink": 0.2},
    "resolve": {"brow_down": 0.45, "brow_angry": 0.3, "frown": 0.25, "lid_angry": 0.3},
    "numb": {"blink": 0.35, "look_y": -0.6, "frown": 0.15},
    "teary": {"brow_sad": 1.0, "lid_sad": 0.5, "wide": 0.25, "tears": 1.0, "frown": 0.35, "open": 0.06},
    "teary_smile": {"brow_sad": 0.8, "lid_sad": 0.35, "tears": 1.0, "smile": 0.5, "squint": 0.2},
    "shame": {"brow_sad": 0.6, "blink": 0.45, "look_y": -1.0, "frown": 0.35},
    "kira": {"wide": 0.5, "brow_up": 0.5, "open": 0.12, "smile": 0.3, "look_y": 0.3, "sparkle": 1.0},
    "teary_kira": {"brow_sad": 0.8, "lid_sad": 0.35, "tears": 1.0, "smile": 0.5, "squint": 0.15, "sparkle": 0.8},
}

# mouth bones: control -> {bone: (x, y, z) degrees at value 1}
MOUTH = {
    "smile": {"oris04.L": (-22, 0, 0), "oris04.R": (-22, 0, 0), "oris03.L": (-18, 0, 0), "oris03.R": (-18, 0, 0),
              "levator02.L": (-14, 0, 0), "levator02.R": (-14, 0, 0), "risorius02.L": (18, 0, 0), "risorius02.R": (18, 0, 0)},
    "frown": {"oris04.L": (22, 0, 0), "oris04.R": (22, 0, 0), "oris03.L": (16, 0, 0), "oris03.R": (16, 0, 0)},
    "open": {"jaw": (11, 0, 0)},
}


def _interp_curve(pts):
    """pts: [(x, z)] -> f(x) linear, clamped"""
    pts = sorted(pts)
    xs = np.array([p[0] for p in pts])
    zs = np.array([p[1] for p in pts])

    def f(x):
        return float(np.interp(x, xs, zs))
    return f


def _envelopes(P, xmin, xmax, bins=18):
    """upper / lower boundary of a filled 2D shape (x, z) as interpolating functions"""
    edges = np.linspace(xmin, xmax, bins + 1)
    up, lo = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        zs = [p.z for p in P if a <= p.x <= b]
        if zs:
            xm = (a + b) / 2
            up.append((xm, max(zs)))
            lo.append((xm, min(zs)))
    up = [(xmin, up[0][1])] + up + [(xmax, up[-1][1])]
    lo = [(xmin, lo[0][1])] + lo + [(xmax, lo[-1][1])]
    return _interp_curve(up), _interp_curve(lo)


def _fcurves_id(idb):
    ad = getattr(idb, "animation_data", None)
    return af._fcurves(ad.action) if ad and ad.action else []


class Face:
    def __init__(self, rig, auto_blink=True, seed=None):
        self.rig = rig
        pre = _base(rig.name) + "_"
        self.p = {}
        for o in rig.children:
            b = _base(o.name)
            if b.startswith(pre):
                self.p[b[len(pre):]] = o
        self.body = self.p.get("body")
        self.auto_blink = auto_blink
        self.seed = seed if seed is not None else sum(map(ord, rig.name))
        self.keys = []
        self.lips = {}
        self.chan = {}           # control -> [(id_block, data_path_owner, kind)]
        self._build()

    # ------------------------------------------------------------------ geometry
    def _rig_coords(self, ob):
        M = self.rig.matrix_world.inverted() @ ob.matrix_world
        return M, [M @ v.co for v in ob.data.vertices]

    def _add_keys(self, ob, M, fns):
        """fns: {key_name: fn(i, p_rig) -> rig-space delta Vector}"""
        me = ob.data
        if me.shape_keys is None:
            ob.shape_key_add(name="Basis", from_mix=False)
        Minv = M.inverted().to_3x3()
        base = [v.co.copy() for v in me.vertices]
        rc = [M @ c for c in base]
        out = {}
        for kname, fn in fns.items():
            kb = me.shape_keys.key_blocks.get(kname) or ob.shape_key_add(name=kname, from_mix=False)
            for i, p in enumerate(rc):
                kb.data[i].co = base[i] + Minv @ fn(i, p)
            kb.value = 0.0
            out[kname] = kb
        return out

    def _conform_eyes(self, scale=1.18):
        """The eye decals were originally ray-cast through the (masked) eyeball hole and sit ~34 mm inside the head.
        Re-project every decal vertex onto the front-most skin/eyeball surface (rig space, front = -Y), enlarged a
        little around each eye centre for anime readability."""
        from mathutils.bvhtree import BVHTree
        body = self.body
        if body is None:
            return
        me = body.data
        Mb = self.rig.matrix_world.inverted() @ body.matrix_world
        gidx = {body.vertex_groups[n].index for n in ("body", "helper-l-eye", "helper-r-eye") if n in body.vertex_groups}
        keep = np.zeros(len(me.vertices), bool)
        for v in me.vertices:
            for g in v.groups:
                if g.group in gidx and g.weight > 0.5:
                    keep[v.index] = True
                    break
        co = [Mb @ v.co for v in me.vertices]
        polys = [tuple(p.vertices) for p in me.polygons if all(keep[i] for i in p.vertices)]
        tree = BVHTree.FromPolygons(co, polys)
        self._tree = tree
        lift = {"sclera": 0.0010, "iris": 0.0023, "hl": 0.0032, "lash": 0.0034}
        # densify the triangle fans so they can follow the curved lids without cutting into each other
        import bmesh
        for side in ("L", "R"):
            for part in lift:
                ob = self.p.get(f"eye_{part}{side}")
                if ob is None or len(ob.data.vertices) > 120:
                    continue
                bm_ = bmesh.new()
                bm_.from_mesh(ob.data)
                bmesh.ops.subdivide_edges(bm_, edges=bm_.edges[:], cuts=2, use_grid_fill=True)
                bm_.to_mesh(ob.data)
                bm_.free()
        for side in ("L", "R"):
            sc = self.p.get(f"eye_sclera{side}")
            if sc is None:
                continue
            _, S = self._rig_coords(sc)
            c = sum(S, Vector()) / len(S)
            for part, lf in lift.items():
                ob = self.p.get(f"eye_{part}{side}")
                if ob is None:
                    continue
                M = self.rig.matrix_world.inverted() @ ob.matrix_world
                Minv = M.inverted()
                for v in ob.data.vertices:
                    p = M @ v.co
                    q = Vector((c.x + (p.x - c.x) * scale, -1.0, c.z + (p.z - c.z) * scale))
                    hit = tree.ray_cast(q, Vector((0, 1, 0)))
                    if hit[0] is None:
                        continue
                    v.co = Minv @ Vector((q.x, hit[0].y - lf, q.z))
                ob.data.update()
        bpy.context.view_layer.update()

    def _build(self):
        rig = self.rig
        old = rig.data.pose_position
        rig.data.pose_position = "REST"
        bpy.context.view_layer.update()
        self._conform_eyes()
        bpy.context.view_layer.update()
        self.x0 = rig.data.bones["head"].head_local.x
        self.kb = {c: [] for c in CONTROLS}       # control -> list of key blocks (value = control)
        self.kb_extra = {}                        # control -> [(key block, scale)]
        eye_h = []
        for side in ("L", "R"):
            sc = self.p.get(f"eye_sclera{side}")
            if sc is None:
                continue
            _, S = self._rig_coords(sc)
            ring = S
            c = sum(S, Vector()) / len(S)
            xmin, xmax = min(p.x for p in ring), max(p.x for p in ring)
            zmin, zmax = min(p.z for p in ring), max(p.z for p in ring)
            H, W = zmax - zmin, xmax - xmin
            eye_h.append(H)
            top, bot = _envelopes(S, xmin, xmax)
            inner = -1.0 if c.x > self.x0 else 1.0

            def e_of(p, c=c, W=W, inner=inner):
                return max(-1.0, min(1.0, (p.x - c.x) * inner / (W / 2)))

            def closed_z(x, c=c, W=W, zmin=zmin, H=H):
                xn = (x - c.x) / (W / 2)
                return zmin + 0.28 * H + 0.16 * H * xn * xn

            def upper_w(p, c=c, top=top):
                t = top(p.x)
                return max(0.0, min(1.0, (p.z - c.z) / max(1e-6, t - c.z)))

            def clampz(x, z, top=top, bot=bot, H=H):
                return max(bot(x) + 0.05 * H, min(top(x) - 0.05 * H, z))

            self._sparkle(side, sc)
            for part in ("sclera", "iris", "hl", "lash", "tear"):
                ob = self.p.get(f"eye_{part}{side}")
                if part == "tear":
                    ob = self._tear(side, sc)
                if ob is None:
                    continue
                M, P = self._rig_coords(ob)
                cen = sum(P, Vector()) / len(P)
                fns = {}
                if part in ("sclera", "iris"):
                    fns["blink"] = lambda i, p, cz=closed_z: Vector((0, 0, cz(p.x) - p.z))
                    fns["squint"] = lambda i, p, top=top: Vector((0, 0, max(0.0, top(p.x) - p.z) * 0.5))
                elif part == "hl":
                    fns["blink"] = lambda i, p, cen=cen: (cen - p) * 0.97 + Vector((0, 0, 0))
                    fns["squint"] = lambda i, p, top=top: Vector((0, 0, max(0.0, top(p.x) - p.z) * 0.45))
                    fns["hl_big"] = lambda i, p, cen=cen: Vector(((p.x - cen.x) * 0.35, 0, (p.z - cen.z) * 0.35))
                elif part == "lash":
                    fns["blink"] = lambda i, p, cz=closed_z, top=top: Vector((0, 0, cz(p.x) + 0.6 * (p.z - top(p.x)) - p.z))
                    fns["squint"] = lambda i, p, H=H: Vector((0, 0, -0.05 * H))
                if part != "tear":
                    fns["wide"] = lambda i, p, c=c: Vector(((p.x - c.x) * 0.10, 0, (p.z - c.z) * 0.24))
                    if part == "lash":
                        fns["lid_sad"] = lambda i, p, e=e_of, H=H: Vector((0, 0, 0.30 * H * e(p)))
                        fns["lid_angry"] = lambda i, p, e=e_of, H=H: Vector((0, 0, -0.34 * H * e(p)))
                    else:
                        fns["lid_sad"] = lambda i, p, e=e_of, H=H, uw=upper_w: Vector((0, 0, 0.30 * H * e(p) * uw(p)))
                        fns["lid_angry"] = lambda i, p, e=e_of, H=H, uw=upper_w: Vector((0, 0, -0.34 * H * e(p) * uw(p)))
                if part in ("iris", "hl"):
                    fns["look_x"] = lambda i, p, W=W, cl=clampz: Vector((0.26 * W / 2, 0, cl(p.x + 0.26 * W / 2, p.z) - p.z))
                    fns["look_y"] = lambda i, p, H=H, cl=clampz: Vector((0, 0, cl(p.x, p.z + 0.20 * H) - p.z))
                    fns["look_down"] = lambda i, p, H=H, cl=clampz: Vector((0, 0, cl(p.x, p.z - 0.22 * H) - p.z))
                if part == "tear":
                    fns["tears"] = lambda i, p, bot=bot, tz=self._tear_z: Vector((0, 0, tz[side][i] - p.z))
                kbs = self._add_keys(ob, M, fns)
                for k, kb in kbs.items():
                    if k in self.kb:
                        self.kb[k].append(kb)
                    else:
                        self.kb_extra.setdefault(k, []).append(kb)
        self.eye_H = sum(eye_h) / len(eye_h) if eye_h else 0.012
        self._brows()
        self._moustache()
        self._mouth()
        rig.data.pose_position = old
        bpy.context.view_layer.update()

    def _sparkle(self, side, sclera):
        """kirakira: a 4-point star highlight on the iris, collapsed to a point unless 'sparkle' is keyed"""
        iris = self.p.get(f"eye_iris{side}")
        if iris is None:
            return
        _, I = self._rig_coords(iris)
        ic = sum(I, Vector()) / len(I)
        ir = max((p - ic).length for p in I)
        front_y = min(p.y for p in I) - 0.0012
        c = Vector((ic.x - 0.28 * ir * (1 if ic.x > self.x0 else -1), front_y, ic.z + 0.32 * ir))
        L, w = 0.95 * ir, 0.16 * ir
        star = []
        for k in range(8):
            a = math.pi / 2 * (k // 2) + (math.pi / 4 if k % 2 else 0.0)
            r = L if k % 2 == 0 else w
            star.append(Vector((c.x + math.cos(a) * r * (1.0 if k % 4 == 0 else 0.75), c.y, c.z + math.sin(a) * r)))
        me = bpy.data.meshes.new(_base(self.rig.name) + f"_sparkle{side}")
        me.from_pydata([c] + star, [], [(0, 1 + k, 1 + (k + 1) % 8) for k in range(8)])
        ob = bpy.data.objects.new(_base(self.rig.name) + f"_eye_sparkle{side}", me)
        for col in iris.users_collection:
            col.objects.link(ob)
        ob.parent, ob.parent_type, ob.parent_bone = iris.parent, iris.parent_type, iris.parent_bone
        ob.matrix_parent_inverse = iris.matrix_parent_inverse.copy()
        ob.matrix_basis = iris.matrix_basis.copy()
        bpy.context.view_layer.update()
        M = self.rig.matrix_world.inverted() @ ob.matrix_world
        Minv = M.inverted()
        for v in me.vertices:                  # vertices were given in rig space: move them into local space
            v.co = Minv @ v.co
        mat = bpy.data.materials.get("AF_sparkle") or af.flat_mat("AF_sparkle", "#FFFFFF", strength=1.5)
        me.materials.append(mat)
        ob.visible_shadow = False
        base = [v.co.copy() for v in me.vertices]
        cen_local = base[0]
        ob.shape_key_add(name="Basis", from_mix=False)
        kb = ob.shape_key_add(name="sparkle", from_mix=False)
        for i, v in enumerate(me.shape_keys.key_blocks["Basis"].data):
            v.co = cen_local.copy()             # collapsed: invisible
        for i in range(len(base)):
            kb.data[i].co = base[i]
        kb.value = 0.0
        self.kb["sparkle"].append(kb)

    def _tear(self, side, sclera):
        """wet lower-lid crescent: a copy of the sclera collapsed onto its lower edge; key 'tears' opens it."""
        if not hasattr(self, "_tear_z"):
            self._tear_z = {}
        me = sclera.data.copy()
        me.name = sclera.data.name + "_tear"
        ob = bpy.data.objects.new(_base(self.rig.name) + f"_eye_tear{side}", me)
        for col in sclera.users_collection:
            col.objects.link(ob)
        ob.parent = sclera.parent
        ob.parent_type = sclera.parent_type
        ob.parent_bone = sclera.parent_bone
        ob.matrix_parent_inverse = sclera.matrix_parent_inverse.copy()
        ob.matrix_basis = sclera.matrix_basis.copy()
        if me.shape_keys:                      # the copy inherits the sclera's keys; the tear needs its own basis
            ob.shape_key_clear()
        bpy.context.view_layer.update()
        mat = bpy.data.materials.get("AF_tear") or af.flat_mat("AF_tear", "#A8D8EE", strength=0.5, alpha=0.45, blended=True)
        me.materials.clear()
        me.materials.append(mat)
        M, P = self._rig_coords(ob)
        ring = P
        c = sum(P, Vector()) / len(P)
        _, bot = _envelopes(P, min(p.x for p in P), max(p.x for p in P))
        H = max(p.z for p in ring) - min(p.z for p in ring)
        # nudge toward the camera so it sits over the iris, then collapse the basis onto the lower edge
        n = (self.rig.matrix_world.inverted().to_3x3() @ Vector((0, -1, 0))).normalized() * 0
        Minv = M.inverted()
        target = []
        for i, p in enumerate(P):
            zb = bot(p.x)
            target.append(zb + max(0.0, p.z - zb) * 0.30 - 0.02 * H)
            p2 = Vector((p.x, p.y - 0.0007, zb - 0.02 * H))
            me.vertices[i].co = Minv @ p2
        self._tear_z[side] = target
        self.p[f"eye_tear{side}"] = ob
        return ob

    def _brows(self):
        ob = self.p.get("brows")
        if ob is None:
            return
        M, P = self._rig_coords(ob)
        H = self.eye_H
        ext = {}
        for sgn in (-1, 1):
            ds = [abs(p.x - self.x0) for p in P if (p.x - self.x0) * sgn > 0]
            if ds:
                ext[sgn] = (min(ds), max(ds))

        def t_of(p):
            sgn = 1 if p.x > self.x0 else -1
            lo, hi = ext.get(sgn, (0, 1))
            return sgn, max(0.0, min(1.0, (abs(p.x - self.x0) - lo) / max(1e-6, hi - lo)))

        def up(i, p):
            s, t = t_of(p)
            return Vector((0, 0, 0.55 * H + 0.08 * H * math.sin(math.pi * t)))

        def down(i, p):
            s, t = t_of(p)
            return Vector((-s * 0.06 * H * (1 - t), 0, -0.36 * H))

        def sad(i, p):
            s, t = t_of(p)
            return Vector((-s * 0.04 * H * (1 - t), 0, 0.70 * H * (1 - t) ** 1.2 - 0.12 * H * t))

        def angry(i, p):
            s, t = t_of(p)
            return Vector((-s * 0.10 * H * (1 - t), 0, -0.52 * H * (1 - t) + 0.16 * H * t))
        kbs = self._add_keys(ob, M, {"brow_up": up, "brow_down": down, "brow_sad": sad, "brow_angry": angry})
        for k, kb in kbs.items():
            self.kb[k].append(kb)

    def _lips(self):
        body = self.body
        gi = body.vertex_groups["lips"].index
        M = self.rig.matrix_world.inverted() @ body.matrix_world
        idx = [v.index for v in body.data.vertices if any(g.group == gi and g.weight > 0.5 for g in v.groups)]
        P = {i: M @ body.data.vertices[i].co for i in idx}
        L = max(idx, key=lambda i: P[i].x)
        R = min(idx, key=lambda i: P[i].x)
        cx = (P[L].x + P[R].x) / 2
        mid = [i for i in idx if abs(P[i].x - cx) < 0.0045] or idx
        UP = max(mid, key=lambda i: P[i].z)
        LO = min(mid, key=lambda i: P[i].z)
        front = min(P[i].y for i in mid)
        return P[L], P[R], P[UP], P[LO], front

    def _moustache(self):
        ob = self.p.get("moustache")
        if ob is None or self.body is None:
            return
        Lc, Rc, up, lo, front = self._lips()
        s = (Lc.x - Rc.x) / 0.0548
        M, P = self._rig_coords(ob)
        half = max(abs(p.x - self.x0) for p in P) or 1.0

        def sm(i, p):
            t = min(1.0, abs(p.x - self.x0) / half)
            return Vector((0, 0, 0.0055 * s * t ** 1.5))

        def fr(i, p):
            t = min(1.0, abs(p.x - self.x0) / half)
            return Vector((0, 0, -0.0045 * s * t ** 1.5))
        kbs = self._add_keys(ob, M, {"smile": sm, "frown": fr})
        for k, kb in kbs.items():
            self.kb[k].append(kb)

    def _mouth(self):
        """dark mouth interior + upper teeth strip behind the lips (shown when the jaw opens)."""
        if self.body is None or "lips" not in self.body.vertex_groups:
            return
        Lc, Rc, up, lo, front = self._lips()
        mw = Lc.x - Rc.x
        cx = (Lc.x + Rc.x) / 2
        zc = (up.z + lo.z) / 2
        cy = (Lc.y + Rc.y) / 2 + 0.003
        pre = _base(self.rig.name)
        dark = bpy.data.materials.get("AF_mouth") or af.flat_mat("AF_mouth", "#2A0912", strength=1.0)
        teeth_m = bpy.data.materials.get("AF_teeth") or af.toon_mat("AF_teeth", "#D9D2DE", shadow="#6E6680", light="#F6F1FA",
                                                                   band=0.3, light_band=0.85)
        objs = []
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, radius=1.0)
        cav = bpy.context.active_object
        cav.name = pre + "_mouthcav"
        cav.data.materials.append(dark)
        rx, ry, rz = mw * 0.29, 0.010 * mw / 0.0548, (up.z - lo.z) * 0.58
        cy = (Lc.y + Rc.y) / 2 + ry + 0.0025          # its front stays behind the mouth corners (no dark patches on cheeks)
        cav.matrix_world = self.rig.matrix_world @ Matrix.Translation(Vector((cx, cy, zc - 0.15 * (up.z - lo.z)))) @ Matrix.Diagonal((rx, ry, rz, 1))
        objs.append(cav)
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        th = bpy.context.active_object
        th.name = pre + "_teeth"
        th.data.materials.append(teeth_m)
        tw, tt, td = mw * 0.5, (up.z - lo.z) * 0.2, 0.004
        th.matrix_world = self.rig.matrix_world @ Matrix.Translation(Vector((cx, front + 0.0105 * mw / 0.0548, zc + 0.05 * (up.z - lo.z)))) @ Matrix.Diagonal((tw, td, tt, 1))
        objs.append(th)
        for ob in objs:
            for col in list(ob.users_collection):
                col.objects.unlink(ob)
            for col in self.body.users_collection:
                col.objects.link(ob)
            ob.visible_shadow = False
            mw_ = ob.matrix_world.copy()
            ob.parent = self.rig
            ob.parent_type = "BONE"
            ob.parent_bone = "head"
            bpy.context.view_layer.update()
            pb = self.rig.pose.bones["head"]
            ob.matrix_parent_inverse = (self.rig.matrix_world @ pb.matrix @ Matrix.Translation(Vector((0, pb.length, 0)))).inverted()
            ob.matrix_world = mw_
        self.p["mouthcav"], self.p["teeth"] = cav, th

    def tear_drop(self, side, f0, dur=42):
        """one tear wells at the lower lid (f0) and rolls down the cheek on the skin, then is gone."""
        tree = getattr(self, "_tree", None)
        sc = self.p.get(f"eye_sclera{side}")
        if tree is None or sc is None:
            return
        rig = self.rig
        old = rig.data.pose_position
        rig.data.pose_position = "REST"
        bpy.context.view_layer.update()
        _, S = self._rig_coords(sc)
        c = sum(S, Vector()) / len(S)
        zmin = min(p.z for p in S)
        H = self.eye_H
        outward = 1.0 if c.x > self.x0 else -1.0
        path = []
        for i in range(9):
            t = i / 8
            x = c.x + outward * (0.18 * H + 0.35 * H * t)
            z = zmin - 0.12 * H - 3.0 * H * (t ** 1.3)
            hit = tree.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)))
            if hit[0] is None:
                continue
            path.append(Vector((x, hit[0].y - 0.0014, z)))
        if len(path) < 3:
            rig.data.pose_position = old
            return
        mat = bpy.data.materials.get("AF_teardrop") or af.flat_mat("AF_teardrop", "#9CD6F0", strength=0.7, alpha=0.75, blended=True)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=1.0)
        d = bpy.context.active_object
        d.name = _base(rig.name) + f"_teardrop{side}{f0}"
        d.data.materials.append(mat)
        d.visible_shadow = False
        for col in list(d.users_collection):
            col.objects.unlink(d)
        for col in self.body.users_collection:
            col.objects.link(d)
        r = 0.15 * H
        d.parent = rig
        d.parent_type = "BONE"
        d.parent_bone = "head"
        bpy.context.view_layer.update()
        pb = rig.pose.bones["head"]
        d.matrix_parent_inverse = (rig.matrix_world @ pb.matrix @ Matrix.Translation(Vector((0, pb.length, 0)))).inverted()
        locs = []
        for p in path:
            d.matrix_world = rig.matrix_world @ Matrix.Translation(p) @ Matrix.Diagonal((r * 0.85, r * 0.7, r * 2.1, 1))
            bpy.context.view_layer.update()
            locs.append(d.location.copy())
        full = d.scale.copy()
        rig.data.pose_position = old
        bpy.context.view_layer.update()
        tiny = full * 0.001
        # well up, hold, roll down (accelerating), vanish
        keys = [(f0 - 1, locs[0], tiny), (f0, locs[0], full * 0.45), (f0 + 8, locs[0], full)]
        for i, l in enumerate(locs[1:], 1):
            keys.append((f0 + 8 + int(dur * (i / (len(locs) - 1)) ** 0.8), l, full))
        keys.append((keys[-1][0] + 2, locs[-1], tiny))
        d.scale = tiny
        d.keyframe_insert("scale", frame=1)
        for f, l, s in keys:
            d.location = l
            d.scale = s
            d.keyframe_insert("location", frame=f)
            d.keyframe_insert("scale", frame=f)
        for fc in af.fcurves_of(d):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT" if fc.data_path == "scale" else "BEZIER"

    # ------------------------------------------------------------------ animation
    def key(self, frame, expr, trans=4):
        vals = dict(PRESETS[expr]) if isinstance(expr, str) else dict(expr)
        self.keys.append((frame, vals, trans))
        self.keys.sort(key=lambda k: k[0])

    def lipsync(self, wav_path, start_frame, gain=1.0, max_open=0.55, fps=24, step=2):
        with wave.open(wav_path) as w:
            sr = w.getframerate()
            x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
            if w.getnchannels() > 1:
                x = x.reshape(-1, w.getnchannels()).mean(axis=1)
        hop = sr / fps
        n = int(len(x) / hop)
        rms = np.array([np.sqrt(np.mean(x[int(i * hop):int((i + 1) * hop)] ** 2) + 1e-12) for i in range(n)])
        ref = np.percentile(rms[rms > rms.max() * 0.05], 90) if np.any(rms > rms.max() * 0.05) else rms.max()
        v = np.clip((rms / (ref + 1e-9)) ** 0.7 * gain, 0, 1)
        v[rms < rms.max() * 0.06] = 0.0
        for i in range(0, n, step):
            seg = v[i:i + step]
            self.lips[start_frame + i] = float(seg.max()) * max_open if len(seg) else 0.0
            for j in range(1, step):
                self.lips[start_frame + i + j] = self.lips[start_frame + i]
        self.lips[start_frame + n + 1] = 0.0

    def value_at(self, f):
        out = {c: 0.0 for c in CONTROLS}
        if not self.keys:
            return out
        prev = {}
        for kf, vals, trans in self.keys:
            if f >= kf:
                prev = vals
                continue
            if f >= kf - trans:
                t = (f - (kf - trans)) / max(1, trans)
                t = t * t * (3 - 2 * t)
                for c in CONTROLS:
                    out[c] = prev.get(c, 0.0) * (1 - t) + vals.get(c, 0.0) * t
                return out
            break
        for c in CONTROLS:
            out[c] = prev.get(c, 0.0)
        return out

    def _blink_overlay(self, f0, f1):
        r = random.Random(self.seed)
        ov = {}
        f = f0 + r.randint(10, 50)
        while f < f1 - 4:
            if self.value_at(f)["blink"] < 0.5:
                for d, v in ((0, 0.6), (1, 1.0), (2, 1.0), (3, 0.45)):
                    ov[f + d] = v
            f += r.randint(56, 110)
        return ov

    def bake(self, f0, f1):
        ov = self._blink_overlay(f0, f1) if self.auto_blink else {}
        last = {}
        mouth_bones = sorted({b for m in MOUTH.values() for b in m})
        rig = self.rig
        for pb in (rig.pose.bones.get(b) for b in mouth_bones):
            if pb:
                pb.rotation_mode = "XYZ"
        for f in range(f0, f1 + 1):
            v = self.value_at(f)
            v["blink"] = max(v["blink"], ov.get(f, 0.0))
            v["open"] = max(v["open"], self.lips.get(f, 0.0))
            # a closing lid overrides every other eye shape (shape keys add, so scale them out)
            for c_ in ("squint", "wide", "lid_sad", "lid_angry", "look_x", "look_y", "tears", "sparkle"):
                v[c_] *= (1.0 - v["blink"])
            for c_ in ("brow_up", "brow_down", "brow_sad", "brow_angry"):
                v[c_] = min(1.3, v[c_] * 1.25)
            look_dn = max(0.0, -v["look_y"])
            v["look_y"] = max(0.0, v["look_y"])
            ch = dict(v)
            ch["look_down"] = look_dn
            ch["hl_big"] = v["tears"]
            # shape keys
            for c, val in ch.items():
                for kb in self.kb.get(c, []) + self.kb_extra.get(c, []):
                    k = (kb.id_data.name, kb.name)
                    if f == f0 or abs(last.get(k, -9) - val) > 1e-4:
                        kb.value = val
                        kb.keyframe_insert("value", frame=f)
                        last[k] = val
            # upper teeth only exist while the mouth is really open (the neutral MPFB lips are slightly parted)
            th = self.p.get("teeth")
            if th is not None:
                if not hasattr(self, "_teeth_scale"):
                    self._teeth_scale = th.scale.copy()
                vis = v["open"] > 0.14
                k = ("teeth", "vis")
                if f == f0 or last.get(k) != vis:
                    th.scale = self._teeth_scale if vis else Vector((self._teeth_scale.x, self._teeth_scale.y, self._teeth_scale.z * 0.001))
                    th.keyframe_insert("scale", frame=f)
                    last[k] = vis
                    for fc in af.fcurves_of(th):
                        for kp in fc.keyframe_points:
                            kp.interpolation = "CONSTANT"
            # mouth bones
            rot = {b: [0.0, 0.0, 0.0] for b in mouth_bones}
            for c, bones in MOUTH.items():
                for b, e in bones.items():
                    for a in range(3):
                        rot[b][a] += e[a] * v[c]
            for b, e in rot.items():
                pb = rig.pose.bones.get(b)
                if pb is None:
                    continue
                k = ("bone", b)
                tup = tuple(round(x, 3) for x in e)
                if f == f0 or last.get(k) != tup:
                    pb.rotation_euler = [math.radians(x) for x in e]
                    pb.keyframe_insert("rotation_euler", frame=f)
                    last[k] = tup
        # constant interpolation everywhere we keyed (anime holds)
        keys_ids = {kb.id_data for lst in list(self.kb.values()) + list(self.kb_extra.values()) for kb in lst}
        for idb in keys_ids:
            for fc in _fcurves_id(idb):
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
        for fc in af.fcurves_of(rig):
            if any(fc.data_path == f'pose.bones["{b}"].rotation_euler' for b in mouth_bones):
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"


REGISTRY = {}


def get(name):
    return REGISTRY[name]


def bake_all(f0, f1):
    for F in REGISTRY.values():
        if not getattr(F, "_baked", False):
            F.bake(f0, f1)
            F._baked = True
