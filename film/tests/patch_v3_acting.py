"""V3 acting beats (body): gaze follows the satellite, the father's raised hand, the boy pointing, a goodbye wave,
the father's hand on his son's shoulder, the final shared look. Signs (YAW, arm axes) are verified with previews."""
ROOT = __file__.rsplit("tests", 1)[0]
p = ROOT + "shots/half.py"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert a in s, "MISSING " + a[:90]
    s = s.replace(a, b, 1)


# ---------------------------------------------------------------- helpers live in lib/body.py
rep('''def bone_tail(rig, bone):''', '''from body import look_track, reach_bone, HEAD_YAW


def bone_tail(rig, bone):''')

# ---------------------------------------------------------------- A2: both follow the dot (timeline 150-250 = local 54-154)
for nm in ("P_A2L", "P_A2R"):
    a = s.index(f"def {nm}():")
    b = s.index("return S", a)
    blk = s[a:b]
    old = '''    poses.apply(son, poses.STAND_LOOK_UP_HIGH, frame=1)
    poses.apply(fa, poses.STAND_LOOK_UP, frame=1)'''
    assert old in blk, nm
    blk = blk.replace(old, '''    look_track(son, poses.STAND_LOOK_UP_HIGH, 54, 154, 432, 14, -14)
    look_track(fa, poses.STAND_LOOK_UP, 58, 158, 432, 14, -14)''')
    s = s[:a] + blk + s[b:]

# ---------------------------------------------------------------- K1W: the dissolve ends (local 110); they turn to each other
a = s.index("def P_K1W():")
b = s.index("return S", a)
blk = s[a:b]
old = '''    poses.apply(son, poses.STAND_LOOK_UP_HIGH, frame=1)
    poses.apply(fa, poses.STAND_LOOK_UP, frame=1)'''
assert old in blk
blk = blk.replace(old, '''    up_s, up_f = poses.STAND_LOOK_UP_HIGH, poses.STAND_LOOK_UP
    to_f = poses.merge(poses.STAND, {"head": (-8, 30 * HEAD_YAW, 0), "neck02": (-4, 10 * HEAD_YAW, 0)})      # son turns to his left
    to_s = poses.merge(poses.STAND, {"head": (-6, -30 * HEAD_YAW, 0), "neck02": (-3, -10 * HEAD_YAW, 0)})    # father turns to his right
    poses.key_sequence(son, [(1, up_s), (122, up_s), (136, to_f), (240, to_f)], step=2)
    poses.key_sequence(fa, [(1, up_f), (128, up_f), (142, to_s), (240, to_s)], step=2)''')
s = s[:a] + blk + s[b:]

# ---------------------------------------------------------------- E1L: the boy's head follows the dot (local 40-120)
rep('''    place(boy, (-1.5, -2.0, 0.06), 90)
    poses.apply(boy, poses.STAND_LOOK_UP_HIGH, frame=1)''', '''    place(boy, (-1.5, -2.0, 0.06), 90)
    look_track(boy, poses.STAND_LOOK_UP_HIGH, 40, 120, 144, 16, -16)''')

# ---------------------------------------------------------------- E3R: the father lifts his hand to the satellite (dot local 52-152)
rep('''    place(fa, (-1.0, -1.2, 6.6), 160)
    poses.apply(fa, poses.STAND_LOOK_UP_HIGH, frame=1)''', '''    place(fa, (-1.0, -1.2, 6.6), 160)
    reach = poses.merge(poses.STAND_LOOK_UP_HIGH, poses._fing("R", 6, 4),
                        {"upperarm01.R": (45, 0, -70), "upperarm02.R": (0, 0, 0), "lowerarm01.R": (25, 0, 0)})
    half_up = poses.blend(poses.STAND_LOOK_UP_HIGH, reach, 0.5)
    poses.key_sequence(fa, [(1, poses.STAND_LOOK_UP_HIGH), (60, poses.STAND_LOOK_UP_HIGH), (72, half_up), (84, reach),
                            (150, reach), (166, half_up), (178, poses.STAND_LOOK_UP_HIGH), (192, poses.STAND_LOOK_UP_HIGH)], step=2)''')

# ---------------------------------------------------------------- F4L: the boy points up at the dot with his free (left) hand
rep('''    poses.apply(boy, poses.merge(poses.STAND_LOOK_UP, poses.FIST_R), frame=1)''', '''    base = poses.merge(poses.STAND_LOOK_UP, poses.FIST_R)
    point = poses.merge(base, poses.POINT_L, {"upperarm01.L": (60, 0, 55), "lowerarm01.L": (10, 0, 0), "head": (-30, 0, 0)})
    poses.key_sequence(boy, [(1, base), (56, base), (66, point), (150, point), (162, base), (240, base)], step=2)''')

# ---------------------------------------------------------------- C1F: the boy waves goodbye (local 34-110)
rep('''    place(boy, (1.4, -6.1, sets_hyd.LANE_Z), 90)
    poses.apply(boy, poses.merge(poses.STAND, {"head": (-4, 0, 0)}), frame=1)''', '''    place(boy, (1.4, -6.1, sets_hyd.LANE_Z), 90)
    stand_b = poses.merge(poses.STAND, {"head": (-4, 0, 0)})
    wave_a = poses.merge(stand_b, poses._fing("R", 4, 2), {"upperarm01.R": (20, 0, -100), "lowerarm01.R": (35, 0, 0), "lowerarm02.R": (0, 0, 0)})
    wave_b = poses.merge(wave_a, {"lowerarm01.R": (35, 0, 28)})
    seq = [(1, stand_b), (30, stand_b), (38, wave_a)]
    f = 38
    for k in range(6):                      # six wave strokes, on twos-threes
        f += 6
        seq.append((f, wave_b if k % 2 == 0 else wave_a))
    seq += [(f + 14, wave_a), (f + 26, stand_b), (144, stand_b)]
    poses.key_sequence(boy, seq, step=2)''')
open(p, "w", encoding="utf-8").write(s)

# ---------------------------------------------------------------- B1: the father rests his hand on his son's shoulder at dusk
p2 = ROOT + "shots/b1.py"
t = open(p2, encoding="utf-8").read()
a_ = '''pm = af.flat_mat("pigeon_dusk", "#3A2438")'''
assert a_ in t
t = t.replace(a_, '''# the father's near hand settles on his son's near shoulder as the crane comes down (local 84-100)
import body
bpy.context.view_layer.update()
fp = fa.matrix_world.translation
side_b = min(("L", "R"), key=lambda sd: (boy.matrix_world @ boy.pose.bones[f"shoulder01.{sd}"].tail - fp).length)
side_f = min(("L", "R"), key=lambda sd: (fa.matrix_world @ fa.pose.bones[f"shoulder01.{sd}"].tail - boy.matrix_world.translation).length)
body.reach_bone(fa, side_f, boy, f"shoulder01.{side_b}", [(1, 0.0), (84, 0.0), (100, 1.0), (144, 1.0)])
''' + a_, 1)
open(p2, "w", encoding="utf-8").write(t)
import ast
ast.parse(s)
ast.parse(t)
print("V3 acting patched (needs previews to verify signs)")
