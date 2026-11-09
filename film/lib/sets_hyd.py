# ALWAYS FALLING — Hyderabad Old City rooftop + neighbourhood set
import bpy, bmesh, math, random
from mathutils import Vector
import af
from af import hexc, box, plane, cylinder, ico, uv_sphere, mesh_obj, add_outline, toon_mat, flat_mat

LANE_Z = -6.4          # lane level; hero terrace floor is z = 0
HERO = dict(x0=-4.5, x1=4.5, y0=-5.5, y1=5.5)

PALETTES = {
    "night": dict(
        sky=[(-1.0, "#120A26"), (-0.01, "#E07A6A"), (0.02, "#B0568A"), (0.07, "#4C46A0"), (0.18, "#232E8E"), (0.45, "#141A60"), (1.0, "#0A0A32")],
        ambient="#2A2A6A", amb=0.75, key_dir=(-0.55, 0.6, -0.45), key_col="#A8D8FF", key_e=2.4,
        stars=dict(density=0.07, size=0.075, scale=240, bright=5.5, color="#F0F4FF"),
        walls=[("#8A4E96", "#3A2050", "#C482D6"), ("#2E7A92", "#14384E", "#62B6D0"), ("#9A8450", "#463A2A", "#D8C07C"),
               ("#3E8A78", "#1A3E3A", "#76C8B0"), ("#5E5EAE", "#282C58", "#9A9AE6")],
        concrete=("#4E5690", "#22264C", "#8890D0"), wood=("#4A3450", "#201628", "#76567E"),
        rope=("#6E6290", "#302A4C", "#A496C8"), cloth=[("#E05A7A", "#6A2448", "#FF9AB0"), ("#F2C04A", "#7A5A30", "#FFE48A"), ("#4AC0D8", "#1E5A78", "#9AE8FF")],
        leaf=("#1E5A56", "#0C2428", "#3E9A84"), trunk=("#2A2A48", "#10101E", "#46467A"),
        far1="#3A3E86", far2="#2C2E6E", far3="#1E2054", farwin="#FFC46A", win="#FFB858", win_e=3.2,
        clay=("#A05A50", "#4A2434", "#D88A6E"), flower=("#E0408E", "#6E1A4C", "#FF7AC0"),
        outline="#0A0A22", wire="#08081A", lamp="#FFC27A"),
    "dusk": dict(
        sky=[(-1.0, "#2A1E3A"), (-0.02, "#FF9A5A"), (0.04, "#FFB27A"), (0.12, "#D47A8E"), (0.3, "#7A4F8C"), (0.6, "#2E2E6A"), (1.0, "#141A44")],
        ambient="#5A4070", amb=0.7, key_dir=(0.8, 0.45, -0.18), key_col="#FFC48A", key_e=3.2,
        stars=dict(density=0.02, size=0.05, scale=240, bright=1.5, color="#FFE8D0"),
        walls=[("#C98F7A", "#6A4060", "#F2C49A"), ("#B99AA8", "#5C4468", "#E8C6C0"), ("#D2A57A", "#704A5A", "#F6CE98"),
               ("#C4A38E", "#5E4460", "#F0D0AC"), ("#B8867A", "#5A3A58", "#E8B694")],
        concrete=("#A07C80", "#523A5A", "#D8AE9A"), wood=("#5A3A40", "#2A1A24", "#8A5E58"),
        rope=("#9A7A70", "#4A3448", "#CCA690"), cloth=[("#6A8AC8", "#3A4478", "#9CB8E8"), ("#C85A6A", "#682A48", "#F08A8A"), ("#F0E6D8", "#9A8098", "#FFFFFF")],
        leaf=("#3A4A3A", "#1C2230", "#6A7A50"), trunk=("#3A2A2A", "#1A1218", "#5E4440"),
        far1="#8A5A78", far2="#6A4468", far3="#4E3458", farwin="#FFD08A", win="#FFC27A", win_e=1.5,
        clay=("#B0705A", "#5A3448", "#E09A78"), flower=("#D0408A", "#701E50", "#FF70B0"),
        outline="#1A0E1E", wire="#1A0E1E", lamp="#FFD9A0"),
    "day": dict(
        sky=[(-1.0, "#7FA9C9"), (0.0, "#E8E2D0"), (0.06, "#BFD6E8"), (0.3, "#7FB0DE"), (1.0, "#3F78C0")],
        ambient="#8AA0C0", amb=0.9, key_dir=(0.5, 0.7, -0.55), key_col="#FFF0D8", key_e=3.5,
        stars=None,
        walls=[("#E8D9A8", "#8A8098", "#FFF4D0"), ("#C8DCC8", "#6E8494", "#ECFAEA"), ("#EAC8C0", "#8A7890", "#FFE6DE"),
               ("#E6E2D6", "#888AA0", "#FFFFFF"), ("#D8C0A0", "#7E7090", "#F6E0C0")],
        concrete=("#BDB4A6", "#6E6E84", "#E2DCD0"), wood=("#7A4E36", "#3E2A2E", "#A86E4A"),
        rope=("#B8A080", "#6A5A62", "#E0CCA6"), cloth=[("#5A7EC0", "#33467A", "#8AAEE6"), ("#D05A6A", "#6E2E4A", "#F68E8E"), ("#F4F0E6", "#9A98AA", "#FFFFFF")],
        leaf=("#4E7A3A", "#28403A", "#7EA850"), trunk=("#5A4232", "#2E2228", "#80624A"),
        far1="#A8B8C8", far2="#90A4B8", far3="#7A90A8", farwin="#E0D8C8", win="#202838", win_e=1.0,
        clay=("#B8704E", "#64404A", "#E09A70"), flower=("#D83A8A", "#7A1E52", "#FF6AB0"),
        outline="#1A1420", wire="#1A1A24", lamp="#FFF2D0"),
}


def T(name, trip, rim=None, band=0.32):
    return toon_mat(name, trip[0], shadow=trip[1], light=trip[2], band=band, light_band=0.78, rim=rim, rim_th=0.6)


class Hyd:
    def __init__(self, time="night", seed=7, year=1975):
        self.time = time
        self.P = PALETTES[time]
        self.rnd = random.Random(seed)
        self.year = year
        P = self.P
        self.m_walls = [T(f"wall{i}_{time}", w) for i, w in enumerate(P["walls"])]
        self.m_conc = T("concrete_" + time, P["concrete"])
        self.m_floor = self.floor_mat()
        self.m_wood = T("wood_" + time, P["wood"])
        self.m_rope = T("rope_" + time, P["rope"])
        self.m_cloth = [T(f"cloth{i}_{time}", c) for i, c in enumerate(P["cloth"])]
        self.m_leaf = T("leaf_" + time, P["leaf"], band=0.38)
        self.m_trunk = T("trunk_" + time, P["trunk"])
        self.m_clay = T("clay_" + time, P["clay"])
        self.m_flower = T("flower_" + time, P["flower"])
        self.m_win = flat_mat("window_" + time, P["win"], strength=P["win_e"])
        self.m_dark = flat_mat("dark_" + time, "#0A1020" if time != "day" else "#2A2A36")
        self.m_far = [flat_mat(f"far{i}_{time}", P[k]) for i, k in enumerate(("far1", "far2", "far3"))]
        self.m_farwin = flat_mat("farwin_" + time, P["farwin"], strength=2.2 if time != "day" else 1.0)
        self.m_wire = flat_mat("wire_" + time, P["wire"])
        self.m_lamp = flat_mat("lamp_" + time, P["lamp"], strength=6.0)
        self.objs = []


    def floor_mat(self):
        P = self.P
        def tex(nt):
            tc = af.N(nt, "ShaderNodeTexCoord")
            br = af.N(nt, "ShaderNodeTexBrick")
            af.L(nt, af.O(tc, "Object"), af.I(br, "Vector"))
            af.I(br, "Scale").default_value = 1.6
            af.I(br, "Mortar Size").default_value = 0.012
            af.I(br, "Color1").default_value = (1, 1, 1, 1)
            af.I(br, "Color2").default_value = (0.9, 0.9, 0.92, 1)
            af.I(br, "Mortar").default_value = (0.62, 0.62, 0.7, 1)
            br.offset = 0.0
            return af.O(br, "Color")
        return toon_mat("floor_" + self.time, P["concrete"][0], shadow=P["concrete"][1], light=P["concrete"][2], band=0.32, light_band=0.78, tex_sock_fn=tex)

    def sky_dressing(self, moon_dir=None, moon_size=14.0, clouds=True, cloud_seed=3):
        P = self.P
        if self.time == "night":
            md = Vector(moon_dir) if moon_dir else -Vector(P["key_dir"])
            md.normalize()
            af.moon("moon", md * 400, moon_size, cam_dir=-md)
        if clouds and self.time != "day":
            cm = T("cloud_" + self.time, ("#6A4CA6", "#2E2266", "#D08ACC") if self.time == "night" else ("#F0A8A0", "#B0708E", "#FFE0B8"),
                   rim="#9FE8FF" if self.time == "night" else "#FFE8C8", band=0.3)
            rnd = random.Random(cloud_seed)
            for i in range(7):
                ang = rnd.uniform(-1.2, 1.2) + (math.pi / 2)
                dist = rnd.uniform(380, 650)
                c = Vector((math.cos(ang) * dist, math.sin(ang) * dist, rnd.uniform(25, 90)))
                cl = af.cumulus(f"cloud{i}", c, size=(rnd.uniform(70, 150), rnd.uniform(30, 50), rnd.uniform(26, 44)), puffs=30, seed=cloud_seed * 10 + i, mat=cm)
                cl.rotation_euler = (0, 0, ang + math.pi / 2)

    # -------------------------------------------------------------- environment
    def sky(self):
        P = self.P
        af.sky_world(P["sky"], ambient=P["ambient"], ambient_strength=P["amb"], stars=P["stars"],
                     milky=dict(axis=(0.35, 0.75, 0.55), width=0.22, bright=0.42, color="#C8A0F0") if self.time == "night" else None,
                     horizon_fade=(0.02, 0.22))
        af.add_sun("key", P["key_dir"], P["key_col"], energy=P["key_e"], angle=1.0)

    def ol(self, ob, t=0.03):
        add_outline(ob, t, self.P["outline"])
        return ob

    # -------------------------------------------------------------- house block
    def house(self, name, x0, x1, y0, y1, roof_z, front="-y", hero=False, props=True):
        rnd = self.rnd
        P = self.P
        wm = self.m_walls[rnd.randrange(len(self.m_walls))] if not hero else self.m_walls[0]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        w, d = x1 - x0, y1 - y0
        h = roof_z - LANE_Z
        b = box(name, (w, d, h), (cx, cy, LANE_Z + h / 2), wm)
        self.ol(b, 0.04)
        # parapet
        ph = rnd.uniform(0.8, 1.0) if not hero else 0.95
        t = 0.2
        for i, (sz, lc) in enumerate([((w, t, ph), (cx, y0 + t / 2, roof_z + ph / 2)), ((w, t, ph), (cx, y1 - t / 2, roof_z + ph / 2)),
                                      ((t, d - 2 * t, ph), (x0 + t / 2, cy, roof_z + ph / 2)), ((t, d - 2 * t, ph), (x1 - t / 2, cy, roof_z + ph / 2))]):
            p = box(f"{name}_par{i}", sz, lc, wm if not hero else self.m_conc)
            self.ol(p, 0.02)
        # cornice band under parapet (Old City detail)
        cor = box(f"{name}_cornice", (w + 0.16, d + 0.16, 0.14), (cx, cy, roof_z - 0.1), wm)
        self.ol(cor, 0.015)
        # windows on the front facade
        floors = max(1, int(round(h / 3.2)))
        fy = y0 - 0.02 if front == "-y" else y1 + 0.02
        rot = (math.radians(90), 0, 0) if front == "-y" else (math.radians(90), 0, math.radians(180))
        nwin = max(1, int(w / 2.6))
        for f in range(floors):
            zc = LANE_Z + 3.2 * f + 1.9
            for k in range(nwin):
                xc = x0 + (k + 0.5) * w / nwin
                lit = (self.time == "night" and rnd.random() < 0.45) or (self.time == "dusk" and rnd.random() < 0.22)
                mat = self.m_win if lit else self.m_dark
                pw, ph_ = 0.8, 1.15
                # arched top window = rect + small arch quad
                plane(f"{name}_w{f}_{k}", pw, ph_, (xc, fy, zc), rot, mat)
                plane(f"{name}_wa{f}_{k}", pw * 0.7, 0.25, (xc, fy, zc + ph_ / 2 + 0.12), rot, mat)
                if lit:
                    pass
        if props and not hero:
            self.roof_props(name, x0, x1, y0, y1, roof_z)
        return b

    def roof_props(self, name, x0, x1, y0, y1, z):
        rnd = self.rnd
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        r = rnd.random()
        if r < 0.45:   # stair room
            sx = rnd.uniform(x0 + 1.4, x1 - 1.4)
            sy = rnd.uniform(y0 + 1.4, y1 - 1.4)
            sr = box(f"{name}_stair", (2.2, 2.2, 2.3), (sx, sy, z + 1.15), self.m_walls[rnd.randrange(len(self.m_walls))])
            self.ol(sr, 0.025)
        if rnd.random() < 0.4:   # water tank
            tx = rnd.uniform(x0 + 1.0, x1 - 1.0)
            ty = rnd.uniform(y0 + 1.0, y1 - 1.0)
            tk = cylinder(f"{name}_tank", 0.65, 1.2, (tx, ty, z + 0.6 + 0.3), self.m_conc, 16)
            self.ol(tk, 0.02)
        if rnd.random() < 0.35:  # clothesline
            self.clothesline(f"{name}_line", Vector((x0 + 0.4, cy + rnd.uniform(-1, 1), z + 1.7)), Vector((x1 - 0.4, cy + rnd.uniform(-1, 1), z + 1.7)), n=rnd.randint(2, 5))
        if self.time == "night" and rnd.random() < 0.15:  # someone's charpai
            self.charpai(f"{name}_charpai", Vector((rnd.uniform(x0 + 1.5, x1 - 1.5), rnd.uniform(y0 + 1.5, y1 - 1.5), z)), rnd.uniform(0, math.pi))

    # -------------------------------------------------------------- props
    def charpai(self, name, loc, rot=0.0, bedding=True):
        """Rope cot: 1.95 x 0.95 m frame, 0.42 m high, woven rope surface."""
        L, W, H = 1.95, 0.95, 0.42
        parts = []
        fr = self.m_wood
        for sx in (-1, 1):
            parts.append(box(f"{name}_rail{sx}", (L, 0.06, 0.07), (0, sx * (W / 2 - 0.03), H), fr))
        for sy in (-1, 1):
            parts.append(box(f"{name}_end{sy}", (0.06, W, 0.07), (sy * (L / 2 - 0.03), 0, H), fr))
        for sx in (-1, 1):
            for sy in (-1, 1):
                parts.append(cylinder(f"{name}_leg{sx}{sy}", 0.04, H + 0.04, (sy * (L / 2 - 0.05), sx * (W / 2 - 0.05), (H + 0.04) / 2), fr, 10, r2=0.032))
        # woven surface: material with a diagonal weave pattern
        m, nt = af.new_mat(name + "_weave")
        tc = af.N(nt, "ShaderNodeTexCoord")
        mp = af.N(nt, "ShaderNodeMapping")
        af.I(mp, "Rotation").default_value = (0, 0, math.radians(45))
        af.I(mp, "Scale").default_value = (28, 28, 1)
        af.L(nt, af.O(tc, "Object"), af.I(mp, "Vector"))
        ck = af.N(nt, "ShaderNodeTexChecker")
        af.L(nt, af.O(mp, "Vector"), af.I(ck, "Vector"))
        af.I(ck, "Color1").default_value = (1, 1, 1, 1)
        af.I(ck, "Color2").default_value = (0.72, 0.72, 0.72, 1)
        # toon
        dif = af.N(nt, "ShaderNodeBsdfDiffuse")
        s2r = af.N(nt, "ShaderNodeShaderToRGB")
        bw = af.N(nt, "ShaderNodeRGBToBW")
        af.L(nt, af.O(dif, "BSDF"), af.I(s2r, "Shader"))
        af.L(nt, af.O(s2r, "Color"), af.I(bw, "Color"))
        rp = af.ramp(nt, [(0.0, self.P["rope"][1]), (0.32, self.P["rope"][0]), (0.78, self.P["rope"][2])], "CONSTANT", fac=af.O(bw, "Val"))
        col = af.mixcol(nt, 1.0, af.O(rp, "Color"), af.O(ck, "Color"), "MULTIPLY")
        af.finish_emission(m, nt, col)
        surf = plane(f"{name}_rope", L - 0.1, W - 0.1, (0, 0, H - 0.01), mat=m)
        sag = surf.modifiers.new("sub", "SUBSURF")
        sag.levels = sag.render_levels = 2
        parts.append(surf)
        if bedding:
            # thin mattress / sheet and a pillow
            sheet = box(f"{name}_sheet", (1.7, 0.8, 0.05), (0.05, 0, H + 0.03), self.m_cloth[2], bevel=0.02)
            pil = box(f"{name}_pillow", (0.32, 0.55, 0.12), (-0.72, 0, H + 0.1), self.m_cloth[2], bevel=0.05)
            parts += [sheet, pil]
        root = bpy.data.objects.new(name, None)
        af.link(root)
        for p in parts:
            p.parent = root
            if p.type == "MESH" and p.name.endswith(("rail-1", "rail1", "end-1", "end1")):
                self.ol(p, 0.012)
        root.location = loc
        root.rotation_euler = (0, 0, rot)
        return root

    def clothesline(self, name, a, b, n=4, sag=0.25):
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.008
        sp = cu.splines.new("POLY")
        N_ = 12
        sp.points.add(N_ - 1)
        for i in range(N_):
            t = i / (N_ - 1)
            p = a.lerp(b, t) - Vector((0, 0, sag * 4 * t * (1 - t)))
            sp.points[i].co = (p.x, p.y, p.z, 1)
        ob = af.link(bpy.data.objects.new(name, cu))
        cu.materials.append(self.m_wire)
        for k in range(n):
            t = (k + 1) / (n + 1) + self.rnd.uniform(-0.05, 0.05)
            p = a.lerp(b, t) - Vector((0, 0, sag * 4 * t * (1 - t)))
            cw, ch = self.rnd.uniform(0.5, 1.0), self.rnd.uniform(0.6, 1.1)
            d = (b - a).normalized()
            cl = plane(f"{name}_c{k}", cw, ch, p - Vector((0, 0, ch / 2)), (math.radians(90), 0, math.atan2(d.y, d.x)), self.m_cloth[self.rnd.randrange(3)])
            wv = cl.modifiers.new("sub", "SUBSURF")
            wv.subdivision_type = "SIMPLE"
            wv.levels = wv.render_levels = 4
            w = cl.modifiers.new("Wave", "WAVE")
            w.use_normal = True
            w.height, w.width, w.speed = 0.03, 0.5, 0.03
            w.time_offset = self.rnd.uniform(-50, 0)
            self.ol(cl, 0.008)
        return ob

    def matka(self, name, loc):
        me = bpy.data.meshes.new(name)
        bm_ = bmesh.new()
        prof = [(0.0, 0.0), (0.12, 0.01), (0.2, 0.08), (0.22, 0.16), (0.2, 0.26), (0.12, 0.33), (0.08, 0.36), (0.1, 0.4), (0.0, 0.4)]
        segs = 24
        rings = []
        for (r, z) in prof:
            ring = [bm_.verts.new((r * math.cos(2 * math.pi * s / segs), r * math.sin(2 * math.pi * s / segs), z)) for s in range(segs)]
            rings.append(ring)
        for i in range(len(rings) - 1):
            for s in range(segs):
                bm_.faces.new((rings[i][s], rings[i][(s + 1) % segs], rings[i + 1][(s + 1) % segs], rings[i + 1][s]))
        bm_.to_mesh(me)
        bm_.free()
        ob = af.link(bpy.data.objects.new(name, me))
        me.materials.append(self.m_clay)
        for p in me.polygons:
            p.use_smooth = True
        ob.location = loc
        self.ol(ob, 0.01)
        return ob

    def pigeon_loft(self, name, loc, rot=0.0):
        root = bpy.data.objects.new(name, None)
        af.link(root)
        parts = [box(name + "_box", (1.4, 0.8, 0.9), (0, 0, 1.45), self.m_wood)]
        for sx in (-1, 1):
            for sy in (-1, 1):
                parts.append(box(f"{name}_post{sx}{sy}", (0.07, 0.07, 1.0), (sx * 0.62, sy * 0.33, 0.5), self.m_wood))
        parts.append(box(name + "_roof", (1.6, 1.0, 0.06), (0, 0, 1.95), self.m_wood, rot=(math.radians(8), 0, 0)))
        for k in range(4):
            parts.append(plane(f"{name}_hole{k}", 0.18, 0.2, (-0.45 + k * 0.3, -0.41, 1.5), (math.radians(90), 0, 0), self.m_dark))
        for p in parts:
            p.parent = root
            self.ol(p, 0.012)
        root.location = loc
        root.rotation_euler = (0, 0, rot)
        return root

    def bougainvillea(self, name, loc, spread=1.4, seed=1):
        rnd = random.Random(seed)
        pot = self.matka(name + "_pot", loc)
        pot.scale = (1.2, 1.2, 0.9)
        bush, _ = af.tree_blob(name + "_leaves", loc + Vector((0, 0, 0.05)), radius=spread * 0.45, blobs=7, seed=seed, mat=self.m_leaf, trunk_h=0.0, squash=0.7)
        flw, _ = af.tree_blob(name + "_flowers", loc + Vector((0.1, -0.05, 0.12)), radius=spread * 0.38, blobs=6, seed=seed + 9, mat=self.m_flower, trunk_h=0.0, squash=0.6)
        self.ol(bush, 0.012)
        return bush

    def antenna(self, name, loc):
        parts = [cylinder(name + "_mast", 0.025, 3.2, loc + Vector((0, 0, 1.6)), self.m_wire, 8)]
        boom = cylinder(name + "_boom", 0.018, 1.6, loc + Vector((0, 0, 3.1)), self.m_wire, 8)
        boom.rotation_euler = (math.radians(90), 0, 0)
        parts.append(boom)
        for k in range(7):
            el = cylinder(f"{name}_el{k}", 0.01, 1.1 - k * 0.07, loc + Vector((0, -0.7 + k * 0.23, 3.1)), self.m_wire, 6)
            el.rotation_euler = (0, math.radians(90), 0)
            parts.append(el)
        return parts

    def bulb(self, name, loc, energy=60.0, color=None):
        b = ico(name, 0.05, loc, self.m_lamp, sub=2)
        af.add_point(name + "_light", loc, color or self.P["lamp"], energy=energy, radius=0.05)
        return b

    def wire(self, name, a, b, sag=0.6):
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.012
        sp = cu.splines.new("POLY")
        N_ = 16
        sp.points.add(N_ - 1)
        a, b = Vector(a), Vector(b)
        for i in range(N_):
            t = i / (N_ - 1)
            p = a.lerp(b, t) - Vector((0, 0, sag * 4 * t * (1 - t)))
            sp.points[i].co = (p.x, p.y, p.z, 1)
        ob = af.link(bpy.data.objects.new(name, cu))
        cu.materials.append(self.m_wire)
        return ob

    # -------------------------------------------------------------- hero house
    def hero(self):
        H = HERO
        house = self.house("hero", H["x0"], H["x1"], H["y0"], H["y1"], 0.0, hero=True, props=False)
        floor = box("hero_floor", (H["x1"] - H["x0"] - 0.4, H["y1"] - H["y0"] - 0.4, 0.06), (0, 0, 0.03), self.m_floor)
        # stair room at back-left with a door and a bulb
        sr = box("hero_stair", (2.4, 2.6, 2.4), (-2.9, 3.8, 1.2), self.m_walls[0])
        self.ol(sr, 0.025)
        door = box("hero_stair_door", (0.9, 0.06, 1.95), (-2.9 + 0.2, 3.8 - 1.31, 0.98), self.m_wood)
        self.ol(door, 0.012)
        self.bulb("hero_bulb", Vector((-2.9 + 0.2, 3.8 - 1.38, 2.1)), energy=45.0 if self.time == "night" else 10.0)
        tank = cylinder("hero_tank", 0.7, 1.3, (-2.9, 3.8, 2.4 + 0.65), self.m_conc, 18)
        self.ol(tank, 0.02)
        self.matka("hero_matka", Vector((3.6, -4.6, 0.06)))
        self.pigeon_loft("hero_loft", Vector((3.2, 4.1, 0.0)), math.radians(180))
        self.bougainvillea("hero_bougain", Vector((-3.8, -4.7, 0.06)), seed=3)
        self.bougainvillea("hero_bougain2", Vector((3.9, 1.0, 0.06)), seed=8)
        self.clothesline("hero_line", Vector((-4.2, 1.2, 1.75)), Vector((1.8, 4.9, 1.75)), n=4)
        if self.year >= 1979:
            self.antenna("hero_antenna", Vector((-3.6, 4.6, 2.4)))
        # front door in the lane (wooden double door, frame, step, chain knocker)
        dz = LANE_Z
        fr = box("hero_doorframe", (1.6, 0.25, 2.5), (1.4, H["y0"] - 0.05, dz + 1.25), self.m_conc)
        self.ol(fr, 0.02)
        for s in (-1, 1):
            leaf = box(f"hero_doorleaf{s}", (0.64, 0.08, 2.2), (1.4 + s * 0.33, H["y0"] - 0.12, dz + 1.15), self.m_wood)
            self.ol(leaf, 0.01)
        step = box("hero_step", (1.9, 0.6, 0.18), (1.4, H["y0"] - 0.35, dz + 0.09), self.m_conc)
        return house

    # -------------------------------------------------------------- neighbourhood
    def neighbourhood(self, radius=70, lane_y=(-8.5, -5.5)):
        rnd = self.rnd
        # rows of houses: along x, rows separated by lanes
        rows = [(-5.5, 5.5, "-y"), (5.5, 16.5, "+y"), (-19.5, -8.5, "+y"), (19.5, 30.5, "-y"), (30.5, 41.5, "+y"),
                (-32.5, -21.5, "-y"), (44.5, 56.5, "-y"), (-46.5, -35.5, "+y"), (59.5, 70.5, "-y")]
        for ri, (y0, y1, front) in enumerate(rows):
            x = -radius
            while x < radius:
                w = rnd.uniform(6.0, 10.5)
                x0, x1 = x, x + w
                x = x1
                if ri == 0 and x1 > HERO["x0"] - 0.01 and x0 < HERO["x1"] + 0.01:
                    continue
                if ri == 0 and x0 < HERO["x0"] < x1:
                    x1 = HERO["x0"]
                if ri == 0 and x0 < HERO["x1"] < x1:
                    x0 = HERO["x1"]
                near = abs((x0 + x1) / 2) < 16 and ri in (0, 1, 2)
                floors = rnd.choice([1, 2, 2]) if near else rnd.choice([1, 2, 2, 2, 3, 3, 4])
                rz = LANE_Z + floors * 3.2
                self.house(f"h{ri}_{int(x0)}", x0, x1, y0, y1, rz, front=front)
        # lane ground
        g = box("lane_ground", (2 * radius, 160, 0.2), (0, 0, LANE_Z - 0.1), self.m_conc)

    def trees(self, n=14):
        rnd = self.rnd
        spots = [(-14, 13), (12, 24), (-26, 36), (24, -14), (-9, -27), (34, 28), (-38, 9), (40, -3), (5, 47), (-20, -40), (16, 60), (-44, 52), (52, 40), (-6, 30)]
        for i, (x, y) in enumerate(spots[:n]):
            tr, tk = af.tree_blob(f"neem{i}", (x, y, LANE_Z), radius=rnd.uniform(3.0, 5.0), blobs=10, seed=i + 20,
                                  mat=self.m_leaf, trunk_mat=self.m_trunk, trunk_h=rnd.uniform(5.0, 8.0))
            self.ol(tr, 0.04)
        palms = [(18, 8), (-30, 22), (8, -22), (-17, 50)]
        for i, (x, y) in enumerate(palms):
            af.palm(f"hpalm{i}", (x, y, LANE_Z), rnd.uniform(13, 17), (rnd.uniform(-0.15, 0.15), rnd.uniform(-0.1, 0.1)), 0.1, 16, 3.6, seed=i + 40,
                    trunk_mat=self.m_trunk, frond_mat=self.m_leaf)

    # -------------------------------------------------------------- skyline (far, silhouettes)
    def minaret(self, name, x, y, z0, h=40.0, r=1.6, mat=None):
        mat = mat or self.m_far[1]
        parts = [cylinder(name + "_shaft", r, h, (x, y, z0 + h / 2), mat, 16, r2=r * 0.8)]
        for k, fz in enumerate((0.6, 0.82)):
            parts.append(cylinder(f"{name}_bal{k}", r * 1.45, 0.6, (x, y, z0 + h * fz), mat, 16))
        parts.append(cylinder(name + "_kiosk", r * 0.9, 3.0, (x, y, z0 + h + 1.5), mat, 12))
        dome = uv_sphere(name + "_dome", r * 1.15, (x, y, z0 + h + 3.6), mat, 16, 10)
        dome.scale = (1, 1, 1.35)
        fin = cylinder(name + "_fin", 0.12, 2.2, (x, y, z0 + h + 6.2), mat, 6)
        return parts + [dome, fin]

    def charminar(self, cx, cy, s=1.0, mat=None):
        """Recognisable silhouette: square arched base, upper arcade, four minarets with balconies and domes."""
        mat = mat or self.m_far[0]
        S = 20.0 * s
        z0 = LANE_Z

        def arch_face(name, rot):
            # outer rectangle with pointed-arch opening (concave n-gon)
            hw, top, spring, apex, ow = S / 2, 24 * s, 13.5 * s, 19.0 * s, 5.4 * s
            pts = [(-hw, 0), (-ow, 0), (-ow, spring)]
            for i in range(1, 12):
                t = i / 12
                ang = math.pi * t
                xx = -ow * math.cos(ang)
                zz = spring + (apex - spring) * math.sin(ang) ** 0.75
                pts.append((xx, zz))
            pts += [(ow, spring), (ow, 0), (hw, 0), (hw, top), (-hw, top)]
            v = [(px, 0, pz) for px, pz in pts]
            ob = mesh_obj(name, v, [list(range(len(v)))], mat)
            so = ob.modifiers.new("thick", "SOLIDIFY")
            so.thickness = 2.4 * s
            ob.rotation_euler = (0, 0, rot)
            return ob
        faces = []
        for k, (dx, dy, rot) in enumerate([(0, -S / 2, 0), (S / 2, 0, math.pi / 2), (0, S / 2, math.pi), (-S / 2, 0, -math.pi / 2)]):
            f = arch_face(f"charminar_face{k}", rot)
            f.location = (cx + dx, cy + dy, z0)
            faces.append(f)
        box("charminar_gallery", (S + 2 * s, S + 2 * s, 1.4 * s), (cx, cy, z0 + 24.7 * s), mat)
        box("charminar_upper", (S - 1 * s, S - 1 * s, 6.5 * s), (cx, cy, z0 + 28.6 * s), mat)
        box("charminar_parapet", (S + 0.6 * s, S + 0.6 * s, 1.2 * s), (cx, cy, z0 + 32.4 * s), mat)
        # small arch insets on upper arcade (darker)
        for side in range(4):
            for k in range(5):
                off = -S / 2 + 1.8 * s + k * (S - 3.6 * s) / 4
                if side == 0:
                    p = (cx + off, cy - S / 2 + 0.4 * s - 0.05, z0 + 28.6 * s)
                    r_ = (math.radians(90), 0, 0)
                elif side == 1:
                    p = (cx + S / 2 - 0.4 * s + 0.05, cy + off, z0 + 28.6 * s)
                    r_ = (math.radians(90), 0, math.radians(90))
                elif side == 2:
                    p = (cx + off, cy + S / 2 - 0.4 * s + 0.05, z0 + 28.6 * s)
                    r_ = (math.radians(90), 0, math.radians(180))
                else:
                    p = (cx - S / 2 + 0.4 * s - 0.05, cy + off, z0 + 28.6 * s)
                    r_ = (math.radians(90), 0, math.radians(-90))
                plane(f"charminar_inset{side}_{k}", 1.6 * s, 3.6 * s, p, r_, self.m_far[2])
        for k, (dx, dy) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)]):
            self.minaret(f"charminar_min{k}", cx + dx * S / 2, cy + dy * S / 2, z0, h=46 * s, r=2.0 * s, mat=mat)

    def dome(self, name, x, y, z0, r, mat):
        drum = cylinder(name + "_drum", r * 1.02, r * 0.7, (x, y, z0 + r * 0.35), mat, 24)
        dm = uv_sphere(name + "_dome", r, (x, y, z0 + r * 0.7), mat, 24, 12)
        dm.scale = (1, 1, 1.12)
        fin = cylinder(name + "_fin", r * 0.05, r * 0.6, (x, y, z0 + r * 1.95), mat, 6)
        return dm

    def skyline(self):
        rnd = self.rnd
        # distant city strips with lit windows
        for layer, (dist, h, mat) in enumerate([(210, 11, self.m_far[2]), (320, 15, self.m_far[1]), (480, 19, self.m_far[0])]):
            for side in (1, -1):
                y = dist * side
                verts, faces = [], []
                x = -700
                while x < 700:
                    w = rnd.uniform(6, 22)
                    hh = h * rnd.uniform(0.5, 1.3)
                    i0 = len(verts)
                    verts += [(x, y, LANE_Z), (x + w, y, LANE_Z), (x + w, y, LANE_Z + hh), (x, y, LANE_Z + hh)]
                    faces.append((i0, i0 + 1, i0 + 2, i0 + 3))
                    if self.time != "day":
                        for k in range(int(w * hh / 40)):
                            if rnd.random() < 0.35:
                                wx = x + rnd.uniform(1, w - 1)
                                wz = LANE_Z + rnd.uniform(2, hh - 1)
                                j = len(verts)
                                dy = -0.3 * side
                                verts += [(wx, y + dy, wz), (wx + 0.9, y + dy, wz), (wx + 0.9, y + dy, wz + 1.0), (wx, y + dy, wz + 1.0)]
                                faces.append((j, j + 1, j + 2, j + 3))
                    x += w + rnd.uniform(0, 3)
                ob = mesh_obj(f"skystrip{layer}_{side}", verts, faces, mat)
                if self.time != "day":
                    ob.data.materials.append(self.m_farwin)
                    # assign window faces (every face after first quad of each building that is small) to slot 1
                    for p in ob.data.polygons:
                        if p.area < 1.0:
                            p.material_index = 1
        plane("far_ground", 8000, 8000, (0, 0, LANE_Z - 0.4), mat=self.m_far[2])
        self.charminar(-110, 470, s=1.0, mat=self.m_far[0])
        self.dome("tombA", 140, 380, LANE_Z + 10, 9, self.m_far[0])
        self.dome("tombB", -260, 520, LANE_Z + 8, 12, self.m_far[0])
        for i, (x, y) in enumerate([(60, 300), (75, 300), (-200, 330), (230, 450), (-330, 260)]):
            self.minaret(f"min{i}", x, y, LANE_Z, h=rnd.uniform(26, 38), r=1.3, mat=self.m_far[1 if y < 320 else 0])

    def lane_props(self):
        # street lamp pole + wires across the lane
        pole = cylinder("lane_pole", 0.09, 7.5, (6.5, -7.6, LANE_Z + 3.75), self.m_wire, 10)
        arm = cylinder("lane_arm", 0.04, 1.2, (6.5, -7.0, LANE_Z + 7.0), self.m_wire, 8)
        arm.rotation_euler = (math.radians(90), 0, 0)
        self.bulb("lane_bulb", Vector((6.5, -6.45, LANE_Z + 6.85)), energy=120.0 if self.time == "night" else 0.0)
        pole2 = cylinder("lane_pole2", 0.09, 7.5, (-11.0, -7.6, LANE_Z + 3.75), self.m_wire, 10)
        for k in range(4):
            self.wire(f"lane_wire{k}", (6.5, -7.6, LANE_Z + 7.2 - k * 0.25), (-11.0, -7.6, LANE_Z + 7.2 - k * 0.25), sag=0.5 + k * 0.1)
        self.wire("lane_wire_house", (6.5, -7.6, LANE_Z + 6.6), (2.5, -5.5, LANE_Z + 5.4), sag=0.3)
        self.wire("lane_wire_across", (-11.0, -7.6, LANE_Z + 6.9), (-14, 6, LANE_Z + 9.0), sag=0.8)
        self.wire("lane_wire_far", (6.5, -7.6, LANE_Z + 7.0), (30, -7.6, LANE_Z + 7.0), sag=0.6)

    def build(self, neighbourhood=True, skyline=True, trees=True, lane=True, dressing=True):
        self.sky()
        if dressing:
            self.sky_dressing()
        self.hero()
        if neighbourhood:
            self.neighbourhood()
        if trees:
            self.trees()
        if skyline:
            self.skyline()
        if lane:
            self.lane_props()
        return self
