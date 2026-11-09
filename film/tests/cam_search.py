# Find a camera for a two-character shot by ray casting: both faces unoccluded, both inside the frame, as close
# as possible. blender -b --factory-startup -P tests/cam_search.py -- preset=I4W
import bpy, os, sys, math
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, "shots", "half.py"), encoding="utf-8").read()
src = src.replace('S = globals()["P_" + PRESET]()\nS.finish(step=2)', "")
g = {"__file__": os.path.join(ROOT, "shots", "half.py"), "__name__": "half_search"}
exec(compile(src, "half.py", "exec"), g)
PRESET = g["PRESET"]
S = g["P_" + PRESET]()
sc = bpy.context.scene
sc.frame_set(120)
dg = bpy.context.evaluated_depsgraph_get()

rigs = {o.name.split(".")[0]: o for o in sc.objects if o.type == "ARMATURE" and "head" in o.pose.bones}
heads = {}
for nm, r in rigs.items():
    pb = r.pose.bones["head"]
    heads[nm] = r.matrix_world @ (pb.head.lerp(pb.tail, 0.45))
print("HEADS", {k: tuple(round(c, 2) for c in v) for k, v in heads.items()})


def owner(ob):
    while ob is not None:
        if ob.type == "ARMATURE":
            return ob.name.split(".")[0]
        for md in getattr(ob, "modifiers", []):
            if md.type == "ARMATURE" and md.object is not None:
                return md.object.name.split(".")[0]
        ob = ob.parent
    return None


def visible(c, nm):
    t = heads[nm]
    d = t - c
    L = d.length
    hit, loc, nrm, idx, ob, mw = sc.ray_cast(dg, c, d.normalized(), distance=L + 0.5)
    if not hit:
        return True
    if (loc - c).length >= L - 0.25:
        return True
    return owner(ob) == nm


def inside(c):
    for d in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((0, 0, -1))):
        hit, loc, *_ = sc.ray_cast(dg, c, d, distance=0.35)
        if hit:
            return True
    return False


names = list(heads)
A, B = heads[names[0]], heads[names[1]]
best = []
lo = min(A.z, B.z) - 1.0
xs = [x * 0.5 for x in range(-8, 21)]
ys = [-8.0 + 0.25 * i for i in range(0, 25)]
zs = [lo + 0.6 * i for i in range(0, 16)]
for x in xs:
    for y in ys:
        for z in zs:
            c = Vector((x, y, z))
            da, db = (A - c), (B - c)
            if da.length < 1.2 or db.length < 1.2:
                continue
            ang = math.degrees(da.angle(db))
            if ang > 36:
                continue
            if inside(c) or not visible(c, names[0]) or not visible(c, names[1]):
                continue
            # faces toward the camera? (head forward axis = -Y of the head bone in MPFB... use the rig's facing)
            score = da.length + db.length + 0.04 * ang
            best.append((score, tuple(round(v, 2) for v in c), round(ang, 1), round(da.length, 1), round(db.length, 1)))
best.sort()
print("CANDIDATES", len(best))
for b in best[:25]:
    print("CAM", b)
