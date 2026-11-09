# B1 (0:15–0:21, 144f): dusk — crane down through circling pigeons to father and son at the parapet, the low sun beyond.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, sets_hyd, poses, birds

S = shot.Shot("B1", frames=144)
H = sets_hyd.Hyd(time="dusk", seed=7, year=1975)
H.build(dressing=False)
H.sky_dressing(clouds=True, cloud_seed=5)
sun_dir = (-Vector(H.P["key_dir"])).normalized()
af.moon("sun", sun_dir * 420, 26.0, phase=5.0, tilt=0.0, col_dark="#FFB070", col_lit="#FFF2CC", glow=0.7, cam_dir=-sun_dir)
H.charpai("hero_charpai", Vector((0.4, 0.6, 0.06)), math.radians(90))
DUSK_CAST = {"SKIN": ("#9A6050", "#4A2A3A", "#E0A07A", "#FFD0A0"), "SKIN_BOY": ("#A06654", "#4C2C3C", "#E6A880", "#FFD0A0"),
             "HAIR": ("#1E1218", "#0C0608", "#4A2C30", "#FFB080"), "CLOTH_WHITE": ("#E0C8C0", "#7A5A78", "#FFF0E0"),
             "CLOTH_SHIRT_BOY": ("#D8C4B8", "#76587A", "#FFEEDC"), "CLOTH_SHORTS": ("#2E3458", "#161A30", "#4A5280"),
             "EYE_WHITE": ("#D8C8C8", "#8A7088", "#F4E8E4")}
rigs = poses.load_chars(["FATHER_75_HOME", "BOY_75"], palette=DUSK_CAST)
fa, boy = rigs["FATHER_75_HOME"], rigs["BOY_75"]
yaw = math.atan2(-sun_dir.x, sun_dir.y) + math.pi
for r, p in ((fa, (-1.05, -4.98, 0.06)), (boy, (-0.38, -5.0, 0.06))):
    r.location = p
    r.rotation_euler = (0, 0, yaw)
lean = {"spine03": (4, 0, 0)}          # arms hang naturally (the old lean rested on air)
poses.key_sequence(fa, [(1, poses.merge(poses.STAND, lean, {"head": (-6, 0, 0)})), (90, poses.merge(poses.STAND, lean, {"head": (-6, 0, 0)})),
                        (104, poses.merge(poses.STAND, lean, {"head": (-4, 22, 0)})), (144, poses.merge(poses.STAND, lean, {"head": (-4, 22, 0)}))], step=3)
poses.key_sequence(boy, [(1, poses.merge(poses.STAND_LOOK_UP_HIGH)), (70, poses.STAND_LOOK_UP_HIGH),
                         (82, poses.merge(poses.STAND, {"head": (-10, 26, 0)})), (144, poses.merge(poses.STAND, {"head": (-10, 26, 0)}))], step=3)
# the father's near hand settles on his son's near shoulder as the crane comes down (local 84-100)
import body
bpy.context.view_layer.update()
fp = fa.matrix_world.translation
side_b = min(("L", "R"), key=lambda sd: (boy.matrix_world @ boy.pose.bones[f"shoulder01.{sd}"].tail - fp).length)
side_f = min(("L", "R"), key=lambda sd: (fa.matrix_world @ fa.pose.bones[f"shoulder01.{sd}"].tail - boy.matrix_world.translation).length)
body.reach_bone(fa, side_f, boy, f"shoulder01.{side_b}", [(1, 0.0), (84, 0.0), (100, 1.0), (144, 1.0)])
pm = af.flat_mat("pigeon_dusk", "#3A2438")
birds.flock(34, (0, 0, 0), radius=(9, 22), height=(5, 15), frames=144, period=(150, 210), mat=pm, seed=4, scale=1.3)
S.cam("cam", keys=[(1, (22.0, 24.0, 30.0), (0.0, -1.0, 6.0), 26.0),
                   (80, (8.0, 6.0, 9.0), (-6.0, -8.0, 3.0), 28.0),
                   (144, (2.3, 0.1, 2.5), (-12.0, -11.0, -0.2), 28.0)])
S.finish(step=1, bloom=(0.85, 0.9, 0.7))
