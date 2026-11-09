# ALWAYS FALLING — Abu Dhabi 1975–1981: construction skyline, cranes, Qasr al-Hosn, camp roof, room, post box
import bpy, bmesh, math, random
from mathutils import Vector
import af
from af import box, plane, cylinder, uv_sphere, add_outline, toon_mat, flat_mat, hexc

PAL = {
    "sunset": dict(
        sky=[(-1.0, "#4A2A3A"), (-0.01, "#FFD08A"), (0.03, "#FFB46A"), (0.1, "#F0806A"), (0.25, "#B05A7E"), (0.5, "#5A3A7A"), (1.0, "#2A2050")],
        ambient="#7A4A6A", amb=0.7, key_dir=(-0.28, 0.95, -0.16), key_col="#FFC27A", key_e=3.4,
        bld=[("#E8B47A", "#7A4A5E", "#FFE0A8"), ("#D8A070", "#704258", "#F8D0A0"), ("#E0C098", "#7A5468", "#FFE8C0")],
        conc=("#C89A78", "#6A4258", "#F0C49A"), steel=("#3A2230", "#1C0E18", "#6A4048"), sand=("#E0B07A", "#8A5A5E", "#FFD8A0"),
        sea=("#C8806A", "#6A3A5A", "#FFC08A"), fort=("#F2E2C8", "#9A7A86", "#FFF6E6"), win="#5A2E3A", win_lit="#FFD27A",
        far="#9A5A6A", far2="#B06A70", sil="#2E1824", outline="#2A1220"),
    "night": dict(
        sky=[(-1.0, "#1A0E1E"), (-0.01, "#8A4A2A"), (0.04, "#5A3030"), (0.15, "#2E1A34"), (0.45, "#1A1030"), (1.0, "#0C0820")],
        ambient="#3A2440", amb=0.55, key_dir=(0.5, 0.6, -0.6), key_col="#FFC890", key_e=0.9,
        bld=[("#6A4A50", "#2E1C2C", "#9A6E66"), ("#5E4250", "#2A1828", "#8E6464"), ("#70524E", "#321E2A", "#A07A6A")],
        conc=("#5A4048", "#281A24", "#8A6460"), steel=("#24161E", "#100A10", "#4A303A"), sand=("#5A4038", "#281A20", "#8A6450"),
        sea=("#3A2A3A", "#1A101C", "#6A4A50"), fort=("#8A7470", "#3E2E36", "#BAA090"), win="#24141C", win_lit="#FFB858",
        far="#4A2E36", far2="#5A3A3E", sil="#120A10", outline="#120810"),
}


def T(name, trip, band=0.32, rim=None):
    return toon_mat(name, trip[0], shadow=trip[1], light=trip[2], band=band, light_band=0.78, rim=rim, rim_th=0.6)


class Auh:
    def __init__(self, time="sunset", seed=11, year=1975):
        self.time = time
        self.P = PAL[time]
        self.rnd = random.Random(seed)
        self.year = year
        P = self.P
        self.m_bld = [T(f"auh_bld{i}_{time}", b) for i, b in enumerate(P["bld"])]
        self.m_conc = T("auh_conc_" + time, P["conc"])
        self.m_steel = T("auh_steel_" + time, P["steel"])
        self.m_sand = T("auh_sand_" + time, P["sand"])
        self.m_fort = T("auh_fort_" + time, P["fort"], rim=P["fort"][2])
        self.m_win = flat_mat("auh_win_" + time, P["win"])
        self.m_winlit = flat_mat("auh_winlit_" + time, P["win_lit"], strength=2.5)
        self.m_far = flat_mat("auh_far_" + time, P["far"])
        self.m_far2 = flat_mat("auh_far2_" + time, P["far2"])
        self.m_sil = flat_mat("auh_sil_" + time, P["sil"])
        self.m_leaf = T("auh_leaf_" + time, ("#3A4A2E", "#1A1E1A", "#6A7A40") if time == "sunset" else ("#1E2420", "#0C0E0C", "#38402E"))
        self.m_trunk = T("auh_trunk_" + time, ("#5A3A30", "#2A1A1C", "#8A5A40"))

    def ol(self, ob, t=0.04):
        add_outline(ob, t, self.P["outline"])
        return ob

    def sky(self, stars=None):
        P = self.P
        st = stars if stars is not None else (dict(density=0.04, size=0.06, scale=240, bright=3.0, color="#FFE8D0") if self.time == "night" else None)
        af.sky_world(P["sky"], ambient=P["ambient"], ambient_strength=P["amb"], stars=st, horizon_fade=(0.03, 0.25))
        af.add_sun("key", P["key_dir"], P["key_col"], energy=P["key_e"], angle=1.0)

    # -------------------------------------------------------------- buildings
    def building(self, name, x, y, w, d, floors, unfinished=False, rot=0.0):
        rnd = self.rnd
        h = floors * 3.3
        root = bpy.data.objects.new(name, None)
        af.link(root)
        root.location = (x, y, 0)
        root.rotation_euler = (0, 0, rot)
        parts = []
        if not unfinished:
            m = self.m_bld[rnd.randrange(len(self.m_bld))]
            b = box(name + "_b", (w, d, h), (0, 0, h / 2), m)
            parts.append(b)
            # window grid on the -y face (arched tops on alternate buildings)
            nx = max(1, int(w / 2.6))
            for f in range(floors):
                for k in range(nx):
                    lit = self.time == "night" and rnd.random() < 0.35
                    wm = self.m_winlit if lit else self.m_win
                    px = -w / 2 + (k + 0.5) * w / nx
                    parts.append(plane(f"{name}_w{f}_{k}", 1.1, 1.5, (px, -d / 2 - 0.02, f * 3.3 + 1.7), (math.radians(90), 0, 0), wm))
            # roof parapet + water tank
            parts.append(box(name + "_par", (w + 0.2, d + 0.2, 0.6), (0, 0, h + 0.3), m))
            if rnd.random() < 0.5:
                parts.append(cylinder(name + "_tank", 1.0, 1.6, (rnd.uniform(-w / 3, w / 3), rnd.uniform(-d / 3, d / 3), h + 1.4), self.m_conc, 12))
        else:
            # exposed concrete frame: slabs + columns, scaffolding on the front
            for f in range(floors + 1):
                parts.append(box(f"{name}_slab{f}", (w, d, 0.3), (0, 0, f * 3.3), self.m_conc))
            nx, ny = max(2, int(w / 4) + 1), max(2, int(d / 4) + 1)
            for i in range(nx):
                for j in range(ny):
                    px = -w / 2 + i * w / (nx - 1)
                    py = -d / 2 + j * d / (ny - 1)
                    parts.append(box(f"{name}_col{i}_{j}", (0.4, 0.4, h), (px, py, h / 2), self.m_conc))
            parts += self.scaffold(name + "_scaf", -w / 2 - 0.2, w / 2 + 0.2, -d / 2 - 1.3, 0.0, h + 1.5)
        for p in parts:
            p.parent = root
            if p.type == "MESH" and ("_b" in p.name[-3:] or "_slab" in p.name or "_par" in p.name):
                self.ol(p, 0.05)
        return root

    def scaffold(self, name, x0, x1, y0, z0, z1, bay=2.0, lift=2.0):
        parts = []
        nx = int((x1 - x0) / bay) + 1
        for i in range(nx):
            x = x0 + i * bay
            for y in (y0, y0 + 1.1):
                parts.append(cylinder(f"{name}_std{i}_{y:.1f}", 0.03, z1 - z0, (x, y, (z0 + z1) / 2), self.m_steel, 6))
        nz = int((z1 - z0) / lift) + 1
        for k in range(nz):
            z = z0 + k * lift
            for y in (y0, y0 + 1.1):
                c = cylinder(f"{name}_led{k}_{y:.1f}", 0.025, x1 - x0, ((x0 + x1) / 2, y, z), self.m_steel, 6)
                c.rotation_euler = (0, math.radians(90), 0)
                parts.append(c)
            if k % 2 == 1:
                parts.append(box(f"{name}_plank{k}", (x1 - x0, 1.1, 0.06), ((x0 + x1) / 2, y0 + 0.55, z + 0.05), self.m_trunk))
        # diagonal braces
        for i in range(0, nx - 1, 2):
            c = cylinder(f"{name}_brace{i}", 0.02, math.hypot(bay, z1 - z0), (x0 + i * bay + bay / 2, y0 - 0.02, (z0 + z1) / 2), self.m_steel, 6)
            c.rotation_euler = (0, math.atan2(bay, z1 - z0), 0)
            parts.append(c)
        return parts

    def crane(self, name, x, y, h=45.0, jib=40.0, rot=0.0):
        m = self.m_sil if self.time != "day" else self.m_steel
        root = bpy.data.objects.new(name, None)
        af.link(root)
        root.location = (x, y, 0)
        root.rotation_euler = (0, 0, rot)
        parts = [box(name + "_mast", (1.6, 1.6, h), (0, 0, h / 2), m)]
        # lattice suggestion: cut-out holes as darker? keep silhouette crisp: add cross bracing bars outside
        for k in range(int(h / 3)):
            z = k * 3 + 1.5
            c = cylinder(f"{name}_x{k}", 0.06, 2.3, (0, -0.85, z), m, 4)
            c.rotation_euler = (0, math.radians(45 if k % 2 else -45), 0)
            parts.append(c)
        parts.append(box(name + "_jib", (jib, 1.0, 1.0), (jib / 2 - 8, 0, h + 0.5), m))
        parts.append(box(name + "_counter", (4, 2.0, 2.2), (-8, 0, h - 0.2), m))
        parts.append(box(name + "_cab", (2.0, 2.0, 2.0), (0.8, 0, h - 1.2), m))
        top = cylinder(name + "_peak", 0.5, 6.0, (0, 0, h + 3.5), m, 6, r2=0.1)
        parts.append(top)
        for xx in (jib - 8, -8):
            c = cylinder(f"{name}_tie{xx}", 0.05, math.hypot(abs(xx), 5.5), (xx / 2, 0, h + 3.5), m, 4)
            c.rotation_euler = (0, math.atan2(xx, 5.5) * -1 + 0, 0)
            parts.append(c)
        hook = cylinder(name + "_cable", 0.04, 18.0, (jib * 0.55 - 8, 0, h - 9.0), m, 4)
        parts.append(hook)
        parts.append(box(name + "_load", (3.0, 1.0, 0.6), (jib * 0.55 - 8, 0, h - 18.2), m))
        for p in parts:
            p.parent = root
        return root

    def fort(self, x, y, s=1.0):
        """Qasr al-Hosn silhouette: white walls with crenellations, a round tower and a square tower."""
        m = self.m_fort
        parts = []
        W, D, H = 40 * s, 36 * s, 9 * s
        for (sx, sy, lx, ly) in ((W, 1.2 * s, 0, -D / 2), (W, 1.2 * s, 0, D / 2), (1.2 * s, D, -W / 2, 0), (1.2 * s, D, W / 2, 0)):
            parts.append(box(f"fort_wall{lx:.0f}{ly:.0f}", (sx, sy, H), (x + lx, y + ly, H / 2), m))
        for k in range(int(W / (2.4 * s))):
            parts.append(box(f"fort_cren{k}", (1.2 * s, 1.4 * s, 1.2 * s), (x - W / 2 + (k + 0.5) * 2.4 * s, y - D / 2, H + 0.6 * s), m))
        parts.append(cylinder("fort_round", 5.5 * s, 18 * s, (x - W / 2, y - D / 2, 9 * s), m, 32))
        parts.append(cylinder("fort_round_top", 5.9 * s, 1.4 * s, (x - W / 2, y - D / 2, 18 * s + 0.7 * s), m, 32))
        parts.append(box("fort_square", (9 * s, 9 * s, 16 * s), (x + W / 2, y + D / 2, 8 * s), m))
        parts.append(box("fort_square_top", (10 * s, 10 * s, 1.2 * s), (x + W / 2, y + D / 2, 16.6 * s), m))
        for p in parts:
            self.ol(p, 0.08)
        return parts

    def mosque(self, x, y, s=1.0):
        m = self.m_fort
        parts = [box("mosque_hall", (24 * s, 18 * s, 8 * s), (x, y, 4 * s), m)]
        d = uv_sphere("mosque_dome", 7 * s, (x, y, 8 * s), m, 32, 16)
        d.scale = (1, 1, 0.9)
        parts.append(d)
        parts.append(cylinder("mosque_min", 1.4 * s, 32 * s, (x + 14 * s, y - 8 * s, 16 * s), m, 16))
        parts.append(cylinder("mosque_bal", 2.3 * s, 0.8 * s, (x + 14 * s, y - 8 * s, 26 * s), m, 16))
        tip = cylinder("mosque_tip", 1.4 * s, 4 * s, (x + 14 * s, y - 8 * s, 34 * s), m, 16, r2=0.1)
        parts.append(tip)
        for p in parts:
            self.ol(p, 0.06)
        return parts

    def skyline(self, center=(0, 120), n=26, radius=150, year=None, flip=False):
        """Mix of finished blocks, unfinished frames and cranes; later years -> taller + more finished."""
        rnd = self.rnd
        yr = year or self.year
        growth = min(1.0, max(0.0, (yr - 1975) / 6.0))
        cx, cy = center
        for i in range(n):
            a = rnd.uniform(-1.1, 1.1)
            d = rnd.uniform(40, radius)
            x = cx + math.sin(a) * d
            y = cy + math.cos(a) * d * 0.6 * (-1 if flip else 1)
            floors = int(rnd.choice([3, 4, 5, 6, 8, 10]) * (1 + growth * rnd.uniform(0.2, 0.9)))
            unfinished = rnd.random() < (0.45 - 0.3 * growth)
            self.building(f"auh{i}", x, y, rnd.uniform(12, 22), rnd.uniform(10, 18), floors, unfinished, rot=rnd.uniform(-0.2, 0.2))
        for k in range(int(4 - 2 * growth) + 2):
            self.crane(f"crane{k}", cx + rnd.uniform(-120, 120), cy + rnd.uniform(-20, 90) * (-1 if flip else 1), h=rnd.uniform(38, 60), jib=rnd.uniform(30, 46), rot=rnd.uniform(0, math.pi))
        # far strip
        verts, faces = [], []
        x = -900
        while x < 900:
            w = rnd.uniform(8, 26)
            hh = rnd.uniform(6, 26) * (1 + growth * 0.6)
            i0 = len(verts)
            fy = cy + (-420 if flip else 420)
            verts += [(x, fy, 0), (x + w, fy, 0), (x + w, fy, hh), (x, fy, hh)]
            faces.append((i0, i0 + 1, i0 + 2, i0 + 3))
            x += w + rnd.uniform(0, 6)
        af.mesh_obj("auh_far", verts, faces, self.m_far)

    def ground(self, sea_y=None):
        plane("auh_sand", 6000, 6000, (0, 0, 0), mat=self.m_sand)
        if sea_y is not None:
            sea = T("auh_sea_" + self.time, self.P["sea"])
            plane("auh_sea", 6000, 3000, (0, sea_y + 1500, 0.05), mat=sea)

    def palms(self, spots):
        for i, (x, y) in enumerate(spots):
            af.palm(f"auhpalm{i}", (x, y, 0), self.rnd.uniform(9, 14), (self.rnd.uniform(-0.1, 0.1), self.rnd.uniform(-0.1, 0.1)), 0.1, 15, 3.4,
                    seed=i + 70, trunk_mat=self.m_trunk, frond_mat=self.m_leaf)

    def sun_disc(self, size=24.0):
        sd = (-Vector(self.P["key_dir"])).normalized()
        af.moon("auh_sun", sd * 600, size, phase=5.0, tilt=0.0, col_dark="#FFB070", col_lit="#FFF0C0", glow=0.8, cam_dir=-sd)

    # -------------------------------------------------------------- interiors / props
    def room(self, lamp=True):
        """Labour-camp room, 3.2 x 3.6 m: bunk bed, table + lamp, window with city lights, calendar."""
        wall = T("room_wall", ("#6A5A70", "#2E2238", "#A08A98"))
        floor = T("room_floor", ("#5A4A44", "#2A1E22", "#8A7060"))
        wood = T("room_wood", ("#6A4430", "#2E1C1C", "#9A6844"))
        cloth = T("room_cloth", ("#7A8AB0", "#36406A", "#B0C0E0"))
        parts = [box("room_floor", (3.2, 3.6, 0.1), (0, 0, -0.05), floor),
                 box("room_wall_back", (3.2, 0.12, 2.8), (0, 1.8, 1.4), wall),
                 box("room_wall_left", (0.12, 3.6, 2.8), (-1.6, 0, 1.4), wall),
                 box("room_wall_right", (0.12, 3.6, 2.8), (1.6, 0, 1.4), wall),
                 box("room_ceiling", (3.2, 3.6, 0.1), (0, 0, 2.85), wall)]
        # window in the back wall (city lights outside)
        win_city = flat_mat("room_window_city", "#2A1830")
        parts.append(plane("room_window", 1.0, 0.9, (0.7, 1.73, 1.6), (math.radians(90), 0, 0), win_city))
        rnd = random.Random(5)
        for k in range(14):
            parts.append(plane(f"room_wlight{k}", 0.05, 0.06, (0.7 + rnd.uniform(-0.45, 0.45), 1.72, 1.6 + rnd.uniform(-0.4, 0.2)), (math.radians(90), 0, 0), self.m_winlit))
        for k, (sz, lc) in enumerate((((1.1, 0.06, 0.06), (0.7, 1.7, 2.07)), ((1.1, 0.06, 0.06), (0.7, 1.7, 1.13)), ((0.06, 0.06, 1.0), (0.17, 1.7, 1.6)), ((0.06, 0.06, 1.0), (1.23, 1.7, 1.6)))):
            parts.append(box(f"room_wframe{k}", sz, lc, wood))
        # bunk bed along the left wall
        for z in (0.45, 1.55):
            parts.append(box(f"room_bunk{z}", (0.9, 1.95, 0.12), (-1.1, 0.3, z), wood))
            parts.append(box(f"room_mat{z}", (0.85, 1.9, 0.12), (-1.1, 0.3, z + 0.12), cloth))
        for sx in (-1, 1):
            for sy in (-1, 1):
                parts.append(box(f"room_post{sx}{sy}", (0.06, 0.06, 1.9), (-1.1 + sx * 0.42, 0.3 + sy * 0.95, 0.95), wood))
        # table + chair
        parts.append(box("room_table", (1.0, 0.6, 0.05), (0.9, 0.9, 0.75), wood))
        for sx in (-1, 1):
            for sy in (-1, 1):
                parts.append(box(f"room_tleg{sx}{sy}", (0.04, 0.04, 0.75), (0.9 + sx * 0.45, 0.9 + sy * 0.25, 0.375), wood))
        parts.append(box("room_chair", (0.42, 0.42, 0.05), (0.85, 0.35, 0.45), wood))
        parts.append(box("room_chair_back", (0.42, 0.05, 0.45), (0.85, 0.15, 0.7), wood))
        # calendar on the right wall
        cal = flat_mat("room_calendar", "#E8E0D0")
        parts.append(plane("room_cal", 0.32, 0.45, (1.54, 0.4, 1.7), (math.radians(90), 0, math.radians(-90)), cal))
        # suitcase under the bunk
        parts.append(box("room_suitcase", (0.6, 0.4, 0.18), (-1.0, -0.1, 0.12), T("room_case", ("#4A2E2A", "#221416", "#6E4440"))))
        for p in parts:
            if p.type == "MESH" and p.name.startswith(("room_bunk", "room_table", "room_chair", "room_suitcase")):
                self.ol(p, 0.012)
        if lamp:
            lm = flat_mat("room_lampbulb", "#FFE2A8", strength=8.0)
            parts.append(cylinder("room_lampbase", 0.07, 0.02, (1.2, 1.05, 0.79), wood, 12))
            parts.append(cylinder("room_lampstem", 0.012, 0.35, (1.2, 1.05, 0.96), self.m_steel, 6))
            shade = cylinder("room_lampshade", 0.06, 0.14, (1.12, 1.0, 1.12), T("room_shade", ("#2E5A3A", "#14281A", "#4E8A5A")), 16, r2=0.16)
            shade.rotation_euler = (math.radians(180 - 25), 0, 0)
            parts.append(shade)
            parts.append(uv_sphere("room_bulb", 0.035, (1.12, 0.98, 1.07), lm, 12, 6))
            af.add_point("room_lamp", (1.1, 0.95, 1.02), "#FFD49A", energy=60.0, radius=0.08)
        return parts

    def cassette_recorder(self, loc, rot=0.0, name="recorder"):
        """1970s portable cassette recorder with spinning reels (keyframe reels' rotation)."""
        body = T(name + "_body", ("#2A2A32", "#121216", "#4A4A56"))
        silver = T(name + "_silver", ("#B8BCC8", "#4A4E5E", "#F2F4FA"))
        window = flat_mat(name + "_window", "#4A3A3A")
        root = bpy.data.objects.new(name, None)
        af.link(root)
        root.location = loc
        root.rotation_euler = (0, 0, rot)
        parts = [box(name + "_case", (0.26, 0.15, 0.06), (0, 0, 0.03), body),
                 box(name + "_grille", (0.1, 0.002, 0.04), (-0.07, -0.076, 0.03), silver),
                 plane(name + "_win", 0.09, 0.03, (0.05, 0.0, 0.0605), (0, 0, 0), window)]
        reels = []
        for k, dx in enumerate((0.03, 0.07)):
            r = cylinder(f"{name}_reel{k}", 0.011, 0.004, (dx, 0.0, 0.062), silver, 6)
            reels.append(r)
            parts.append(r)
        for k in range(5):
            b = box(f"{name}_key{k}", (0.025, 0.02, 0.012), (-0.06 + k * 0.03, 0.06, 0.066), silver if k != 1 else T(name + "_rec", ("#C02A2A", "#5A1010", "#FF5A5A")))
            parts.append(b)
        for p in parts:
            p.parent = root
        add_outline(parts[0], 0.003, "#0A0608")
        return root, reels

    def post_box(self, loc):
        red = T("postbox_red", ("#C8322E", "#5A1218", "#F06A50"))
        parts = [cylinder("postbox_body", 0.28, 1.3, (loc[0], loc[1], 0.65), red, 24),
                 cylinder("postbox_cap", 0.32, 0.12, (loc[0], loc[1], 1.36), red, 24),
                 box("postbox_slot", (0.26, 0.04, 0.04), (loc[0], loc[1] - 0.27, 1.05), flat_mat("postbox_slot_dark", "#120808"))]
        for p in parts[:2]:
            self.ol(p, 0.02)
        return parts
