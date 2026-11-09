import bpy, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, "shots", "half.py"), encoding="utf-8").read().replace('S = globals()["P_" + PRESET]()\nS.finish(step=2)', "")
g = {"__file__": os.path.join(ROOT, "shots", "half.py"), "__name__": "probe"}
exec(compile(src, "half.py", "exec"), g)
S = g["P_" + g["PRESET"]]()
sc = bpy.context.scene
for f in (1, 200):
    sc.frame_set(f)
    for o in sc.objects:
        if o.type == "ARMATURE" and "head" in o.pose.bones:
            mw = o.matrix_world
            sh = {sd: tuple(round(v, 2) for v in (mw @ o.pose.bones[f"shoulder01.{sd}"].tail)) for sd in "LR"}
            hand = {sd: tuple(round(v, 2) for v in (mw @ o.pose.bones[f"lowerarm02.{sd}"].tail)) for sd in "LR"}
            print("PROBE", f, o.name, "loc", tuple(round(v, 2) for v in o.location), "shoulders", sh, "hands", hand)
    for o in sc.objects:
        if "_reach_" in o.name:
            print("PROBE", f, o.name, "target", tuple(round(v, 2) for v in o.matrix_world.translation))
