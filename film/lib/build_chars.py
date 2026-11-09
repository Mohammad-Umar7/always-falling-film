# Build the whole cast in the live Blender (MPFB required) and save assets/chars.blend
import bpy, sys, os, importlib, math
LIB = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else BUILD_LIB  # noqa
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import af, chars
importlib.reload(af)
importlib.reload(chars)

# ---------------------------------------------------------------- clean lab
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
    for x in list(coll):
        try:
            coll.remove(x)
        except Exception:
            pass
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)

# ---------------------------------------------------------------- materials (neutral lab palette; shots retune TOON_RAMP)
M = {}
M["SKIN"] = af.toon_mat("SKIN", "#B57B57", shadow="#7A4A3A", light="#D69C74", band=0.32, light_band=0.8, rim="#FFD7B5", rim_th=0.6)
M["SKIN_BOY"] = af.toon_mat("SKIN_BOY", "#BC835E", shadow="#80503D", light="#DDA47B", band=0.32, light_band=0.8, rim="#FFD7B5", rim_th=0.6)
M["HAIR"] = af.toon_mat("HAIR", "#1C1513", shadow="#0B0707", light="#3B302B", band=0.4, light_band=0.85, rim="#7C8FC0", rim_th=0.6)
M["HAIR_GREY"] = af.toon_mat("HAIR_GREY", "#3A3634", shadow="#1A1716", light="#7B7470", band=0.4, light_band=0.85, rim="#A8B4D0", rim_th=0.6)
M["EYE"] = af.flat_mat("EYE", "#120A07")
M["WHITE"] = af.toon_mat("CLOTH_WHITE", "#E6ECF6", shadow="#8E9AC4", light="#FFFFFF", band=0.32, light_band=0.8)
M["SHIRT_WORK"] = af.toon_mat("CLOTH_SHIRT_WORK", "#9DB7D6", shadow="#5A6F96", light="#C9DCF0", band=0.32, light_band=0.8)
M["TROUSER"] = af.toon_mat("CLOTH_TROUSER", "#3B3A44", shadow="#1E1D26", light="#5A5966", band=0.32, light_band=0.8)
M["VEST"] = af.toon_mat("CLOTH_VEST", "#7A2E36", shadow="#45161E", light="#A04A50", band=0.32, light_band=0.8)
M["SHIRT_92"] = af.toon_mat("CLOTH_SHIRT_92", "#D9D2C3", shadow="#8C8578", light="#F4EEE2", band=0.32, light_band=0.8)
M["SHIRT_BOY"] = af.toon_mat("CLOTH_SHIRT_BOY", "#E9E4D6", shadow="#9C9686", light="#FFFFFF", band=0.32, light_band=0.8)
M["SHORTS"] = af.toon_mat("CLOTH_SHORTS", "#2E4A6B", shadow="#18283D", light="#4A6C91", band=0.32, light_band=0.8)
M["SHIRT_SON"] = af.toon_mat("CLOTH_SHIRT_SON", "#5F7FA3", shadow="#334A66", light="#86A4C4", band=0.32, light_band=0.8)
M["TROUSER_SON"] = af.toon_mat("CLOTH_TROUSER_SON", "#2A2B30", shadow="#141418", light="#45464E", band=0.32, light_band=0.8)
M["SHOES"] = af.toon_mat("CLOTH_SHOES", "#2C2020", shadow="#120C0C", light="#4E3A34", band=0.32, light_band=0.8)
M["BELT"] = af.toon_mat("CLOTH_BELT", "#1C110C", shadow="#0A0604", light="#3A2418", band=0.32, light_band=0.8)
M["EYE_WHITE"] = af.toon_mat("EYE_WHITE", "#F2F0EA", shadow="#A8A6B8", light="#FFFFFF", band=0.25, light_band=0.9)
M["EYE_IRIS"] = af.flat_mat("EYE_IRIS", "#24140E")
M["EYE_HL"] = af.flat_mat("EYE_HL", "#FFFFFF", strength=1.6)
M["EYE_LASH"] = af.flat_mat("EYE_LASH", "#140C0A")
for mn in ("SKIN", "SKIN_BOY"):
    M[mn].node_tree.nodes["TOON_RAMP"].color_ramp.elements[1].position = 0.22
OUTLINE = "#0B0810"


def build(name, age, x, macros, wardrobe, hair_style, hair_mat, skin_mat, moustache=None, part_x=0.035, fringe_dir=-1.0, lock_count=80):
    body, rig = chars.make_human(name, age, **macros)
    rig.location.x = x
    bpy.context.view_layer.update()
    chars.body_setup(body, rig, skin_mat)
    chars.add_subsurf(body, 1)
    parts = [body]
    cloth = []
    for item in wardrobe:
        kind = item[0]
        if kind == "kurta":
            top, skirt = chars.kurta(body, rig, name + "_kurta", item[1], length="knee", sleeves="full", inflate=0.014)
            chars.neckline(top, body, depth=0.012, slit=0.085, slit_w=0.008)
            cloth += [top, skirt]
        elif kind == "pajama":
            cloth.append(chars.trousers(body, rig, name + "_pajama", item[1], inflate=0.022, r_top=0.105, r_hem=0.095))
        elif kind == "shirt":
            sh = chars.shirt(body, rig, name + "_shirt", item[1], sleeves=item[2], tuck=item[3], inflate=0.012)
            chars.neckline(sh, body, depth=0.006, slit=0.07, slit_w=0.011)
            cloth.append(sh)
        elif kind == "trousers":
            tr, belt = chars.trousers(body, rig, name + "_trousers", item[1], inflate=0.018, r_top=0.1, r_hem=0.088, belt_mat=M["BELT"])
            cloth += [tr, belt]
        elif kind == "shorts":
            cloth.append(chars.trousers(body, rig, name + "_shorts", item[1], length="short", inflate=0.013, r_top=0.08, r_hem=0.072))
        elif kind == "shoes":
            cloth.append(chars.shoes(body, rig, name + "_shoes", item[1]))
        elif kind == "vest":
            cloth.append(chars.vest(body, rig, name + "_vest", item[1], inflate=0.024))
    for g in cloth:
        chars.add_subsurf(g, 1)
    shell = chars.hair_shell(body, rig, name + "_hairshell", hair_mat,
                             hairline=0.052 if hair_style != "boy" else 0.06, side_frac=0.45 if hair_style == "70s" else 0.78,
                             nape=0.035 if hair_style == "70s" else 0.115, inflate=0.014 if hair_style == "70s" else 0.0045)
    locks = chars.hair_locks(body, rig, shell, name + "_hairlocks", hair_mat, style="70s" if hair_style != "boy" else "side",
                             count=lock_count, seed=int(age * 7) % 97, part_x=part_x,
                             length=(0.07, 0.14) if hair_style == "70s" else (0.022, 0.045),
                             fringe=14 if hair_style == "70s" else 10, fringe_dir=fringe_dir, fringe_len=(0.055, 0.095))
    eyes = chars.eyes(body, rig, name + "_eye", M["EYE"])
    kid = name.startswith("BOY")
    brows = chars.face_ribbons(body, rig, name + "_brows", hair_mat,
                               chars.brow_strokes(body, w_in=0.0072, w_out=0.0028, arch=0.0065, z_off=0.027) if kid else chars.brow_strokes(body))
    eyes += chars.eye_decals(body, rig, name + "_eye", M["EYE_WHITE"], M["EYE_IRIS"], M["EYE_HL"],
                             w=0.032 if kid else 0.029, h=0.015 if kid else 0.0115, iris_r=0.0068 if kid else 0.0056, lash_mat=M["EYE_LASH"])
    extra = []
    if moustache is not None:
        extra.append(chars.face_ribbons(body, rig, name + "_moustache", hair_mat, chars.moustache_strokes(body, **moustache)))
    chars.outline_all([body, shell] + cloth, 0.0045, OUTLINE)
    chars.outline_all([locks], 0.0025, OUTLINE)
    # collection
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    allobs = [rig, body, shell, locks, brows] + cloth + eyes + extra
    for o in allobs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
    return rig


CAST = {}
CAST["FATHER_75_HOME"] = build("FATHER_75_HOME", 28, 0.0, dict(weight=0.46, muscle=0.55, height=0.42, prop=0.55),
                               [("kurta", M["WHITE"]), ("pajama", M["WHITE"])], "70s", M["HAIR"], M["SKIN"], moustache={})
CAST["FATHER_75_WORK"] = build("FATHER_75_WORK", 30, 1.5, dict(weight=0.44, muscle=0.58, height=0.42, prop=0.55),
                               [("shirt", M["SHIRT_WORK"], "half", True), ("trousers", M["TROUSER"]), ("shoes", M["SHOES"])], "70s", M["HAIR"], M["SKIN"], moustache={})
CAST["FATHER_92"] = build("FATHER_92", 45, 3.0, dict(weight=0.6, muscle=0.5, height=0.41, prop=0.5),
                          [("shirt", M["SHIRT_92"], "full", True), ("vest", M["VEST"]), ("trousers", M["TROUSER"]), ("shoes", M["SHOES"])], "70s", M["HAIR_GREY"], M["SKIN"],
                          moustache=dict(width=0.035, z_top=0.02, droop=0.013, w_c=0.014, w_e=0.0055))
CAST["BOY_75"] = build("BOY_75", 5, 4.5, dict(weight=0.45, muscle=0.5, height=0.5, prop=0.5),
                       [("shirt", M["SHIRT_BOY"], "half", True), ("shorts", M["SHORTS"])], "boy", M["HAIR"], M["SKIN_BOY"], part_x=-0.02, fringe_dir=1.0, lock_count=55)
CAST["BOY_79"] = build("BOY_79", 9, 5.5, dict(weight=0.42, muscle=0.5, height=0.5, prop=0.5),
                       [("shirt", M["SHIRT_BOY"], "half", True), ("shorts", M["SHORTS"])], "boy", M["HAIR"], M["SKIN_BOY"], part_x=-0.02, fringe_dir=1.0, lock_count=55)
CAST["BOY_81"] = build("BOY_81", 11, 6.6, dict(weight=0.42, muscle=0.5, height=0.5, prop=0.5),
                       [("shirt", M["SHIRT_BOY"], "half", True), ("shorts", M["SHORTS"])], "boy", M["HAIR"], M["SKIN_BOY"], part_x=-0.025, fringe_dir=1.0, lock_count=60)
CAST["SON_92"] = build("SON_92", 22, 7.8, dict(weight=0.42, muscle=0.55, height=0.55, prop=0.6),
                       [("shirt", M["SHIRT_SON"], "full", True), ("trousers", M["TROUSER_SON"]), ("shoes", M["SHOES"])], "70s", M["HAIR"], M["SKIN"],
                       moustache=dict(width=0.03, z_top=0.018, droop=0.008, w_c=0.008, w_e=0.003), part_x=-0.03, fringe_dir=1.0)

af.save(os.path.join(af.ASSETS, os.environ.get("AF_CHARS_OUT", "chars_v2.blend")))
print("AF: cast built", list(CAST))
