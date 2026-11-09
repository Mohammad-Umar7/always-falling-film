# Pigeon flock: simple anime silhouettes circling (orbit rhyme), stepped wing flaps.
import bpy, math, random
from mathutils import Vector, Euler
import af


def pigeon(name, mat, scale=1.0):
    body = af.uv_sphere(name, 0.11 * scale, (0, 0, 0), mat, 12, 8)
    body.scale = (1.0, 0.42, 0.42)
    head = af.uv_sphere(name + "_head", 0.035 * scale, (0.1 * scale, 0, 0.03 * scale), mat, 10, 6)
    head.parent = body
    head.matrix_parent_inverse = body.matrix_world.inverted()
    wings = []
    for s in (-1, 1):
        v = [(0.04 * scale, 0, 0), (-0.06 * scale, 0, 0), (-0.09 * scale, s * 0.24 * scale, 0), (0.02 * scale, s * 0.2 * scale, 0)]
        w = af.mesh_obj(f"{name}_wing{s}", v, [(0, 1, 2, 3)], mat)
        w.parent = body
        wings.append(w)
    tail = af.mesh_obj(name + "_tail", [(-0.08 * scale, -0.03 * scale, 0), (-0.08 * scale, 0.03 * scale, 0), (-0.18 * scale, 0.05 * scale, 0), (-0.18 * scale, -0.05 * scale, 0)], [(0, 1, 2, 3)], mat)
    tail.parent = body
    return body, wings


def flock(n, center, radius=(14, 24), height=(7, 16), frames=144, period=(110, 160), mat=None, seed=1, scale=1.0, step=2, flap=3):
    rnd = random.Random(seed)
    c = Vector(center)
    birds = []
    for i in range(n):
        body, wings = pigeon(f"pigeon{i}", mat, scale)
        r = rnd.uniform(*radius)
        h = rnd.uniform(*height)
        per = rnd.uniform(*period)
        ph = rnd.uniform(0, 2 * math.pi)
        bob = rnd.uniform(0.3, 1.2)
        lag = rnd.uniform(0, 1)
        for f in range(1, frames + 1, step):
            a = ph + 2 * math.pi * f / per
            p = c + Vector((math.cos(a) * r, math.sin(a) * r, h + math.sin(a * 2 + lag) * bob))
            tang = Vector((-math.sin(a), math.cos(a), 0))
            body.location = p
            body.rotation_euler = (math.radians(-18), 0, math.atan2(tang.y, tang.x))
            body.keyframe_insert("location", frame=f)
            body.keyframe_insert("rotation_euler", frame=f)
        for f in range(1, frames + 1, flap):
            up = ((f // flap) + i) % 2 == 0
            for s, w in zip((-1, 1), wings):
                w.rotation_euler = (math.radians(s * (55 if up else -25)), 0, 0)
                w.keyframe_insert("rotation_euler", frame=f)
        af.set_interp(body, "LINEAR")
        for w in wings:
            af.set_interp(w, "CONSTANT")
        birds.append(body)
    return birds
