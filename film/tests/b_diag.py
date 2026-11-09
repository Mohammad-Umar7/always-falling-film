import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, scene_b, poses

af.clear_scene()
af.setup_scene(samples=8, w=960, h=540)
H, rigs = scene_b.night_roof(moon_dir=(0.62, 0.16, 0.77), clouds=False)
fa, boy = rigs["FATHER_75_HOME"], rigs["BOY_75"]
poses.apply(fa, poses.LIE_POINT_L)
poses.apply(boy, poses.merge(poses.LIE, {"head": (-14, -6, 0)}))
bpy.context.view_layer.update()


def wp(rig, bone, tail=True):
    b = rig.pose.bones[bone]
    return tuple(round(x, 3) for x in (rig.matrix_world @ (b.tail if tail else b.head)))


for nm, r in (("FA", fa), ("BOY", boy)):
    for bn in ("head", "neck01", "lowerarm02.L", "lowerarm02.R", "upperarm01.L", "upperarm01.R", "finger2-3.L", "foot.L"):
        print("AF:", nm, bn, wp(r, bn))
cam = af.add_camera("top", (0.4, 0.4, 3.2), (0.4, 0.45, 0.0), lens=30)
af.render_still(os.path.join(af.ROOT, "tests", "b_diag_top.png"))
