# ALWAYS FALLING - V3 "set detail" pass (team feedback: "so low poly").
# The characters hold up; the SETS read as a blockout: flat-coloured boxes with razor edges and no surface life.
#   * every cel material that is NOT on a character gets painted variation multiplied into its colour:
#       soft large mottling (like a painted background), fine grain, and coloured contact shadows (AO) in corners,
#       under ledges and where things meet the ground - the depth cue the flat boxes were missing
#   * box-like set meshes get a small chamfer so edges catch the light like drawn edges instead of CG razor cuts
# Characters, faces, skies, stars, the Earth and emissive lights are left untouched.
import bpy, math

SPACE = {"C3d", "C4", "D1", "D2", "H1", "I2a", "I2b", "I2c"}      # orbit / re-entry: no sets to dress
TINT = (0.33, 0.27, 0.48, 1.0)                                      # contact shadows lean cool violet (linear)


def _char_objects():
    out = set()
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        arm = any(md.type == "ARMATURE" for md in ob.modifiers)
        par = ob.parent is not None and ob.parent.type == "ARMATURE"
        if arm or par:
            out.add(ob)
    return out


def _paint_chain(nt, col_sock, ao_dist):
    N = nt.nodes.new
    geo = N("ShaderNodeNewGeometry")
    geo.location = (-1400, -700)
    # soft large mottling: ~3 m blotches, +-10%
    n1 = N("ShaderNodeTexNoise")
    n1.location = (-1200, -600)
    n1.inputs["Scale"].default_value = 0.32
    n1.inputs["Detail"].default_value = 3.0
    n1.inputs["Roughness"].default_value = 0.55
    nt.links.new(geo.outputs["Position"], n1.inputs["Vector"])
    m1 = N("ShaderNodeMapRange")
    m1.location = (-1000, -600)
    m1.inputs["From Min"].default_value, m1.inputs["From Max"].default_value = 0.32, 0.68
    m1.inputs["To Min"].default_value, m1.inputs["To Max"].default_value = 0.87, 1.09
    nt.links.new(n1.outputs["Fac"], m1.inputs["Value"])
    # fine grain: ~10 cm, +-4%
    n2 = N("ShaderNodeTexNoise")
    n2.location = (-1200, -850)
    n2.inputs["Scale"].default_value = 9.0
    n2.inputs["Detail"].default_value = 2.0
    nt.links.new(geo.outputs["Position"], n2.inputs["Vector"])
    m2 = N("ShaderNodeMapRange")
    m2.location = (-1000, -850)
    m2.inputs["From Min"].default_value, m2.inputs["From Max"].default_value = 0.35, 0.65
    m2.inputs["To Min"].default_value, m2.inputs["To Max"].default_value = 0.955, 1.035
    nt.links.new(n2.outputs["Fac"], m2.inputs["Value"])
    mot = nt.nodes.new("ShaderNodeMath")
    mot.operation = "MULTIPLY"
    mot.location = (-800, -700)
    nt.links.new(m1.outputs["Result"], mot.inputs[0])
    nt.links.new(m2.outputs["Result"], mot.inputs[1])
    # contact shadows
    ao = N("ShaderNodeAmbientOcclusion")
    ao.location = (-1200, -1050)
    ao.samples = 12
    ao.inputs["Distance"].default_value = ao_dist
    m3 = N("ShaderNodeMapRange")
    m3.location = (-1000, -1050)
    m3.inputs["From Min"].default_value, m3.inputs["From Max"].default_value = 0.15, 0.95
    m3.inputs["To Min"].default_value, m3.inputs["To Max"].default_value = 0.0, 1.0
    nt.links.new(ao.outputs["AO"], m3.inputs["Value"])
    aoc = N("ShaderNodeMix")
    aoc.data_type = "RGBA"
    aoc.blend_type = "MIX"
    aoc.location = (-800, -1000)
    aoc.inputs["A"].default_value = TINT
    aoc.inputs["B"].default_value = (1.0, 1.0, 1.0, 1.0)
    nt.links.new(m3.outputs["Result"], aoc.inputs["Factor"])
    # colour x AO tint x mottling
    mul1 = N("ShaderNodeMix")
    mul1.data_type = "RGBA"
    mul1.blend_type = "MULTIPLY"
    mul1.location = (-600, -500)
    mul1.inputs["Factor"].default_value = 0.62                  # how strong the contact shadow is
    nt.links.new(col_sock, mul1.inputs["A"])
    nt.links.new(aoc.outputs["Result"], mul1.inputs["B"])
    mul2 = N("ShaderNodeVectorMath")
    mul2.operation = "SCALE"
    mul2.location = (-400, -500)
    nt.links.new(mul1.outputs["Result"], mul2.inputs["Vector"])
    nt.links.new(mot.outputs["Value"], mul2.inputs["Scale"])
    return mul2.outputs["Vector"]


def dress_materials(char_obs, ao_dist=0.9):
    char_mats = set()
    for ob in char_obs:
        for s in ob.material_slots:
            if s.material:
                char_mats.add(s.material.name)
    n = 0
    for m in bpy.data.materials:
        if m.name in char_mats or not m.node_tree or m.get("af_detail"):
            continue
        nt = m.node_tree
        if not any(nd.bl_idname == "ShaderNodeValToRGB" and (nd.name.startswith("TOON_RAMP") or nd.label.startswith("TOON_RAMP"))
                   for nd in nt.nodes):
            continue                                             # flat/emissive materials: lights, sky cards, moon
        em = next((nd for nd in nt.nodes if nd.bl_idname == "ShaderNodeEmission"), None)
        if em is None or not em.inputs["Color"].is_linked:
            continue
        lk = em.inputs["Color"].links[0]
        src = lk.from_socket
        nt.links.remove(lk)
        out = _paint_chain(nt, src, ao_dist)
        nt.links.new(out, em.inputs["Color"])
        m["af_detail"] = 1
        n += 1
    return n


def bevel_sets(char_obs):
    n = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob in char_obs or ob.data is None:
            continue
        if any(md.type in ("BEVEL", "SUBSURF", "ARMATURE") for md in ob.modifiers):
            continue
        me = ob.data
        if len(me.polygons) == 0 or len(me.polygons) > 64:
            continue
        d = sorted(ob.dimensions)
        if d[0] < 0.04:                                          # planes, cards, wires, decals: leave alone
            continue
        if not any(s.material and s.material.get("af_detail") for s in ob.material_slots):
            continue                                             # only dressed (cel) set pieces
        sc = max(ob.scale) if max(ob.scale) > 0 else 1.0
        b = ob.modifiers.new("AF_Bevel", "BEVEL")
        b.width = min(0.035, 0.12 * d[0]) / sc
        b.segments = 2
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(40)
        b.use_clamp_overlap = True
        try:
            ob.modifiers.move(len(ob.modifiers) - 1, 0)          # before the outline shell
        except Exception:
            pass
        n += 1
    return n


def calm_catchlights(strength=1.1):
    """eye highlights at 1.6 bloomed into 'glowing eyes' in the night close-ups; keep them bright but not luminous"""
    for nm in ("EYE_HL", "AF_sparkle"):
        m = bpy.data.materials.get(nm)
        if m and m.node_tree:
            for nd in m.node_tree.nodes:
                if nd.bl_idname == "ShaderNodeEmission":
                    nd.inputs["Strength"].default_value = min(nd.inputs["Strength"].default_value, strength)


def apply(sid):
    calm_catchlights()
    if sid in SPACE:
        print("AF: detail pass skipped (space)", sid)
        return
    ch = _char_objects()
    nm = dress_materials(ch)
    nb = bevel_sets(ch)
    print("AF: detail pass", sid, "materials", nm, "bevels", nb)
