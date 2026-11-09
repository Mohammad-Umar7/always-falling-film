# Parametric shots: split-screen halves (960x1080) and the remaining full-frame Hyderabad shots.
# usage: blender -b --factory-startup -P shots/half.py -- preset=C2L [preview|final] [frames=..] [scale=..]
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector, Matrix
import af, shot, poses, scene_b, sets_hyd, scene_auh, sets_auh, sets_room

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PRESET = [a[7:] for a in argv if a.startswith("preset=")][0]

HALF = (960, 1080)
FULL = (1920, 1080)

LANE_CAST_NIGHT = dict(poses.NIGHT_CAST)


def place(rig, loc, yaw=0.0):
    rig.location = loc
    rig.rotation_euler = (0, 0, math.radians(yaw))


def attach(ob, rig, bone):
    bpy.context.view_layer.update()            # location may have just been set: refresh matrix_world first
    mw = ob.matrix_world.copy()
    ob.parent = rig
    ob.parent_type = "BONE"
    ob.parent_bone = bone
    bpy.context.view_layer.update()
    pb = rig.pose.bones[bone]
    ob.matrix_parent_inverse = (rig.matrix_world @ pb.matrix @ Matrix.Translation(Vector((0, pb.length, 0)))).inverted()
    ob.matrix_world = mw


def seat(rig, seat_z):
    bpy.context.view_layer.update()
    pz = (rig.matrix_world @ rig.pose.bones["pelvis.L"].head).z
    rig.location.z += (seat_z + 0.07) - pz
    bpy.context.view_layer.update()


def lap_points(rig):
    bpy.context.view_layer.update()
    pts = {}
    for side in ("L", "R"):
        knee = rig.matrix_world @ rig.pose.bones[f"lowerleg01.{side}"].head
        hip = rig.matrix_world @ rig.pose.bones[f"upperleg01.{side}"].head
        pts[side] = (knee, hip)
    return pts


def hands_on_knees(rig, lift=0.055, along=0.22):
    """IK both hands onto the tops of the knees (no hands hovering over nothing)."""
    for side, (knee, hip) in lap_points(rig).items():
        scene_b.ik_arm(rig, side, knee.lerp(hip, along) + Vector((0, 0, lift)))


from body import look_track, reach_bone, HEAD_YAW


def bone_tail(rig, bone):
    bpy.context.view_layer.update()
    return rig.matrix_world @ rig.pose.bones[bone].tail


def hyd_night(year, cast, moon_dir=(0.25, 0.55, 0.8), charpai=True, moon_size=21.0, clouds=True):
    H, rigs = scene_b.night_roof(year=year, moon_dir=moon_dir, cast=cast, lying=False, clouds=clouds, moon_size=moon_size)
    if not charpai:
        for o in list(bpy.data.objects):
            if o.name.startswith("hero_charpai"):
                bpy.data.objects.remove(o, do_unlink=True)
    return H, rigs


def auh_night(year=1975):
    A = scene_auh.camp_roof(year=year)
    rigs = poses.load_chars(["FATHER_75_WORK"], palette=scene_auh.NIGHT_CAST)
    return A, rigs["FATHER_75_WORK"]


def auh_moon(dirv=(0.2, 0.9, 0.55), size=16.0):
    d = Vector(dirv).normalized()
    af.moon("moon_auh", d * 400, size, cam_dir=-d)


def envelope(name, loc, rot=(0, 0, 0), mat=None):
    m = mat or af.toon_mat("envelope", "#F2EEE2", shadow="#9A96A8", light="#FFFFFF", band=0.3, light_band=0.8)
    ob = af.box(name, (0.16, 0.002, 0.09), loc, m, rot=rot)
    af.add_outline(ob, 0.002, "#2A2430")
    return ob


# ====================================================================== presets
def P_C2L():
    S = shot.Shot("C2L", 96, *HALF)
    H, r = hyd_night(1975, ["BOY_75"], moon_dir=(-0.3, -0.75, 0.6))
    boy = r["BOY_75"]
    place(boy, (0.8, -4.7, 0.06), 180 + 180)
    poses.apply(boy, poses.STAND_LOOK_UP_HIGH, frame=1)
    S.cam("cam", keys=[(1, (1.15, -2.9, 0.55), (0.2, -14.0, 6.5), 24.0), (96, (1.12, -2.95, 0.55), (0.2, -14.0, 6.8), 24.0)])
    return S


def P_C2R():
    S = shot.Shot("C2R", 96, *HALF)
    A, fa = auh_night(1975)
    place(fa, (0.0, -2.0, 6.6), 180)
    poses.apply(fa, poses.STAND_LOOK_UP_HIGH, frame=1)
    auh_moon()
    S.cam("cam", keys=[(1, (1.8, -4.6, 7.5), (-4.0, 12.0, 12.0), 26.0), (96, (1.75, -4.5, 7.5), (-4.0, 12.0, 12.3), 26.0)])
    return S


def P_E1L():
    S = shot.Shot("E1L", 144, *HALF)
    H, r = hyd_night(1976, ["BOY_75"], moon_dir=(0.6, 0.2, 0.75))
    boy = r["BOY_75"]
    place(boy, (-1.5, -2.0, 0.06), 90)
    look_track(boy, poses.STAND_LOOK_UP_HIGH, 40, 120, 144, 16, -16)
    S.cam("cam", keys=[(1, (-3.6, -2.6, 0.5), (0.5, -1.4, 3.2), 26.0), (144, (-3.5, -2.55, 0.5), (0.5, -1.4, 3.3), 26.0)])
    return S


def P_E1R():
    S = shot.Shot("E1R", 144, *HALF)
    A = sets_auh.Auh(time="night", seed=12, year=1976)
    A.sky()
    A.room(lamp=False)
    af.add_point("room_lamp", (1.25, 1.05, 1.05), "#FFD49A", energy=60.0, radius=0.08)
    r = poses.load_chars(["FATHER_75_WORK"], palette=scene_auh.NIGHT_CAST)
    fa = r["FATHER_75_WORK"]
    place(fa, (0.85, 0.32, 0.0), 180)
    poses.apply(fa, poses.merge(poses.SIT, {"head": (18, 0, 0), "neck01": (10, 0, 0)}), frame=1)
    seat(fa, 0.47)
    nm = sets_room.note_mat()
    n_ = sets_room.note("e1r_note", (0.9, 0.9, 0.79), (0, 0, math.radians(8)), size=0.16, mat=nm)
    env = envelope("e1r_env", (1.12, 0.95, 0.785), (math.radians(90), 0, math.radians(-12)))
    el = scene_b.ik_arm(fa, "L", Vector((0.78, 0.87, 0.815)))
    er = scene_b.ik_arm(fa, "R", Vector((1.02, 0.9, 0.82)))
    # fold: note slides toward the envelope (stepped) - both hands travel with it, fingertips on the note
    for f, p in ((1, (0.9, 0.9, 0.79)), (40, (0.9, 0.9, 0.79)), (70, (1.0, 0.93, 0.80)), (100, (1.1, 0.95, 0.80)), (144, (1.1, 0.95, 0.80))):
        n_.location = p
        n_.keyframe_insert("location", frame=f)
        d = Vector(p) - Vector((0.9, 0.9, 0.79))
        el.location = Vector((0.84, 0.885, 0.80)) + d          # pushes the note along the table
        er.location = Vector((1.16, 0.93, 0.80))               # steadies the envelope
        el.keyframe_insert("location", frame=f)
        er.keyframe_insert("location", frame=f)
    for o in (n_, el, er):
        af.set_interp(o, "CONSTANT")
    S.cam("cam", keys=[(1, (1.45, 0.42, 1.52), (0.9, 0.76, 0.97), 22.0), (144, (1.44, 0.43, 1.51), (0.92, 0.77, 0.96), 23.0)])
    return S


def P_E2L():
    S = shot.Shot("E2L", 144, *HALF)
    sets_room.front_door_inside("morning")
    env = envelope("e2l_env", (0.0, 0.7, 1.0), (math.radians(90), 0, 0))
    keys = [(1, (0.0, 0.85, 1.0), (math.radians(90), 0, 0)), (40, (0.0, 0.85, 1.0), (math.radians(90), 0, 0)),
            (52, (0.0, 0.62, 1.0), (math.radians(90), 0, 0)), (64, (0.02, 0.45, 0.5), (math.radians(40), 0.2, 0.3)),
            (74, (0.05, 0.35, 0.01), (0.0, 0, 0.35)), (144, (0.05, 0.35, 0.01), (0.0, 0, 0.35))]
    for f, l, rr in keys:
        env.location = l
        env.rotation_euler = rr
        env.keyframe_insert("location", frame=f)
        env.keyframe_insert("rotation_euler", frame=f)
    af.set_interp(env, "CONSTANT")
    S.cam("cam", keys=[(1, (0.25, -0.9, 0.55), (0.0, 0.7, 0.75), 30.0), (144, (0.25, -0.85, 0.5), (0.0, 0.7, 0.6), 30.0)])
    return S


def P_E2R():
    S = shot.Shot("E2R", 144, *HALF)
    A = sets_auh.Auh(time="sunset", seed=13, year=1976)
    A.sky()
    A.ground()
    A.skyline(center=(0, 150), n=18, radius=160, year=1976)
    A.post_box((0.0, 0.0))
    A.sun_disc(24.0)
    r = poses.load_chars(["FATHER_75_WORK"], palette=scene_auh.SUNSET_CAST)
    fa = r["FATHER_75_WORK"]
    place(fa, (0.25, -0.75, 0.0), 160)
    poses.apply(fa, poses.merge(poses.STAND, {"head": (12, 0, 0)}), frame=1)
    env = envelope("e2r_env", (0.0, -0.4, 1.06), (math.radians(90), 0, 0))
    eh = scene_b.ik_arm(fa, "R", Vector((0.05, -0.42, 1.06)))
    for f, p in ((1, (0.0, -0.55, 1.06)), (30, (0.0, -0.55, 1.06)), (52, (0.0, -0.32, 1.055)), (60, (0.0, -0.2, 1.055)), (144, (0.0, -0.2, 1.055))):
        env.location = p
        env.keyframe_insert("location", frame=f)
        eh.location = Vector(p) + Vector((0.06, -0.05, 0.0))
        eh.keyframe_insert("location", frame=f)
    env.scale = (1, 1, 1)
    env.keyframe_insert("scale", frame=59)
    env.scale = (0.001, 0.001, 0.001)
    env.keyframe_insert("scale", frame=61)
    for o in (env, eh):
        af.set_interp(o, "CONSTANT")
    S.cam("cam", keys=[(1, (-1.1, -0.95, 1.42), (0.08, -0.4, 1.22), 32.0), (144, (-1.08, -0.93, 1.41), (0.08, -0.4, 1.23), 33.0)])
    return S


def P_E3L():
    S = shot.Shot("E3L", 192, *HALF)
    H, r = hyd_night(1976, ["BOY_75"], moon_dir=(0.15, -0.8, 0.58))
    boy = r["BOY_75"]
    place(boy, (0.6, -2.5, 0.06), 0)
    poses.apply(boy, poses.merge(poses.STAND_LOOK_UP_HIGH, poses.FIST_L), frame=1)
    hand_target = Vector((0.72, -2.8, 1.2))
    eh = scene_b.ik_arm(boy, "L", hand_target)
    nm = sets_room.note_mat()
    bpy.context.view_layer.update()
    pb = boy.pose.bones["lowerarm02.L"]
    wrist = boy.matrix_world @ pb.tail
    fdir = (wrist - boy.matrix_world @ pb.head).normalized()
    n_ = sets_room.note("e3l_note", wrist + fdir * 0.075, (math.radians(78), 0, 0), size=0.17, mat=nm)   # pinched in the fist
    S.cam("cam", keys=[(1, (0.95, -1.75, 0.55), (0.5, -3.4, 1.35), 30.0), (192, (0.94, -1.8, 0.55), (0.5, -3.4, 1.4), 31.0)])
    return S


def P_E3R():
    S = shot.Shot("E3R", 192, *HALF)
    A, fa = auh_night(1976)
    place(fa, (-1.0, -1.2, 6.6), 160)
    reach = poses.merge(poses.STAND_LOOK_UP_HIGH, poses._fing("R", 6, 4),
                        {"upperarm01.R": (96, 0, -44), "upperarm02.R": (0, 0, 0), "lowerarm01.R": (14, 0, 0)})
    half_up = poses.blend(poses.STAND_LOOK_UP_HIGH, reach, 0.5)
    poses.key_sequence(fa, [(1, poses.STAND_LOOK_UP_HIGH), (60, poses.STAND_LOOK_UP_HIGH), (72, half_up), (84, reach),
                            (150, reach), (166, half_up), (178, poses.STAND_LOOK_UP_HIGH), (192, poses.STAND_LOOK_UP_HIGH)], step=2)
    auh_moon((-0.3, 0.8, 0.5), 18.0)
    S.cam("cam", keys=[(1, (1.4, -2.0, 7.9), (-6.0, 1.0, 9.5), 30.0), (192, (1.35, -2.0, 7.9), (-6.0, 1.0, 9.7), 30.0)])
    return S


def P_F1L():
    S = shot.Shot("F1L", 240, *HALF)
    H, r = hyd_night(1977, ["BOY_79"], moon_dir=(-0.5, 0.4, 0.75))
    boy = r["BOY_79"]
    place(boy, (0.66, 0.2, 0.47), 90)
    sitp = poses.merge(poses.SIT, {"head": (24, 0, 0), "neck01": (10, 0, 0)})
    look = poses.merge(poses.SIT, {"head": (-20, 0, 0), "neck01": (-12, 0, 0)})
    poses.key_sequence(boy, [(1, sitp), (90, sitp), (102, look), (150, look), (162, sitp), (240, sitp)], step=3)
    bpy.context.scene.frame_set(1)
    seat(boy, 0.53)
    H.bulb("f1l_lamp", Vector((1.3, 0.9, 1.1)), energy=50.0)
    lp = lap_points(boy)
    lap = (lp["L"][0] + lp["R"][0] + lp["L"][1] + lp["R"][1]) / 4 + Vector((0.04, 0, 0.075))
    book = af.box("f1l_book", (0.17, 0.24, 0.02), lap, af.toon_mat("book", "#C8D0F0", shadow="#5A6290", light="#FFFFFF"))
    book.rotation_euler = (0, math.radians(-18), 0)
    for side, dy in (("L", 0.13), ("R", -0.13)):
        scene_b.ik_arm(boy, side, lap + Vector((-0.02, dy, 0.03)))
    S.cam("cam", keys=[(1, (2.2, -1.2, 0.95), (0.4, 0.4, 1.2), 30.0), (240, (2.15, -1.1, 0.95), (0.4, 0.4, 1.25), 30.0)])
    return S


def P_F1R():
    S = shot.Shot("F1R", 240, *HALF)
    A = scene_auh.construction(year=1977)
    r = poses.load_chars(["FATHER_75_WORK"], palette=scene_auh.SUNSET_CAST)
    fa = r["FATHER_75_WORK"]
    place(fa, scene_auh.SCAFFOLD_PLANK, 10)
    poses.apply(fa, poses.merge(poses.STAND, {"head": (-4, 0, 0), "upperarm01.R": (30, 0, 30), "lowerarm01.R": (60, 0, 0)}), frame=1)
    # the city grows during the shot (stepped every 24 frames)
    grow = [o for o in bpy.data.objects if o.name.startswith("auh") and o.type == "EMPTY" and o.name[3:].isdigit()]
    for k, o in enumerate(grow):
        for f in range(1, 241, 24):
            t = f / 240.0
            o.scale = (1, 1, 0.55 + 0.45 * min(1.0, t * (1.0 + 0.3 * (k % 3))))
            o.keyframe_insert("scale", frame=f)
        af.set_interp(o, "CONSTANT")
    S.cam("cam", keys=[(1, (1.6, -4.6, 7.4), (-9.0, -40.0, 9.0), 28.0), (240, (1.9, -4.2, 7.6), (-8.0, -40.0, 10.0), 26.0)])
    return S


def P_F2L():
    S = shot.Shot("F2L", 240, *HALF)
    H, r = hyd_night(1979, ["BOY_79"], moon_dir=(-0.4, -0.5, 0.75))
    boy = r["BOY_79"]
    place(boy, (0.4, 0.2, 0.47), 90)
    poses.apply(boy, poses.merge(poses.SIT, {"head": (10, 0, -16)}), frame=1)
    seat(boy, 0.53)
    ear = bone_tail(boy, "head")
    eh = scene_b.ik_arm(boy, "L", ear + Vector((0.0, 0.1, -0.11)))
    A = sets_auh.Auh(time="night")
    rec, reels = A.cassette_recorder(Vector((0, 0, 0)), name="boyplayer")
    rec.scale = (0.8, 0.8, 0.8)
    hand = bone_tail(boy, "lowerarm02.L")
    rec.location = hand + Vector((0.0, 0.0, 0.02))
    rec.rotation_euler = (math.radians(90), 0, math.radians(90))
    attach(rec, boy, "lowerarm02.L")
    for k, rl in enumerate(reels):
        rl.rotation_euler = (0, 0, 0)
        rl.keyframe_insert("rotation_euler", frame=1)
        rl.rotation_euler = (0, 0, math.radians(-2200))
        rl.keyframe_insert("rotation_euler", frame=240)
        af.set_interp(rl, "LINEAR")
    S.cam("cam", keys=[(1, (1.12, -0.55, 1.1), (0.42, 0.22, 0.98), 36.0), (240, (1.1, -0.53, 1.09), (0.42, 0.22, 0.99), 38.0)])
    return S


def P_F2R():
    S = shot.Shot("F2R", 240, *HALF)
    A = sets_auh.Auh(time="night", seed=12, year=1979)
    A.sky()
    A.room(lamp=False)
    af.add_point("room_lamp", (1.25, 1.05, 1.05), "#FFD49A", energy=60.0, radius=0.08)
    rec, reels = A.cassette_recorder(Vector((0.85, 0.95, 0.78)), rot=math.radians(-10))
    for rl in reels:
        rl.rotation_euler = (0, 0, 0)
        rl.keyframe_insert("rotation_euler", frame=1)
        rl.rotation_euler = (0, 0, math.radians(-2400))
        rl.keyframe_insert("rotation_euler", frame=240)
        af.set_interp(rl, "LINEAR")
    r = poses.load_chars(["FATHER_75_WORK"], palette=scene_auh.NIGHT_CAST)
    fa = r["FATHER_75_WORK"]
    place(fa, (0.85, 0.32, 0.0), 180)
    poses.apply(fa, poses.merge(poses.SIT, {"head": (20, 0, 0), "neck01": (12, 0, 0)}), frame=1)
    seat(fa, 0.47)
    eh = scene_b.ik_arm(fa, "R", Vector((0.82, 1.0, 0.85)))
    for f, p in ((1, (0.82, 1.0, 0.86)), (30, (0.82, 1.0, 0.86)), (38, (0.80, 1.0, 0.845)), (44, (0.82, 0.98, 0.9)), (240, (0.82, 0.98, 0.9))):
        eh.location = p
        eh.keyframe_insert("location", frame=f)
    af.set_interp(eh, "CONSTANT")
    S.cam("cam", keys=[(1, (1.45, 1.02, 1.28), (0.84, 0.62, 0.98), 32.0), (240, (1.43, 1.02, 1.26), (0.84, 0.64, 0.97), 34.0)])
    return S


def P_F3L():
    S = shot.Shot("F3L", 240, *HALF)
    R = sets_room.Room("night", 1979).build(shutters_open=1.0, cassettes=12)
    lab = af.flat_mat("cas_label", "#E8DCC0", strength=0.9)
    bpy.context.view_layer.update()                   # cassettes' world matrices must be current before parenting
    for k, c in enumerate(R.cassettes):
        l = af.box(f"cas_lab{k}", (0.003, 0.012, 0.06), (c.location.x + 0.037, c.location.y, c.location.z + 0.01), lab)
        l.parent = c
        l.matrix_parent_inverse = c.matrix_world.inverted()
        f_on = 1 + k * 16 if k < 9 else 999
        c.scale = (1, 1, 1) if k < 3 else (0.001, 0.001, 0.001)
        c.keyframe_insert("scale", frame=1)
        if 3 <= k < 9:
            c.scale = (1, 1, 1)
            c.keyframe_insert("scale", frame=f_on)
        af.set_interp(c, "CONSTANT")
    # wall calendar above the shelf: the year flips while the tapes pile up
    paper = af.flat_mat("cal_paper", "#E9E2D0", strength=0.85)
    red = af.flat_mat("cal_red", "#B8303A", strength=0.9)
    ink = af.flat_mat("cal_ink", "#20141A", strength=1.0)
    af.plane("cal_sheet", 0.22, 0.28, (-1.615, -0.02, 1.66), (math.radians(90), 0, math.radians(90)), paper)
    af.plane("cal_head", 0.22, 0.06, (-1.612, -0.02, 1.77), (math.radians(90), 0, math.radians(90)), red)
    for i, yr in enumerate(("1977", "1978", "1979", "1980")):
        cu = bpy.data.curves.new(f"cal_{yr}", "FONT")
        cu.body = yr
        cu.align_x, cu.align_y = "CENTER", "CENTER"
        cu.size = 0.07
        t = af.link(bpy.data.objects.new(f"cal_{yr}", cu))
        t.data.materials.append(ink)
        t.location = (-1.608, -0.02, 1.63)
        t.rotation_euler = (math.radians(90), 0, math.radians(90))
        f0, f1 = 1 + i * 60, 61 + i * 60
        for f, sc_ in ((1, 0.0), (f0, 1.0), (f1, 0.0)):
            t.scale = (sc_ or 0.001,) * 3
            t.keyframe_insert("scale", frame=f)
        af.set_interp(t, "CONSTANT")
    S.cam("cam", keys=[(1, (-0.75, 0.08, 1.46), (-1.62, 0.12, 1.44), 44.0), (240, (-0.8, 0.1, 1.46), (-1.62, 0.13, 1.45), 48.0)])
    return S


def P_F3R():
    S = shot.Shot("F3R", 240, *HALF)
    A = sets_auh.Auh(time="night", seed=12, year=1980)
    A.sky()
    A.room()
    envs = []
    for k in range(6):
        e = envelope(f"f3r_env{k}", (0.75 + k * 0.012, 0.95 - k * 0.006, 0.785 + k * 0.004), (math.radians(90), 0, math.radians(-8 + k * 3)))
        e.scale = (1, 1, 1)
        e.keyframe_insert("scale", frame=1)
        if k >= 2:
            e.scale = (0.001, 0.001, 0.001)
            e.keyframe_insert("scale", frame=60 + (5 - k) * 40)
        af.set_interp(e, "CONSTANT")
    S.cam("cam", keys=[(1, (0.55, 0.3, 1.3), (1.0, 0.92, 0.85), 34.0), (240, (0.58, 0.33, 1.28), (1.0, 0.92, 0.85), 36.0)])
    return S


def P_F4L():
    S = shot.Shot("F4L", 240, *HALF)
    H, r = hyd_night(1979, ["BOY_79"], moon_dir=(0.1, -0.9, 0.42), clouds=True)
    boy = r["BOY_79"]
    place(boy, (0.3, -3.8, 0.06), 0)
    base = poses.merge(poses.STAND_LOOK_UP, poses.FIST_R)
    point = poses.merge(base, poses.POINT_L, {"upperarm01.L": (18, 0, 112), "upperarm02.L": (0, 0, 0), "lowerarm01.L": (6, 0, 0),
                                              "head": (-30, 0, 0)})
    poses.key_sequence(boy, [(1, base), (56, base), (66, point), (150, point), (162, base), (240, base)], step=2)
    # a real umbrella: 8 scalloped panels on a shallow cone, ribs, a tip and a curved handle
    import bmesh
    umb_m = af.toon_mat("umbrella", "#9A2438", shadow="#4A0E22", light="#D04A5E")
    rib_m = af.toon_mat("umbrella_rib", "#1A1418", shadow="#08060A", light="#3A3038")
    c0 = Vector((0.2, -3.84, 1.62))
    bm_ = bmesh.new()
    apex = bm_.verts.new(c0 + Vector((0, 0, 0.2)))
    rim, R, n = [], 0.58, 16
    for k in range(n):
        a_ = 2 * math.pi * k / n
        r_ = R * (1.0 if k % 2 == 0 else 0.9)                 # scallops between the ribs
        z_ = -0.03 if k % 2 == 0 else 0.03
        rim.append(bm_.verts.new(c0 + Vector((math.cos(a_) * r_, math.sin(a_) * r_, z_))))
    for k in range(n):
        bm_.faces.new((apex, rim[k], rim[(k + 1) % n]))
    me = bpy.data.meshes.new("umbrella")
    bm_.to_mesh(me)
    bm_.free()
    canopy = af.link(bpy.data.objects.new("umbrella", me))
    me.materials.append(umb_m)
    sol = canopy.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.01
    af.add_outline(canopy, 0.008, "#05060E")
    pole = af.cylinder("umbrella_pole", 0.011, 0.86, (0.2, -3.84, 1.39), rib_m, 8)
    af.uv_sphere("umbrella_tip", 0.02, c0 + Vector((0, 0, 0.23)), rib_m, 8, 6)
    scene_b.ik_arm(boy, "R", Vector((0.2, -3.84, 1.0)))
    S.cam("cam", keys=[(1, (0.9, -1.4, 0.7), (0.2, -10.0, 4.5), 26.0), (240, (0.88, -1.45, 0.7), (0.2, -10.0, 4.7), 26.0)])
    return S


def P_F4R():
    S = shot.Shot("F4R", 240, *HALF)
    A, fa = auh_night(1979)
    place(fa, (2.5, 1.5, 6.6), 200)
    poses.apply(fa, poses.STAND_LOOK_UP_HIGH, frame=1)
    auh_moon((0.4, 0.85, 0.35), 20.0)
    S.cam("cam", keys=[(1, (4.6, -3.0, 7.0), (-2.0, 14.0, 11.0), 30.0), (240, (4.5, -3.05, 7.0), (-2.0, 14.0, 11.3), 30.0)])
    return S


def P_F5L():
    S = shot.Shot("F5L", 240, *HALF)
    R = sets_room.Room("night", 1980).build(shutters_open=1.0, cassettes=9)
    r = poses.load_chars(["BOY_81"], palette=poses.NIGHT_CAST)
    boy = r["BOY_81"]
    place(boy, (-0.93, -0.2, 0.0), 90)
    poses.apply(boy, poses.merge(poses.SIT, {"head": (20, 0, 0), "upperarm01.L": (30, 0, -20), "lowerarm01.L": (90, 0, 0),
                                             "upperarm01.R": (30, 0, 20), "lowerarm01.R": (90, 0, 0)}), frame=1)
    seat(boy, 0.52)
    hands_on_knees(boy)
    A = sets_auh.Auh(time="night")
    rec, reels = A.cassette_recorder(Vector((-1.2, -0.45, 0.53)), rot=math.radians(70), name="boyplayer")   # beside him, in view
    for rl in reels:
        rl.rotation_euler = (0, 0, 0)
        rl.keyframe_insert("rotation_euler", frame=1)
        rl.rotation_euler = (0, 0, math.radians(-1600))
        rl.keyframe_insert("rotation_euler", frame=240)
        af.set_interp(rl, "LINEAR")
    S.cam("cam", keys=[(1, (0.6, -1.3, 1.15), (-0.8, -0.1, 0.85), 34.0), (240, (0.55, -1.25, 1.12), (-0.8, -0.1, 0.85), 36.0)])
    return S


def P_F5R():
    S = shot.Shot("F5R", 240, *HALF)
    A = sets_auh.Auh(time="night", seed=12, year=1980)
    A.sky()
    A.room()
    rec, reels = A.cassette_recorder(Vector((0.85, 0.95, 0.78)), rot=math.radians(-10))
    r = poses.load_chars(["FATHER_75_WORK"], palette=scene_auh.NIGHT_CAST)
    fa = r["FATHER_75_WORK"]
    place(fa, (-1.1, -0.35, 0.0), 90)
    poses.apply(fa, poses.merge(poses.SIT, {"head": (28, 0, 0), "neck01": (14, 0, 0), "spine03": (12, 0, 0),
                                            "upperarm01.L": (30, 0, -26), "lowerarm01.L": (60, 0, 0), "upperarm01.R": (30, 0, 26), "lowerarm01.R": (60, 0, 0)}), frame=1)
    seat(fa, 0.69)
    hands_on_knees(fa, lift=0.04, along=0.1)
    S.cam("cam", keys=[(1, (1.3, -1.4, 1.35), (-0.6, 0.4, 0.95), 28.0), (240, (1.25, -1.35, 1.32), (-0.6, 0.4, 0.95), 29.0)])
    return S


def P_G1L():
    S = shot.Shot("G1L", 192, *HALF)
    R = sets_room.Room("night", 1981).build(shutters_open=1.0, cassettes=9)
    r = poses.load_chars(["BOY_81"], palette=poses.NIGHT_CAST)
    boy = r["BOY_81"]
    place(boy, (-0.93, -0.2, 0.0), 90)
    a = poses.merge(poses.SIT, {"head": (20, 0, 0), "upperarm01.L": (30, 0, -20), "lowerarm01.L": (90, 0, 0), "upperarm01.R": (30, 0, 20), "lowerarm01.R": (90, 0, 0)})
    b = poses.merge(a, {"head": (34, 0, 0), "neck01": (14, 0, 0), "spine03": (10, 0, 0)})
    poses.key_sequence(boy, [(1, a), (120, a), (140, b), (192, b)], step=3)
    bpy.context.scene.frame_set(1)
    seat(boy, 0.52)
    A = sets_auh.Auh(time="night")
    rec, reels = A.cassette_recorder(Vector((-1.2, -0.45, 0.53)), rot=math.radians(70), name="boyplayer")   # beside him, in view
    for rl in reels:
        rl.rotation_euler = (0, 0, 0)
        rl.keyframe_insert("rotation_euler", frame=1)
        rl.rotation_euler = (0, 0, math.radians(-900))
        rl.keyframe_insert("rotation_euler", frame=110)
        af.set_interp(rl, "LINEAR")
    S.cam("cam", keys=[(1, (0.3, -1.0, 1.0), (-0.95, -0.15, 0.95), 40.0), (192, (0.25, -0.95, 0.98), (-0.95, -0.15, 0.92), 44.0)])
    return S


def P_G1R():
    S = shot.Shot("G1R", 192, *HALF)
    A, fa = auh_night(1981)
    place(fa, (2.0, 2.5, 6.6), 190)
    poses.apply(fa, poses.STAND_LOOK_UP_HIGH, frame=1)
    auh_moon((-0.2, 0.9, 0.45), 14.0)
    S.cam("cam", keys=[(1, (7.5, -9.0, 9.0), (0.0, 12.0, 9.5), 24.0), (192, (7.4, -9.2, 9.1), (0.0, 12.0, 9.8), 24.0)])
    return S


def P_G2L():
    S = shot.Shot("G2L", 144, *HALF)
    R = sets_room.Room("night", 1981).build(shutters_open=1.0, cassettes=9)
    r = poses.load_chars(["BOY_81"], palette=poses.NIGHT_CAST)
    boy = r["BOY_81"]
    place(boy, (0.0, 1.06, 0.0), 180)
    reach = poses.merge(poses.STAND, {"upperarm01.L": (70, 0, -20), "upperarm01.R": (70, 0, 20), "lowerarm01.L": (20, 0, 0), "lowerarm01.R": (20, 0, 0), "head": (-6, 0, 0)})
    poses.key_sequence(boy, [(1, poses.STAND), (30, poses.STAND), (44, reach), (110, reach), (124, poses.STAND), (144, poses.STAND)], step=2)
    for k, piv in enumerate(R.shutters):
        s = -1 if k == 0 else 1
        piv.keyframe_insert("rotation_euler", frame=58 + k * 6)
        piv.rotation_euler = (0, 0, math.radians(s * 4))
        piv.keyframe_insert("rotation_euler", frame=84 + k * 6)
    for side, x in (("L", -0.24), ("R", 0.24)):
        scene_b.ik_arm(boy, side, Vector((x, 1.4, 1.12)))
        con = boy.pose.bones[f"lowerarm02.{side}"].constraints[-1]
        for f, v in ((1, 0.0), (70, 0.0), (86, 1.0), (112, 1.0), (126, 0.0)):
            con.influence = v
            con.keyframe_insert("influence", frame=f)
    S.cam("cam", keys=[(1, (-0.3, -1.1, 1.25), (0.0, 1.5, 1.45), 30.0), (144, (-0.28, -1.0, 1.25), (0.0, 1.5, 1.45), 31.0)])
    return S


def P_G2R():
    S = shot.Shot("G2R", 144, *HALF)
    A, fa = auh_night(1981)
    place(fa, (-1.0, -1.2, 6.6), 160)
    poses.apply(fa, poses.STAND_LOOK_UP_HIGH, frame=1)
    auh_moon((-0.3, 0.8, 0.5), 18.0)
    S.cam("cam", keys=[(1, (0.9, -1.5, 8.05), (-6.0, 1.5, 9.4), 36.0), (144, (0.88, -1.5, 8.05), (-6.0, 1.5, 9.5), 37.0)])
    return S


def P_G3L():
    S = shot.Shot("G3L", 144, *HALF)
    R = sets_room.Room("night", 1981).build(shutters_open=0.04, cassettes=9)
    S.cam("cam", keys=[(1, (-0.2, -0.9, 1.3), (0.0, 1.5, 1.5), 32.0), (144, (-0.18, -0.8, 1.3), (0.0, 1.5, 1.5), 33.0)])
    return S


def P_G3R():
    S = shot.Shot("G3R", 144, *HALF)
    A, fa = auh_night(1981)
    place(fa, (2.0, 2.5, 6.6), 190)
    poses.apply(fa, poses.STAND_LOOK_UP_HIGH, frame=1)
    auh_moon((-0.2, 0.9, 0.45), 14.0)
    S.cam("cam", keys=[(1, (10.5, -13.0, 11.0), (0.0, 12.0, 10.0), 22.0), (144, (10.4, -13.2, 11.1), (0.0, 12.0, 10.3), 22.0)])
    return S


# -------------------------------------------------------------- 1992
def roof92(cast, moon_dir=(0.3, -0.6, 0.74), clouds=True):
    H = sets_hyd.Hyd(time="night", seed=7, year=1992)
    H.build(dressing=False)
    H.sky_dressing(moon_dir=moon_dir, clouds=clouds, moon_size=18.0)
    key = bpy.data.objects.get("key")
    if key:
        key.rotation_euler = (-Vector(moon_dir)).to_track_quat("-Z", "Y").to_euler()
    rigs = poses.load_chars(cast, palette=poses.NIGHT_CAST)
    return H, rigs


def P_I1L():
    S = shot.Shot("I1L", 192, *HALF)
    H, r = roof92(["SON_92"])
    son = r["SON_92"]
    place(son, (0.9, -5.4, 0.0), 180)
    sitp = poses.merge(poses.SIT, {"head": (16, 0, 0), "neck01": (6, 0, 0), "upperarm01.L": (20, 0, -30), "upperarm01.R": (20, 0, 30)})
    poses.apply(son, sitp, frame=1)
    seat(son, 0.96)
    hands_on_knees(son)
    # (no headphones: continuity with I3L minutes later)
    S.cam("cam", keys=[(1, (2.3, -2.6, 1.1), (0.6, -5.2, 1.0), 34.0), (192, (2.25, -2.65, 1.1), (0.6, -5.2, 1.0), 35.0)])
    return S


def P_I1R():
    S = shot.Shot("I1R", 192, *HALF)
    H, r = roof92(["FATHER_92"])
    fa = r["FATHER_92"]
    place(fa, (1.55, -6.55, sets_hyd.LANE_Z), 180)
    poses.apply(fa, poses.merge(poses.STAND, poses.HOLD_SUITCASE_R, {"head": (10, 0, 0)}), frame=1)
    case_m = af.toon_mat("suitcase92", "#4A2E2A", shadow="#221416", light="#6E4440")
    hand = bone_tail(fa, "lowerarm02.R")
    case = af.box("suitcase", (0.5, 0.16, 0.38), hand + Vector((0, 0, -0.22)), case_m, bevel=0.02)
    af.add_outline(case, 0.006, "#0A0608")
    S.cam("cam", keys=[(1, (3.55, -6.0, sets_hyd.LANE_Z + 1.05), (1.4, -6.15, sets_hyd.LANE_Z + 1.25), 24.0),
                       (192, (3.45, -6.02, sets_hyd.LANE_Z + 1.05), (1.4, -6.15, sets_hyd.LANE_Z + 1.3), 26.0)])
    return S


def streak_sky(f0, f1, start, end, name="sky_streak"):
    """The burning satellite seen from the ground: a glowing head with a long fading trail across the sky."""
    import reentry as rx
    pts = [Vector(start).lerp(Vector(end), i / 59) + Vector((0, 0, -30 * (i / 59) ** 2)) for i in range(60)]
    ob, head = rx.streak(name, pts, f0, f1, depth=(2.2, 0.1), strength=10.0)
    return ob, head


def P_I3L():
    S = shot.Shot("I3L", 168, *HALF)
    H, r = roof92(["SON_92"], moon_dir=(0.6, 0.6, 0.5))
    son = r["SON_92"]
    place(son, (0.9, -5.38, 0.0), 0)                # on the parapet, legs over the lane side
    down = poses.merge(poses.SIT, {"head": (16, 0, 0), "neck01": (6, 0, 0)})
    up = poses.merge(poses.SIT, {"head": (-30, 0, 0), "neck01": (-16, 0, 0), "spine02": (-6, 0, 0)})
    poses.key_sequence(son, [(1, down), (40, down), (52, up), (168, up)], step=2)
    bpy.context.scene.frame_set(1)
    seat(son, 0.96)
    for side, dx in (("L", 0.26), ("R", -0.26)):      # palms on the parapet beside his hips
        scene_b.ik_arm(son, side, Vector((0.9 + dx, -5.36, 0.99)))
    streak_sky(20, 160, (-260, -160, 240), (220, -120, 120))
    li = af.add_point("streak_light", (0.9, -6.5, 4.0), "#FF9A4A", energy=0.0, radius=1.0)
    li.data.keyframe_insert("energy", frame=30)
    li.data.energy = 900.0
    li.data.keyframe_insert("energy", frame=60)
    S.cam("cam", keys=[(1, (1.6, -6.5, 2.3), (0.9, -5.35, 1.55), 34.0), (168, (1.58, -6.52, 2.3), (0.9, -5.35, 1.6), 37.0)])
    return S


def P_I3R():
    S = shot.Shot("I3R", 168, *HALF)
    H, r = roof92(["FATHER_92"])
    fa = r["FATHER_92"]
    place(fa, (1.55, -6.55, sets_hyd.LANE_Z), 180)
    down = poses.merge(poses.STAND, poses.HOLD_SUITCASE_R, {"head": (10, 0, 0)})
    up = poses.merge(poses.STAND, poses.HOLD_SUITCASE_R, poses.LOOK_UP)
    poses.key_sequence(fa, [(1, down), (30, down), (44, up), (168, up)], step=2)
    li = af.add_point("streak_light", (1.0, -7.0, sets_hyd.LANE_Z + 6.0), "#FF9A4A", energy=0.0, radius=1.0)
    li.data.keyframe_insert("energy", frame=20)
    li.data.energy = 1400.0
    li.data.keyframe_insert("energy", frame=50)
    S.cam("cam", keys=[(1, (2.05, -5.95, sets_hyd.LANE_Z + 2.35), (1.55, -6.55, sets_hyd.LANE_Z + 1.52), 40.0),
                       (168, (2.0, -5.98, sets_hyd.LANE_Z + 2.3), (1.55, -6.55, sets_hyd.LANE_Z + 1.56), 44.0)])
    return S


def suitcase_at(hand_loc):
    case_m = af.toon_mat("suitcase92", "#4A2E2A", shadow="#221416", light="#6E4440")
    case = af.box("suitcase", (0.5, 0.16, 0.38), hand_loc + Vector((0, 0, -0.22)), case_m, bevel=0.02)
    af.add_outline(case, 0.006, "#0A0608")
    return case


def P_I4W():
    S = shot.Shot("I4W", 240, *FULL)
    H, r = roof92(["SON_92", "FATHER_92"], moon_dir=(0.5, 0.5, 0.7))
    son, fa = r["SON_92"], r["FATHER_92"]
    place(son, (1.3, -5.12, 0.06), 0)
    poses.apply(son, poses.merge(poses.STAND, poses.LOOK_DOWN, {"spine03": (22, 0, 0), "spine02": (10, 0, 0), "upperarm01.L": (34, 0, -30), "upperarm01.R": (34, 0, 30), "lowerarm01.L": (30, 0, 0), "lowerarm01.R": (30, 0, 0)}), frame=1)
    place(fa, (1.5, -6.6, sets_hyd.LANE_Z), 180)
    poses.apply(fa, poses.merge(poses.STAND, poses.HOLD_SUITCASE_R, poses.LOOK_UP_HIGH), frame=1)
    suitcase_at(bone_tail(fa, "lowerarm02.R"))
    li = af.add_point("streak_light", (1.5, -7.5, -1.0), "#FF9A4A", energy=900.0, radius=1.0)
    li.data.keyframe_insert("energy", frame=1)
    li.data.energy = 120.0
    li.data.keyframe_insert("energy", frame=200)
    # the sky's point of view (rhymes with B4a): straight down, the lane between them collapses to a hand's width
    # from the lane, just behind the father's shoulder: he looks up at his son leaning over the parapet above
    # (found by ray casting, tests/cam_search.py: both faces unoccluded, 22 degrees apart)
    # screen-up runs from the father to the son, so the frame stands upright: son at the top, father at the bottom
    S.cam_up("cam", [(1, (2.0, -7.25, sets_hyd.LANE_Z + 0.54), (0.73, -5.675, -1.285), 34.0),
                     (240, (1.98, -7.22, sets_hyd.LANE_Z + 0.58), (0.73, -5.675, -1.285), 37.0)], up=(-0.2, 1.3, 6.38))
    return S


def P_J1():
    S = shot.Shot("J1", 192, *FULL)
    H, r = roof92(["FATHER_92"], moon_dir=(0.3, -0.5, 0.8))
    fa = r["FATHER_92"]
    place(fa, (1.5, -6.6, sets_hyd.LANE_Z), 180)
    up = poses.merge(poses.STAND, poses.HOLD_SUITCASE_R, poses.LOOK_UP_HIGH)
    mid = poses.merge(poses.STAND, poses.HOLD_SUITCASE_R, poses.LOOK_UP)
    poses.key_sequence(fa, [(1, up), (60, up), (90, mid), (192, mid)], step=3)
    suitcase_at(bone_tail(fa, "lowerarm02.R"))
    S.cam("cam", keys=[(1, (1.35, -5.65, 1.55), (1.5, -6.62, sets_hyd.LANE_Z + 1.4), 135.0), (192, (1.35, -5.68, 1.5), (1.5, -6.62, sets_hyd.LANE_Z + 1.45), 165.0)])
    return S


def P_J2():
    S = shot.Shot("J2", 168, *FULL)
    H, r = roof92(["SON_92"], moon_dir=(-0.4, -0.7, 0.6))
    son = r["SON_92"]
    place(son, (1.3, -4.95, 0.06), 0)
    poses.apply(son, poses.merge(poses.STAND, poses.LOOK_DOWN, {"spine03": (12, 0, 0)}), frame=1)
    head = bone_tail(son, "head")
    af.add_sun("rim_warm", (-0.55, -0.7, -0.35), "#FF9A52", energy=1.4, angle=3.0)
    S.cam("cam", keys=[(1, (1.3 + 0.15, -5.75, head.z - 0.45), (1.3, -4.95, head.z - 0.06), 50.0), (168, (1.3 + 0.14, -5.7, head.z - 0.43), (1.3, -4.95, head.z - 0.06), 56.0)])
    return S


def P_J3():
    S = shot.Shot("J3", 120, *FULL)
    H, r = roof92(["FATHER_92"])
    fa = r["FATHER_92"]
    place(fa, (1.4, -6.12, sets_hyd.LANE_Z), 180)
    poses.apply(fa, poses.merge(poses.STAND, {"head": (10, 0, 0)}), frame=1)
    # two knocks with his right hand (camera side) on the sound cues (timeline 6505 / 6522 = local 25 / 42);
    # the arm rises only for the knocks, then hangs again before the door swings open
    eh = scene_b.ik_arm(fa, "R", Vector((1.6, -5.72, sets_hyd.LANE_Z + 1.3)))
    rest, back, hit = -5.74, -5.88, -5.69
    for f, y in ((1, rest), (19, back), (25, hit), (29, rest), (36, back), (42, hit), (46, rest), (120, rest)):
        eh.location = (1.6, y, sets_hyd.LANE_Z + 1.3)
        eh.keyframe_insert("location", frame=f)
    af.set_interp(eh, "CONSTANT")
    con = fa.pose.bones["lowerarm02.R"].constraints[-1]
    for f, v in ((1, 0.0), (13, 0.0), (17, 1.0), (50, 1.0), (56, 0.0)):
        con.influence = v
        con.keyframe_insert("influence", frame=f)
    suitcase_at(Vector((1.8, -6.15, sets_hyd.LANE_Z + 0.41)))
    # door leaves swing inward from frame 70, warm light spills out
    for o in list(bpy.data.objects):
        if o.name == "hero_doorleaf1":            # far leaf only, hinged at its outer edge, swings into the house
            hinge = bpy.data.objects.new("door_hinge", None)
            af.link(hinge)
            hinge.location = (o.location.x + 0.32, o.location.y, o.location.z)
            bpy.context.view_layer.update()
            mw = o.matrix_world.copy()
            o.parent = hinge
            o.matrix_world = mw
            hinge.keyframe_insert("rotation_euler", frame=70)
            hinge.rotation_euler = (0, 0, math.radians(-78))
            hinge.keyframe_insert("rotation_euler", frame=100)
    # the set's doorframe is one solid block that swallows the leaves: replace it with jambs + lintel for this shot
    fr = bpy.data.objects.get("hero_doorframe")
    if fr is not None:
        fm = fr.data.materials[0] if fr.data.materials else None
        fr.hide_render = True
        fr.hide_viewport = True
        for nm, size, loc in (("jambL", (0.16, 0.26, 2.5), (0.68, -5.55, sets_hyd.LANE_Z + 1.25)),
                              ("jambR", (0.16, 0.26, 2.5), (2.12, -5.55, sets_hyd.LANE_Z + 1.25)),
                              ("lintel", (1.6, 0.26, 0.2), (1.4, -5.55, sets_hyd.LANE_Z + 2.4))):
            j = af.box("door_" + nm, size, loc, fm)
            af.add_outline(j, 0.008, "#0A0608")
    # the lit room behind the door (the house is a solid block): a warm glowing doorway + a light just in front of it
    glow_m = af.flat_mat("door_glow", "#E89A58", strength=0.85)
    af.plane("door_glow", 1.3, 2.25, (1.4, -5.555, sets_hyd.LANE_Z + 1.12), (math.radians(90), 0, 0), glow_m)
    warm = af.add_point("door_warm", (1.62, -5.575, sets_hyd.LANE_Z + 1.7), "#FFB46A", energy=0.0, radius=0.0)
    warm.data.keyframe_insert("energy", frame=72)
    warm.data.energy = 190.0
    warm.data.keyframe_insert("energy", frame=104)
    # over his right shoulder, onto the door: it swings open and the warm light falls on him
    S.cam("cam", keys=[(1, (2.75, -7.45, sets_hyd.LANE_Z + 1.5), (1.35, -5.7, sets_hyd.LANE_Z + 1.3), 32.0),
                       (120, (2.65, -7.35, sets_hyd.LANE_Z + 1.5), (1.35, -5.7, sets_hyd.LANE_Z + 1.32), 35.0)])
    return S


def P_A2L():
    S = shot.Shot("A2L", 432, *HALF)
    H, r = roof92(["SON_92", "FATHER_92"], moon_dir=(0.2, 0.75, 0.62))
    son, fa = r["SON_92"], r["FATHER_92"]
    place(son, (0.4, 1.0, 0.06), 180)
    place(fa, (-0.9, 1.15, 0.06), 180)
    look_track(son, poses.STAND_LOOK_UP_HIGH, 54, 154, 432, 14, -14)
    look_track(fa, poses.STAND_LOOK_UP, 58, 158, 432, 14, -14)
    suitcase_at(Vector((-1.45, 1.15, 0.28)))
    S.cam("cam", keys=[(1, (0.75, -0.6, 1.05), (0.25, 6.0, 3.8), 34.0), (432, (0.74, -0.65, 1.05), (0.25, 6.0, 4.0), 34.0)])
    return S


def P_A2R():
    S = shot.Shot("A2R", 432, *HALF)
    H, r = roof92(["SON_92", "FATHER_92"], moon_dir=(0.2, 0.75, 0.62))
    son, fa = r["SON_92"], r["FATHER_92"]
    place(son, (0.4, 1.0, 0.06), 180)
    place(fa, (-0.9, 1.15, 0.06), 180)
    look_track(son, poses.STAND_LOOK_UP_HIGH, 54, 154, 432, 14, -14)
    look_track(fa, poses.STAND_LOOK_UP, 58, 158, 432, 14, -14)
    suitcase_at(Vector((-1.45, 1.15, 0.28)))
    S.cam("cam", keys=[(1, (-1.25, -0.55, 1.05), (-0.75, 6.0, 3.7), 34.0), (432, (-1.24, -0.6, 1.05), (-0.75, 6.0, 3.9), 34.0)])
    return S


def P_K1W():
    S = shot.Shot("K1W", 240, *FULL)
    H, r = roof92(["SON_92", "FATHER_92"], moon_dir=(0.2, 0.75, 0.62))
    son, fa = r["SON_92"], r["FATHER_92"]
    place(son, (-0.02, 1.0, 0.06), 180)             # the father half a step behind his son's shoulder,
    place(fa, (-0.42, 1.14, 0.06), 180)             # so the hand settles on it with a bent elbow
    up_s, up_f = poses.STAND_LOOK_UP_HIGH, poses.STAND_LOOK_UP
    to_f = poses.merge(poses.STAND, {"head": (-8, 30 * HEAD_YAW, 0), "neck02": (-4, 10 * HEAD_YAW, 0)})      # son turns to his left
    to_s = poses.merge(poses.STAND, {"head": (-6, -30 * HEAD_YAW, 0), "neck02": (-3, -10 * HEAD_YAW, 0)})    # father turns to his right
    poses.key_sequence(son, [(1, up_s), (122, up_s), (136, to_f), (240, to_f)], step=2)
    poses.key_sequence(fa, [(1, up_f), (128, up_f), (142, to_s), (240, to_s)], step=2)
    suitcase_at(Vector((-1.0, 1.15, 0.28)))
    # 1975 rhymes with 1992: as in B1 at dusk, the father's hand settles on his son's shoulder (after they turn)
    import body
    bpy.context.view_layer.update()
    side_b = min(("L", "R"), key=lambda sd: (son.matrix_world @ son.pose.bones[f"shoulder01.{sd}"].tail - fa.matrix_world.translation).length)
    side_f = min(("L", "R"), key=lambda sd: (fa.matrix_world @ fa.pose.bones[f"shoulder01.{sd}"].tail - son.matrix_world.translation).length)
    body.reach_bone(fa, side_f, son, f"shoulder01.{side_b}", [(1, 0.0), (148, 0.0), (168, 1.0), (240, 1.0)])
    S.cam("cam", keys=[(1, (-0.25, -0.9, 1.1), (-0.25, 6.0, 3.8), 34.0), (240, (-0.3, -3.0, 2.0), (-6.0, 60.0, 8.0), 28.0)])
    return S


def P_C1F():
    S = shot.Shot("C1F", 144, *FULL)
    H = sets_hyd.Hyd(time="day", seed=7, year=1975)
    H.build(dressing=False)
    rigs = poses.load_chars(["BOY_75", "FATHER_75_WORK"])
    boy, fa = rigs["BOY_75"], rigs["FATHER_75_WORK"]
    place(boy, (1.4, -6.1, sets_hyd.LANE_Z), 90)
    stand_b = poses.merge(poses.STAND, {"head": (-4, 0, 0)})
    wave_a = poses.merge(stand_b, poses._fing("R", 4, 2), {"upperarm01.R": (20, 0, -100), "lowerarm01.R": (35, 0, 0), "lowerarm02.R": (0, 0, 0)})
    wave_b = poses.merge(wave_a, {"lowerarm01.R": (35, 0, 28)})
    seq = [(1, stand_b), (30, stand_b), (38, wave_a)]
    f = 38
    for k in range(6):                      # six wave strokes, on twos-threes
        f += 6
        seq.append((f, wave_b if k % 2 == 0 else wave_a))
    seq += [(f + 14, wave_a), (f + 26, stand_b), (144, stand_b)]
    poses.key_sequence(boy, seq, step=2)
    # father walks away down the lane (+x), suitcase in his right hand, stepped walk
    walk = []
    for i, f in enumerate(range(1, 145, 6)):
        ph = i % 4
        walk.append((f, poses.merge(poses.STAND, poses.HOLD_SUITCASE_R, poses.walk_poses(ph))))
    for f, p in walk:
        poses.apply(fa, p, frame=f)
    for f in range(1, 145, 2):
        fa.location = (2.4 + 0.032 * (f - 1), -7.0, sets_hyd.LANE_Z)
        fa.keyframe_insert("location", frame=f)
    fa.rotation_euler = (0, 0, math.radians(90))
    bpy.context.scene.frame_set(1)
    hand = bone_tail(fa, "lowerarm02.R")
    case = suitcase_at(hand)
    attach(case, fa, "lowerarm02.R")
    S.cam("cam", keys=[(1, (-2.2, -7.6, sets_hyd.LANE_Z + 1.0), (8.0, -6.9, sets_hyd.LANE_Z + 1.15), 34.0), (144, (-2.15, -7.6, sets_hyd.LANE_Z + 1.0), (8.0, -6.9, sets_hyd.LANE_Z + 1.2), 36.0)])
    return S


def P_C1R():
    S = shot.Shot("C1R", 144, *HALF)
    A = scene_auh.construction(year=1975)
    r = poses.load_chars(["FATHER_75_WORK"], palette=scene_auh.SUNSET_CAST)
    fa = r["FATHER_75_WORK"]
    place(fa, (6.0, -18.0, 0.0), 10)
    poses.apply(fa, poses.merge(poses.STAND, poses.HOLD_SUITCASE_R, {"head": (-6, 0, 0)}), frame=1)
    suitcase_at(bone_tail(fa, "lowerarm02.R"))
    S.cam("cam", keys=[(1, (7.2, -14.5, 1.4), (2.0, -60.0, 9.0), 28.0), (144, (7.1, -14.8, 1.45), (2.0, -60.0, 9.5), 28.0)])
    return S


S = globals()["P_" + PRESET]()
S.finish(step=2)
