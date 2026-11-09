# The boy's room in Hyderabad (1976–1981): shuttered window to the night sky, bed, wall with the 2-rupee note,
# shelf of cassettes, calendar, table with a cassette player; plus the front door with a letter slot.
import bpy, math, random, os
from mathutils import Vector
import af
from af import box, plane, cylinder, uv_sphere, add_outline, toon_mat, flat_mat

NOTE_TEX = os.path.join(af.ASSETS, "tex", "note_2rs.png")

PAL = {
    "night": dict(wall=("#5A6A96", "#262E50", "#8C9CC8"), floor=("#4A4E6A", "#20223A", "#72769A"), wood=("#4A3A4E", "#201824", "#6E5A70"),
                  cloth=("#7A8AC0", "#36406E", "#B0BEE6"), sky=[(-1, "#0B1C2E"), (0.0, "#2E587A"), (0.3, "#14335E"), (1, "#060B26")],
                  amb="#2A3A66", key=("#9FC0FF", 1.6), lamp=("#FFC27A", 40.0)),
    "morning": dict(wall=("#E8D8B0", "#8A7E98", "#FFF2D0"), floor=("#B89A80", "#6A5468", "#E0C4A8"), wood=("#7A5038", "#3E2830", "#A8724E"),
                    cloth=("#9AB0E0", "#56608E", "#CCD8F6"), sky=[(-1, "#9AB8D8"), (0.0, "#F2E8D2"), (0.3, "#A8CCF0"), (1, "#5A90D8")],
                    amb="#C0B0A8", key=("#FFF0D8", 3.0), lamp=("#FFC27A", 0.0)),
}


def T(name, trip, band=0.32):
    return toon_mat(name, trip[0], shadow=trip[1], light=trip[2], band=band, light_band=0.78)


def note_mat(name="note2rs"):
    m, nt = af.new_mat(name)
    tc = af.N(nt, "ShaderNodeTexCoord")
    im = af.N(nt, "ShaderNodeTexImage")
    im.image = bpy.data.images.load(NOTE_TEX, check_existing=True)
    af.L(nt, af.O(tc, "UV"), af.I(im, "Vector"))
    dif = af.N(nt, "ShaderNodeBsdfDiffuse")
    s2r = af.N(nt, "ShaderNodeShaderToRGB")
    af.L(nt, af.O(dif, "BSDF"), af.I(s2r, "Shader"))
    bw = af.N(nt, "ShaderNodeRGBToBW")
    af.L(nt, af.O(s2r, "Color"), af.I(bw, "Color"))
    rp = af.ramp(nt, [(0.0, "#6A6A8A"), (0.2, "#D8D8E8"), (0.6, "#FFFFFF")], "CONSTANT", fac=af.O(bw, "Val"))
    col = af.mixcol(nt, 1.0, af.O(im, "Color"), af.O(rp, "Color"), "MULTIPLY")
    af.finish_emission(m, nt, col)
    m.use_backface_culling = False
    return m


def note(name, loc, rot, size=0.16, mat=None):
    """A banknote card 2:1 with UVs."""
    w, h = size, size / 2
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for li, (u, v) in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = (u, v)
    ob = af.link(bpy.data.objects.new(name, me))
    me.materials.append(mat or note_mat())
    ob.location = loc
    ob.rotation_euler = rot
    return ob


class Room:
    """Room 3.4 (x) x 3.0 (y) x 2.9 (z); window in the back wall (+y) looking out to the sky."""
    def __init__(self, time="night", year=1979):
        self.P = PAL[time]
        self.time = time
        self.year = year
        P = self.P
        self.m_wall = T("broom_wall_" + time, P["wall"])
        self.m_floor = T("broom_floor_" + time, P["floor"])
        self.m_wood = T("broom_wood_" + time, P["wood"])
        self.m_cloth = T("broom_cloth_" + time, P["cloth"])

    def build(self, shutters_open=1.0, cassettes=8, note_on_wall=True, calendar_year=None):
        P = self.P
        af.sky_world(P["sky"], ambient=P["amb"], ambient_strength=0.7,
                     stars=dict(density=0.06, size=0.07, scale=240, bright=4.0, color="#E4ECFF") if self.time == "night" else None)
        af.add_sun("key", (0.2, -0.8, -0.55), P["key"][0], energy=P["key"][1], angle=1.5)
        parts = [box("br_floor", (3.4, 3.0, 0.1), (0, 0, -0.05), self.m_floor),
                 box("br_left", (0.15, 3.0, 2.9), (-1.7, 0, 1.45), self.m_wall),
                 box("br_right", (0.15, 3.0, 2.9), (1.7, 0, 1.45), self.m_wall),
                 box("br_ceiling", (3.4, 3.0, 0.1), (0, 0, 2.9), self.m_wall)]
        # back wall with a window opening (x -0.5..0.5, z 1.0..2.1)
        parts += [box("br_back_l", (1.2, 0.15, 2.9), (-1.1, 1.5, 1.45), self.m_wall),
                  box("br_back_r", (1.2, 0.15, 2.9), (1.1, 1.5, 1.45), self.m_wall),
                  box("br_back_b", (1.0, 0.15, 1.0), (0, 1.5, 0.5), self.m_wall),
                  box("br_back_t", (1.0, 0.15, 0.8), (0, 1.5, 2.5), self.m_wall)]
        # window bars
        for k in range(4):
            parts.append(cylinder(f"br_bar{k}", 0.012, 1.1, (-0.36 + k * 0.24, 1.5, 1.55), self.m_wood, 6))
        # wooden shutters (two leaves hinged at the window sides, rotate inward to close)
        self.shutters = []
        for s in (-1, 1):
            piv = bpy.data.objects.new(f"br_shutter_piv{s}", None)
            af.link(piv)
            piv.location = (s * 0.5, 1.42, 1.0)
            leaf = box(f"br_shutter{s}", (0.5, 0.05, 1.1), (-s * 0.25, 0, 0.55), self.m_wood)
            leaf.parent = piv
            add_outline(leaf, 0.008, "#0A0A18")
            piv.rotation_euler = (0, 0, math.radians(s * 100 * shutters_open))
            self.shutters.append(piv)
        # bed along the left wall
        parts.append(box("br_bed", (0.95, 1.9, 0.4), (-1.15, 0.1, 0.2), self.m_wood))
        parts.append(box("br_mattress", (0.9, 1.85, 0.12), (-1.15, 0.1, 0.46), self.m_cloth))
        parts.append(box("br_pillow", (0.6, 0.35, 0.1), (-1.15, 0.85, 0.56), T("br_pillow_" + self.time, ("#E8E8F0", "#8A8AA8", "#FFFFFF"))))
        # table under the window with the cassette player
        parts.append(box("br_table", (0.9, 0.55, 0.05), (0.6, 1.1, 0.72), self.m_wood))
        for sx in (-1, 1):
            for sy in (-1, 1):
                parts.append(box(f"br_tleg{sx}{sy}", (0.04, 0.04, 0.72), (0.6 + sx * 0.4, 1.1 + sy * 0.22, 0.36), self.m_wood))
        # shelf with cassettes on the right wall
        parts.append(box("br_shelf", (0.12, 0.9, 0.03), (-1.6, 0.25, 1.22), self.m_wood))
        cas = T("br_cassette", ("#2A2A36", "#121218", "#4A4A5E"))
        lab = T("br_cassette_label", ("#E8D8B8", "#8A7A86", "#FFF4DE"))
        self.cassettes = []
        for k in range(cassettes):
            c = box(f"br_cas{k}", (0.07, 0.017, 0.11), (-1.6, -0.15 + k * 0.022, 1.29), cas)
            self.cassettes.append(c)
            parts.append(c)
        # calendar
        cal = flat_mat("br_calendar", "#EDE6D6")
        parts.append(plane("br_cal", 0.3, 0.42, (1.62, 0.7, 1.55), (math.radians(90), 0, math.radians(-90)), cal))
        # the note pinned above the bed
        self.note = None
        if note_on_wall:
            self.note = note("br_note", (-1.6, 0.35, 1.55), (math.radians(90), 0, math.radians(90)), size=0.2)
            pin = uv_sphere("br_pin", 0.008, (-1.6 + 0.012, 0.35, 1.6), flat_mat("br_pinred", "#C83030"), 8, 4)
        # ceiling bulb (off at night, the moon lights the room) and a warm lamp on the table
        if self.P["lamp"][1] > 0:
            lm = flat_mat("br_lampbulb", "#FFE2A8", strength=6.0)
            parts.append(uv_sphere("br_lamp", 0.04, (0.95, 1.2, 1.0), lm, 12, 6))
            af.add_point("br_lamplight", (0.95, 1.15, 1.0), self.P["lamp"][0], energy=self.P["lamp"][1], radius=0.06)
        for p in parts:
            if p.type == "MESH" and p.name.startswith(("br_bed", "br_table", "br_shelf")):
                add_outline(p, 0.012, "#0A0A18")
        return self


def front_door_inside(time="morning"):
    """Inside the front door (for the letter landing, E2L): door with a letter slot, floor, morning light through cracks."""
    P = PAL[time]
    af.sky_world(P["sky"], ambient=P["amb"], ambient_strength=0.9, stars=None)
    af.add_sun("key", (0.3, 0.6, -0.7), P["key"][0], energy=P["key"][1], angle=1.0)
    wall = T("fd_wall", P["wall"])
    wood = T("fd_wood", ("#7A4A30", "#3A2228", "#A8683E"))
    floor = T("fd_floor", P["floor"])
    parts = [box("fd_floor", (4, 4, 0.1), (0, 0, -0.05), floor),
             box("fd_wall", (4, 0.2, 3), (0, 0.9, 1.5), wall)]
    door = box("fd_door", (1.3, 0.08, 2.2), (0, 0.78, 1.1), wood)
    add_outline(door, 0.01, "#1A1010")
    slot = box("fd_slot", (0.3, 0.1, 0.04), (0, 0.76, 1.0), flat_mat("fd_slot_dark", "#120A08"))
    # a slice of sunlight under the door
    sun = flat_mat("fd_sunline", "#FFE6B0", strength=2.0)
    plane("fd_light", 1.2, 0.05, (0, 0.72, 0.01), mat=sun)
    return door
