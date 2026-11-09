# Batch of fixes to shots/half.py: seated characters, cameras, props.
ROOT = __file__.rsplit("tests", 1)[0]
p = ROOT + "shots/half.py"
s = open(p, encoding="utf-8-sig").read()


def rep(a, b):
    global s
    assert a in s, "MISSING: " + a[:80]
    s = s.replace(a, b, 1)


rep('''def bone_tail(rig, bone):''', '''def seat(rig, seat_z):
    bpy.context.view_layer.update()
    pz = (rig.matrix_world @ rig.pose.bones["pelvis.L"].head).z
    rig.location.z += (seat_z + 0.07) - pz
    bpy.context.view_layer.update()


def bone_tail(rig, bone):''')
# F1L
rep('''    poses.key_sequence(boy, [(1, sitp), (90, sitp), (102, look), (150, look), (162, sitp), (240, sitp)], step=3)''',
    '''    poses.key_sequence(boy, [(1, sitp), (90, sitp), (102, look), (150, look), (162, sitp), (240, sitp)], step=3)
    bpy.context.scene.frame_set(1)
    seat(boy, 0.53)''')
# F2L: player to the ear
rep('''    poses.apply(boy, poses.merge(poses.SIT, {"head": (6, 0, -14), "upperarm01.L": (20, 0, -10), "lowerarm01.L": (125, 0, 0)}), frame=1)
    A = sets_auh.Auh(time="night")''', '''    poses.apply(boy, poses.merge(poses.SIT, {"head": (10, 0, -16)}), frame=1)
    seat(boy, 0.53)
    ear = bone_tail(boy, "head")
    eh = scene_b.ik_arm(boy, "L", ear + Vector((0.12, 0.02, -0.12)))
    A = sets_auh.Auh(time="night")''')
rep('''    S.cam("cam", keys=[(1, (1.5, -0.55, 1.05), (0.42, 0.25, 1.05), 40.0), (240, (1.42, -0.5, 1.05), (0.42, 0.25, 1.05), 42.0)])''',
    '''    S.cam("cam", keys=[(1, (1.15, -0.75, 1.25), (0.42, 0.25, 1.2), 34.0), (240, (1.1, -0.7, 1.25), (0.42, 0.25, 1.22), 36.0)])''')
# F5L
rep('''    place(boy, (-1.1, -0.2, 0.52), 90)
    poses.apply(boy, poses.merge(poses.SIT, {"head": (20, 0, 0), "upperarm01.L": (30, 0, -20), "lowerarm01.L": (90, 0, 0),
                                             "upperarm01.R": (30, 0, 20), "lowerarm01.R": (90, 0, 0)}), frame=1)''',
    '''    place(boy, (-1.15, -0.2, 0.0), 90)
    poses.apply(boy, poses.merge(poses.SIT, {"head": (20, 0, 0), "upperarm01.L": (30, 0, -20), "lowerarm01.L": (90, 0, 0),
                                             "upperarm01.R": (30, 0, 20), "lowerarm01.R": (90, 0, 0)}), frame=1)
    seat(boy, 0.52)''')
# G1L
rep('''    place(boy, (-1.1, -0.2, 0.52), 90)
    a = poses.merge(''', '''    place(boy, (-1.15, -0.2, 0.0), 90)
    a = poses.merge(''')
rep('''    poses.key_sequence(boy, [(1, a), (120, a), (140, b), (192, b)], step=3)''',
    '''    poses.key_sequence(boy, [(1, a), (120, a), (140, b), (192, b)], step=3)
    bpy.context.scene.frame_set(1)
    seat(boy, 0.52)''')
# F5R
rep('''    place(fa, (-1.1, -0.35, 0.57), 90)''', '''    place(fa, (-1.1, -0.35, 0.0), 90)''')
rep('''"upperarm01.R": (30, 0, 26), "lowerarm01.R": (60, 0, 0)}), frame=1)
    S.cam("cam", keys=[(1, (1.3, -1.4, 1.35), (-0.6, 0.4, 0.95), 28.0)''',
    '''"upperarm01.R": (30, 0, 26), "lowerarm01.R": (60, 0, 0)}), frame=1)
    seat(fa, 0.69)
    S.cam("cam", keys=[(1, (1.3, -1.4, 1.35), (-0.6, 0.4, 0.95), 28.0)''')
# E1R
rep('''    poses.apply(fa, poses.merge(poses.SIT, {"head": (18, 0, 0), "neck01": (10, 0, 0)}), frame=1)
    fa.location.z = 0.0''', '''    poses.apply(fa, poses.merge(poses.SIT, {"head": (18, 0, 0), "neck01": (10, 0, 0)}), frame=1)
    seat(fa, 0.47)''')
rep('''    S.cam("cam", keys=[(1, (0.55, 0.45, 1.25), (0.98, 0.95, 0.76), 34.0), (144, (0.58, 0.5, 1.2), (0.98, 0.95, 0.76), 36.0)])''',
    '''    S.cam("cam", keys=[(1, (1.45, 1.35, 1.12), (0.95, 0.88, 0.8), 34.0), (144, (1.42, 1.32, 1.1), (0.95, 0.88, 0.8), 36.0)])''')
# F2R
rep('''    poses.apply(fa, poses.merge(poses.SIT, {"head": (20, 0, 0), "neck01": (12, 0, 0)}), frame=1)
    eh = scene_b.ik_arm(fa, "R", Vector((0.82, 1.0, 0.85)))''', '''    poses.apply(fa, poses.merge(poses.SIT, {"head": (20, 0, 0), "neck01": (12, 0, 0)}), frame=1)
    seat(fa, 0.47)
    eh = scene_b.ik_arm(fa, "R", Vector((0.82, 1.0, 0.85)))''')
# E2R
rep('''    S.cam("cam", keys=[(1, (0.75, -1.35, 1.2), (0.0, -0.25, 1.05), 40.0), (144, (0.72, -1.3, 1.18), (0.0, -0.25, 1.05), 42.0)])''',
    '''    S.cam("cam", keys=[(1, (-0.95, -0.75, 1.25), (0.0, -0.3, 1.05), 36.0), (144, (-0.92, -0.72, 1.23), (0.0, -0.3, 1.05), 38.0)])''')
# E3L
rep('''    S.cam("cam", keys=[(1, (0.66, -2.2, 0.75), (0.52, -6.0, 3.6), 30.0), (192, (0.66, -2.25, 0.75), (0.52, -6.0, 3.7), 31.0)])''',
    '''    S.cam("cam", keys=[(1, (0.95, -1.75, 0.55), (0.5, -3.4, 1.35), 30.0), (192, (0.94, -1.8, 0.55), (0.5, -3.4, 1.4), 31.0)])''')
# F3L / F3R
rep('''    S.cam("cam", keys=[(1, (0.2, -1.1, 1.6), (1.7, 0.2, 1.62), 30.0), (240, (0.3, -1.0, 1.6), (1.7, 0.25, 1.62), 30.0)])''',
    '''    S.cam("cam", keys=[(1, (0.9, -0.2, 1.62), (1.62, 0.15, 1.65), 34.0), (240, (0.95, -0.15, 1.62), (1.62, 0.2, 1.65), 36.0)])''')
rep('''    S.cam("cam", keys=[(1, (0.2, 0.0, 1.5), (1.5, 0.45, 1.5), 30.0), (240, (0.25, 0.05, 1.48), (1.5, 0.5, 1.48), 30.0)])''',
    '''    S.cam("cam", keys=[(1, (0.55, 0.3, 1.3), (1.0, 0.92, 0.85), 34.0), (240, (0.58, 0.33, 1.28), (1.0, 0.92, 0.85), 36.0)])''')
# I1L
rep('''    place(son, (0.9, -4.55, 0.55), 0)
    sitp = poses.merge(poses.SIT, {"head": (16, 0, 0), "neck01": (6, 0, 0), "upperarm01.L": (20, 0, -30), "upperarm01.R": (20, 0, 30)})
    poses.apply(son, sitp, frame=1)''', '''    place(son, (0.9, -5.0, 0.0), 0)
    sitp = poses.merge(poses.SIT, {"head": (16, 0, 0), "neck01": (6, 0, 0), "upperarm01.L": (20, 0, -30), "upperarm01.R": (20, 0, 30)})
    poses.apply(son, sitp, frame=1)
    seat(son, 1.01)''')
# I3L
rep('''    place(son, (0.9, -4.55, 0.55), 0)
    down = poses.merge(''', '''    place(son, (0.9, -5.0, 0.0), 0)
    down = poses.merge(''')
rep('''    poses.key_sequence(son, [(1, down), (40, down), (52, up), (168, up)], step=2)''', '''    poses.key_sequence(son, [(1, down), (40, down), (52, up), (168, up)], step=2)
    bpy.context.scene.frame_set(1)
    seat(son, 1.01)''')
# I1R / I3R
rep('''    place(fa, (1.6, -6.4, sets_hyd.LANE_Z), 200)
    poses.apply(fa, poses.merge(poses.STAND, poses.HOLD_SUITCASE_R, {"head": (8, 0, 0)}), frame=1)''',
    '''    place(fa, (1.55, -6.55, sets_hyd.LANE_Z), 180)
    poses.apply(fa, poses.merge(poses.STAND, poses.HOLD_SUITCASE_R, {"head": (10, 0, 0)}), frame=1)''')
rep('''    S.cam("cam", keys=[(1, (0.6, -7.6, sets_hyd.LANE_Z + 1.2), (1.9, -5.6, sets_hyd.LANE_Z + 1.25), 40.0),
                       (192, (0.62, -7.55, sets_hyd.LANE_Z + 1.2), (1.9, -5.6, sets_hyd.LANE_Z + 1.28), 42.0)])''',
    '''    S.cam("cam", keys=[(1, (1.85, -5.7, sets_hyd.LANE_Z + 1.35), (1.45, -7.6, sets_hyd.LANE_Z + 1.2), 38.0),
                       (192, (1.84, -5.72, sets_hyd.LANE_Z + 1.35), (1.45, -7.6, sets_hyd.LANE_Z + 1.22), 40.0)])''')
rep('''    place(fa, (1.6, -6.4, sets_hyd.LANE_Z), 200)
    down = poses.merge(poses.STAND, poses.HOLD_SUITCASE_R, {"head": (8, 0, 0)})''',
    '''    place(fa, (1.55, -6.55, sets_hyd.LANE_Z), 180)
    down = poses.merge(poses.STAND, poses.HOLD_SUITCASE_R, {"head": (10, 0, 0)})''')
rep('''    S.cam("cam", keys=[(1, (1.1, -7.4, sets_hyd.LANE_Z + 1.25), (1.65, -6.3, sets_hyd.LANE_Z + 1.75), 46.0),
                       (168, (1.12, -7.35, sets_hyd.LANE_Z + 1.25), (1.65, -6.3, sets_hyd.LANE_Z + 1.8), 48.0)])''',
    '''    S.cam("cam", keys=[(1, (1.75, -5.75, sets_hyd.LANE_Z + 1.2), (1.5, -7.2, sets_hyd.LANE_Z + 1.7), 42.0),
                       (168, (1.74, -5.77, sets_hyd.LANE_Z + 1.2), (1.5, -7.2, sets_hyd.LANE_Z + 1.75), 44.0)])''')
# I4W
rep('''    S.cam("cam", keys=[(1, (3.6, -1.8, 3.2), (1.3, -6.6, -4.2), 26.0), (240, (3.9, -1.2, 3.8), (1.35, -6.6, -4.4), 26.0)])''',
    '''    S.cam("cam", keys=[(1, (1.9, -3.9, 2.25), (1.5, -6.9, -5.6), 24.0), (240, (2.1, -3.6, 2.6), (1.5, -6.9, -5.8), 22.0)])''')
# J1
rep('''    S.cam("cam", keys=[(1, (1.35, -5.15, 1.45), (1.5, -6.6, sets_hyd.LANE_Z + 1.3), 32.0), (192, (1.35, -5.18, 1.42), (1.5, -6.6, sets_hyd.LANE_Z + 1.4), 38.0)])''',
    '''    S.cam("cam", keys=[(1, (1.35, -5.65, 1.55), (1.5, -6.7, sets_hyd.LANE_Z + 1.4), 30.0), (192, (1.35, -5.68, 1.5), (1.5, -6.7, sets_hyd.LANE_Z + 1.5), 36.0)])''')
# J3
rep('''    S.cam("cam", keys=[(1, (0.6, -6.9, sets_hyd.LANE_Z + 1.45), (1.35, -5.6, sets_hyd.LANE_Z + 1.2), 40.0), (120, (0.65, -6.95, sets_hyd.LANE_Z + 1.45), (1.35, -5.6, sets_hyd.LANE_Z + 1.25), 40.0)])''',
    '''    S.cam("cam", keys=[(1, (-0.4, -6.6, sets_hyd.LANE_Z + 1.5), (1.4, -5.75, sets_hyd.LANE_Z + 1.2), 32.0), (120, (-0.35, -6.65, sets_hyd.LANE_Z + 1.5), (1.4, -5.75, sets_hyd.LANE_Z + 1.25), 32.0)])''')
# K1W
rep('''    S.cam("cam", keys=[(1, (-0.25, -0.9, 1.1), (-0.25, 6.0, 3.8), 34.0), (240, (-0.4, -9.0, 4.5), (-0.3, 8.0, 4.0), 24.0)])''',
    '''    S.cam("cam", keys=[(1, (-0.25, -0.9, 1.1), (-0.25, 6.0, 3.8), 34.0), (240, (-0.3, -4.2, 2.4), (-6.0, 60.0, 8.0), 26.0)])''')
open(p, "w", encoding="utf-8").write(s)
import ast
ast.parse(s)
print("half patch ok")
