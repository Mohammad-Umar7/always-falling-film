# 92,000 orbits: precessing rings around the Earth, revealed progressively (geometry nodes delete by index)
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
import af


def ring_mesh(name, n_rings, r0, r1, incl_deg=50.7, seg=160, width=5.0, seed=1, base=None):
    """One mesh holding n_rings flat ribbons; integer attribute 'ring' = order of appearance.
    Node angle advances by the golden angle (uniform cocoon); radius decays r0 -> r1 (orbit decay)."""
    bm_ = bmesh.new()
    lay = bm_.verts.layers.int.new("ring")
    col = bm_.verts.layers.float.new("hue")
    inc = math.radians(incl_deg)
    golden = math.pi * (3 - math.sqrt(5))
    for k in range(n_rings):
        t = k / max(1, n_rings - 1)
        r = r0 + (r1 - r0) * (t ** 3)
        node = k * golden
        M = (base if base is not None else Matrix.Identity(4)) @ Matrix.Rotation(node, 4, "Z") @ Matrix.Rotation(inc, 4, "X")
        ring_v = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            p = Vector((math.cos(a) * r, math.sin(a) * r, 0.0))
            radial = p.normalized()
            for s_ in (-1, 1):
                v = bm_.verts.new((M @ (p + radial * s_ * width * 0.5)).to_3d())
                v[lay] = k
                v[col] = (k % 2)
                ring_v.append(v)
        for i in range(seg):
            a0, a1 = ring_v[2 * i], ring_v[2 * i + 1]
            b0, b1 = ring_v[(2 * i + 2) % (2 * seg)], ring_v[(2 * i + 3) % (2 * seg)]
            bm_.faces.new((a0, a1, b1, b0))
    me = bpy.data.meshes.new(name)
    bm_.to_mesh(me)
    bm_.free()
    ob = af.link(bpy.data.objects.new(name, me))
    return ob


def reveal_modifier(ob, count_keys):
    """Geometry Nodes: delete geometry whose 'ring' >= Count (animated via keyframes on the modifier input)."""
    ng = bpy.data.node_groups.new("AF_reveal_rings", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    cs = ng.interface.new_socket("Count", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput")
    na = ng.nodes.new("GeometryNodeInputNamedAttribute")
    na.data_type = "INT"
    na.inputs["Name"].default_value = "ring"
    cmp = ng.nodes.new("FunctionNodeCompare")
    cmp.data_type = "FLOAT"
    cmp.operation = "GREATER_EQUAL"
    dl = ng.nodes.new("GeometryNodeDeleteGeometry")
    dl.domain = "POINT"
    ng.links.new(na.outputs["Attribute"], cmp.inputs[0])
    ng.links.new(gi.outputs["Count"], cmp.inputs[1])
    ng.links.new(gi.outputs["Geometry"], dl.inputs["Geometry"])
    ng.links.new(cmp.outputs["Result"], dl.inputs["Selection"])
    ng.links.new(dl.outputs["Geometry"], go.inputs["Geometry"])
    md = ob.modifiers.new("reveal", "NODES")
    md.node_group = ng
    ident = [it.identifier for it in ng.interface.items_tree if getattr(it, "name", "") == "Count" and it.in_out == "INPUT"][0]
    for f, c in count_keys:
        md[ident] = float(c)
        ob.keyframe_insert(f'modifiers["reveal"]["{ident}"]', frame=f)
    return md


def ring_material(gold="#FFC861", blue="#6FB8FF", strength=0.9):
    """Additive glow: transparent + emission (lets the Earth show through, overlaps brighten)."""
    m, nt = af.new_mat("orbit_glow")
    attr = af.N(nt, "ShaderNodeAttribute")
    attr.attribute_name = "hue"
    c = af.mixcol(nt, af.O(attr, "Fac"), gold, blue)
    em = af.N(nt, "ShaderNodeEmission")
    af.L(nt, c, af.I(em, "Color"))
    af.I(em, "Strength").default_value = strength
    tr = af.N(nt, "ShaderNodeBsdfTransparent")
    add = af.N(nt, "ShaderNodeAddShader")
    af.L(nt, af.O(tr, "BSDF"), add.inputs[0])
    af.L(nt, af.O(em, "Emission"), add.inputs[1])
    out = af.N(nt, "ShaderNodeOutputMaterial")
    af.L(nt, add.outputs[0], af.I(out, "Surface"))
    m.surface_render_method = "BLENDED"
    m.use_backface_culling = False
    return m


def trail_circle(name, center, radius, start_dir, travel_dir, f0, f1, depth=0.25, color="#FFD27A", strength=6.0):
    """Glowing trail drawn behind the satellite along its orbit (curve circle, bevel_factor animated)."""
    c = Vector(center)
    u = Vector(start_dir).normalized()
    v = Vector(travel_dir).normalized()
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = depth
    cu.bevel_resolution = 3
    sp_ = cu.splines.new("POLY")
    n = 720
    sp_.points.add(n - 1)
    for i in range(n):
        a = -2 * math.pi * i / (n - 1)
        p = c + (u * math.cos(a) + v * math.sin(a)) * radius
        sp_.points[i].co = (p.x, p.y, p.z, 1)
    m = af.flat_mat(name + "_m", color, strength=strength)
    cu.materials.append(m)
    ob = af.link(bpy.data.objects.new(name, cu))
    cu.bevel_factor_mapping_end = "SPLINE"
    cu.bevel_factor_end = 0.0
    cu.keyframe_insert("bevel_factor_end", frame=f0)
    cu.bevel_factor_end = 1.0
    cu.keyframe_insert("bevel_factor_end", frame=f1)
    return ob
