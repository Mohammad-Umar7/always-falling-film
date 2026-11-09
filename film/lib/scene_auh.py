# Abu Dhabi shot helpers (right half of the split: 960x1080, warm palette)
import bpy, math
from mathutils import Vector
import af, sets_auh, poses

SUNSET_CAST = {"SKIN": ("#A8684E", "#4E2A34", "#E8A47A", "#FFD0A0"), "HAIR": ("#20141A", "#0C0608", "#4A2E30", "#FFB080"),
               "CLOTH_SHIRT_WORK": ("#9AB2D6", "#56607E", "#D2E0F4"), "CLOTH_TROUSER": ("#3E2E3A", "#1C121A", "#5E4652"),
               "EYE_WHITE": ("#E0C8C0", "#8A6A78", "#F8E8E0")}
NIGHT_CAST = {"SKIN": ("#6A4A50", "#2E1C28", "#A07070", "#FFC890"), "HAIR": ("#140C12", "#080408", "#342228", "#FFB070"),
              "CLOTH_SHIRT_WORK": ("#7E92B8", "#38425E", "#B2C4E2"), "CLOTH_TROUSER": ("#2A1E28", "#120C12", "#44323E"),
              "EYE_WHITE": ("#B8A2A2", "#6E5660", "#D8C6C2")}


def construction(year=1975, seed=11, time="sunset"):
    A = sets_auh.Auh(time=time, seed=seed, year=year)
    A.sky()
    A.ground()
    sea = sets_auh.T("auh_sea_" + time, A.P["sea"])
    from af import plane
    plane("auh_sea", 6000, 3000, (0, -1900, 0.05), mat=sea)
    A.skyline(center=(0, -150), n=24, radius=170, year=year, flip=True)
    A.fort(-60, -230, s=1.0)
    A.mosque(80, -250, s=1.0)
    A.palms([(-20, -60), (25, -75), (-45, -95), (60, -110), (10, -160)])
    if time == "sunset":
        A.sun_disc(30.0)
    # the father's building: unfinished frame at the origin, scaffold plank at 3rd lift
    A.building("site", 0, 0, 14, 12, 5, unfinished=True)
    return A


def camp_roof(year=1975, seed=12):
    A = sets_auh.Auh(time="night", seed=seed, year=year)
    A.sky()
    A.ground()
    A.skyline(center=(0, 160), n=26, radius=190, year=year)
    A.fort(-80, 260, s=1.0)
    A.mosque(90, 280, s=1.0)
    roof = box_roof(A)
    return A


SCAFFOLD_PLANK = (0.0, -7.25, 6.11)   # where the father stands on the site scaffold (front face, 3rd lift)


def box_roof(A):
    from af import box, cylinder
    roof_z = 6.6
    b = box("camp", (18, 12, roof_z), (0, 0, roof_z / 2), A.m_bld[0])
    A.ol(b, 0.05)
    for i, (sz, lc) in enumerate((((18, 0.2, 0.9), (0, -6, roof_z + 0.45)), ((18, 0.2, 0.9), (0, 6, roof_z + 0.45)),
                                  ((0.2, 12, 0.9), (-9, 0, roof_z + 0.45)), ((0.2, 12, 0.9), (9, 0, roof_z + 0.45)))):
        p = box(f"camp_par{i}", sz, lc, A.m_conc)
        A.ol(p, 0.02)
    t = cylinder("camp_tank", 0.8, 1.6, (6.5, 3.5, roof_z + 0.8), A.m_conc, 16)
    A.ol(t, 0.02)
    ac = box("camp_ac", (0.7, 0.5, 0.45), (-8.5, -2, roof_z + 0.5), A.m_steel)
    return roof_z
