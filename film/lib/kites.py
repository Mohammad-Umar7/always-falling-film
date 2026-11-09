# V4: kites over the Old City at dusk (Hyderabad flies them from every roof) - the sky is never a still picture.
# Each kite is a bowed diamond (patang) with a small tail, dancing on noise: bobbing, swaying, drifting downwind.
import bpy, bmesh, math, random
from mathutils import Vector
import af

COLS = ["#E8336A", "#FFC233", "#2EC27E", "#F05A28", "#3FB6F0", "#B04FE0", "#FFFFFF"]


def _kite_mesh(name, size):
    bm = bmesh.new()
    w, h = size * 0.5, size * 0.62
    v = [bm.verts.new(p) for p in ((0, 0, h), (w, -0.06 * size, 0), (0, 0, -h * 0.8), (-w, -0.06 * size, 0), (0, 0.04 * size, 0))]
    for a, b in ((0, 1), (1, 2), (2, 3), (3, 0)):
        bm.faces.new((v[a], v[b], v[4]))
    # tail: two little triangles hanging from the bottom tip
    t0 = bm.verts.new((0, 0, -h * 0.8))
    t1 = bm.verts.new((-0.12 * size, 0, -h * 1.35))
    t2 = bm.verts.new((0.12 * size, 0, -h * 1.35))
    bm.faces.new((t0, t1, t2))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    af.link(ob)
    return ob


def fly(cam_pos, view_dir, n=6, dist=(70.0, 120.0), height=(9.0, 18.0), spread=0.45, size=1.4, frames=144, seed=3):
    """n kites scattered around view_dir (horizontal), dist metres out, dancing for `frames`"""
    rng = random.Random(seed)
    vd = Vector((view_dir[0], view_dir[1], 0)).normalized()
    side = vd.cross(Vector((0, 0, 1))).normalized()
    obs = []
    for i in range(n):
        d = rng.uniform(*dist)
        p = Vector(cam_pos) + vd * d + side * (d * rng.uniform(-spread, spread))
        p.z = rng.uniform(*height)
        ob = _kite_mesh(f"kite_{i}", size * rng.uniform(0.85, 1.25))
        col = COLS[i % len(COLS)]
        mat = af.flat_mat(f"kite_mat_{i}", col, strength=1.15)
        ob.data.materials.append(mat)
        ob.location = p
        yaw = math.atan2(-vd.x, vd.y) + rng.uniform(-0.6, 0.6)        # roughly facing the camera
        ob.rotation_euler = (math.radians(rng.uniform(-12, 12)), 0, yaw)
        ob.keyframe_insert("location", frame=1)
        ob.keyframe_insert("rotation_euler", frame=1)
        for fc in af._fcurves(ob.animation_data.action):
            m = fc.modifiers.new("NOISE")
            m.blend_type = "ADD"
            if fc.data_path == "location":
                m.strength = (1.6, 1.6, 1.2)[fc.array_index] * size
                m.scale = rng.uniform(26, 40)
            else:
                m.strength = math.radians((26, 30, 22)[fc.array_index])
                m.scale = rng.uniform(14, 24)                         # the quick twitch of a kite in gusts
            m.phase = rng.uniform(0, 100)
        obs.append(ob)
    return obs
