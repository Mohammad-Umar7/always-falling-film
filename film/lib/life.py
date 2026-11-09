# ALWAYS FALLING - V3 "life pass": nobody is ever a statue.
#   * breathing: additive sine on the chest/shoulders (slower when asleep, faster for children and under emotion)
#   * idle drift: smooth noise on spine / neck / head (tiny head turns and settles), scaled per character
#   * camera life: handheld drift (noise on the aim point / rotation) and an optional slow push-in
#   * depth of field on close-ups: focus locked to the nearest character's head, background melts away (anime look)
# Everything is ADDITIVE F-curve modifiers on top of the keyed acting, so poses, IK contacts and timing stay intact.
import bpy, math, random
from mathutils import Vector

# per shot: overrides. breath period (frames), idle scale, camera shake scale, dof f-stop (None = off)
SHOT = {
    "B4a": dict(dof=2.0), "B4b": dict(dof=2.0), "J2": dict(dof=1.6, push=0.06), "J1": dict(dof=2.8), "J3": dict(dof=2.2, push=0.05),
    "I3L": dict(dof=2.4), "I3R": dict(dof=2.0, push=0.05), "I1R": dict(dof=2.0), "G1L": dict(dof=2.4, push=0.05),
    "F2L": dict(dof=2.2), "F2R": dict(dof=2.0), "F5L": dict(dof=2.8), "F5R": dict(dof=2.8), "E1R": dict(dof=2.2),
    "F1L": dict(dof=3.2), "G2R": dict(dof=2.4), "I1L": dict(dof=3.5), "E3R": dict(dof=3.0),
    "B5": dict(cam=0.4), "I4W": dict(cam=0.3), "K1W": dict(cam=0.5), "A2L": dict(cam=0.6), "A2R": dict(cam=0.6),
}
SLEEPING = {("B5", "FATHER_75_HOME"), ("B5", "BOY_75"), ("F5R", "FATHER_75_WORK")}
AGITATED = {("I3L", "SON_92"), ("I3R", "FATHER_92"), ("J1", "FATHER_92"), ("J2", "SON_92"), ("G1L", "BOY_81"), ("J3", "FATHER_92")}


def _fc(rig, bone, axis):
    path = f'pose.bones["{bone}"].rotation_euler'
    ad = rig.animation_data
    if ad is None or ad.action is None:
        rig.pose.bones[bone].keyframe_insert("rotation_euler", frame=1)
        ad = rig.animation_data
    import af
    for fc in af._fcurves(ad.action):
        if fc.data_path == path and fc.array_index == axis:
            return fc
    rig.pose.bones[bone].keyframe_insert("rotation_euler", index=axis, frame=1)
    for fc in af._fcurves(rig.animation_data.action):
        if fc.data_path == path and fc.array_index == axis:
            return fc
    return None


def _sine(fc, amp_deg, period, phase):
    m = fc.modifiers.new("FNGENERATOR")
    m.function_type = "SIN"
    m.use_additive = True
    m.amplitude = math.radians(amp_deg)
    m.phase_multiplier = 2 * math.pi / period
    m.phase_offset = phase
    m.value_offset = 0.0
    return m


def _noise(fc, amp_deg, scale, phase):
    m = fc.modifiers.new("NOISE")
    m.blend_type = "ADD"
    m.strength = math.radians(amp_deg) * 2.0      # NOISE strength is peak-to-peak-ish
    m.scale = scale
    m.phase = phase
    return m


def breathe_and_idle(rig, sid, name, n_frames, seed):
    if rig is None or "spine03" not in rig.pose.bones:
        return
    rnd = random.Random(seed)
    kid = name.startswith("BOY")
    asleep = (sid, name) in SLEEPING
    agitated = (sid, name) in AGITATED
    period = 120 if asleep else (64 if kid else 84)
    if agitated:
        period = int(period * 0.7)
    depth = 1.0 if not asleep else 1.5
    ph = rnd.uniform(0, 6.28)
    # chest rises (spine03 tips back slightly), shoulders lift with each breath
    for bone, axis, amp in (("spine03", 0, -1.3 * depth), ("spine04", 0, -0.6 * depth),
                            ("clavicle.L", 2, 1.2 * depth), ("clavicle.R", 2, -1.2 * depth)):
        if bone in rig.pose.bones:
            fc = _fc(rig, bone, axis)
            if fc:
                _sine(fc, amp, period, ph)
    if asleep:
        return
    # idle drift: small slow settles of the spine, neck and head (turns + nods), never in sync between bones
    idle = 1.0 if not agitated else 1.4
    for bone, axis, amp, scale in (("spine02", 2, 0.8, 70), ("neck01", 1, 1.2, 55), ("head", 0, 1.4, 48),
                                   ("head", 1, 2.0, 62), ("head", 2, 0.8, 80)):
        if bone in rig.pose.bones:
            fc = _fc(rig, bone, axis)
            if fc:
                _noise(fc, amp * idle, scale, rnd.uniform(0, 100))


def camera_life(cam, sid, n_frames, seed):
    """handheld drift. Track-To cameras: jitter the aim target; keyed-rotation cameras: jitter rotation."""
    if cam is None:
        return
    import af
    cfg = SHOT.get(sid, {})
    k = cfg.get("cam", 1.0)
    rnd = random.Random(seed)
    tgt = None
    for c in cam.constraints:
        if c.type == "TRACK_TO" and c.target is not None:
            tgt = c.target
    if tgt is not None:
        dist = (Vector(tgt.location) - Vector(cam.location)).length
        amp = 0.0022 * dist * k                      # ~0.13 degree wobble
        if tgt.animation_data is None or tgt.animation_data.action is None:
            tgt.keyframe_insert("location", frame=1)
        for fc in af._fcurves(tgt.animation_data.action):
            if fc.data_path == "location":
                m = fc.modifiers.new("NOISE")
                m.blend_type = "ADD"
                m.strength = amp * 2
                m.scale = 40 + 10 * fc.array_index
                m.phase = rnd.uniform(0, 100)
    else:
        if cam.animation_data is None or cam.animation_data.action is None:
            cam.keyframe_insert("rotation_euler", frame=1)
        for fc in af._fcurves(cam.animation_data.action):
            if fc.data_path == "rotation_euler":
                m = fc.modifiers.new("NOISE")
                m.blend_type = "ADD"
                m.strength = math.radians(0.12) * 2 * k
                m.scale = 45
                m.phase = rnd.uniform(0, 100)
    push = cfg.get("push")
    if push:
        cd = cam.data
        l0 = cd.lens
        cd.keyframe_insert("lens", frame=1)
        cd.lens = l0 * (1 + push)
        cd.keyframe_insert("lens", frame=n_frames)
        cd.lens = l0


def depth_of_field(cam, sid, rigs):
    cfg = SHOT.get(sid, {})
    fstop = cfg.get("dof")
    if cam is None or not fstop or not rigs:
        return
    bpy.context.view_layer.update()
    cpos = cam.matrix_world.translation
    best, bd = None, 1e9
    for r in rigs:
        if "head" not in r.pose.bones:
            continue
        hp = r.matrix_world @ r.pose.bones["head"].head
        d = (hp - cpos).length
        if d < bd:
            best, bd = r, d
    if best is None:
        return
    foc = bpy.data.objects.new(f"dof_focus_{best.name}", None)
    bpy.context.scene.collection.objects.link(foc)
    foc.parent = best
    foc.parent_type = "BONE"
    foc.parent_bone = "head"
    foc.location = (0, 0, 0)
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = foc
    cam.data.dof.aperture_fstop = fstop
    cam.data.dof.aperture_blades = 6


def environment_life(n_frames, seed):
    """the world moves too: washing on the line flaps, neem trees sway, clouds drift"""
    import af
    rnd = random.Random(seed)
    n = 0
    for ob in list(bpy.data.objects):
        nm = ob.name
        if ob.type != "MESH":
            continue
        if "_line_c" in nm:                                  # hanging washing: gusty flap
            amps, scale = (5.0, 3.0, 0.0), 14
        elif nm.startswith("neem"):                          # canopies sway slowly
            amps, scale = (1.0, 1.0, 0.0), 55
        elif nm.startswith("cloud"):                         # clouds drift across the sky
            if ob.animation_data is None or ob.animation_data.action is None:
                x0 = ob.location.x
                ob.keyframe_insert("location", index=0, frame=1)
                ob.location.x = x0 + 0.12 * n_frames
                ob.keyframe_insert("location", index=0, frame=n_frames)
                ob.location.x = x0
                for fc in af._fcurves(ob.animation_data.action):
                    for kp in fc.keyframe_points:
                        kp.interpolation = "LINEAR"
                n += 1
            continue
        else:
            continue
        if ob.animation_data is None or ob.animation_data.action is None:
            ob.keyframe_insert("rotation_euler", frame=1)
        for fc in af._fcurves(ob.animation_data.action):
            if fc.data_path == "rotation_euler" and amps[fc.array_index] > 0:
                m = fc.modifiers.new("NOISE")
                m.blend_type = "ADD"
                m.strength = math.radians(amps[fc.array_index]) * 2
                m.scale = scale
                m.phase = rnd.uniform(0, 100)
        n += 1
    return n


# ---------------------------------------------------------------- V4: real camera moves (parallax, not a drifting picture)
# per shot: dolly (toward the subject), truck (sideways), crane (up), as fractions of the camera-subject distance;
# "off" keeps a camera exactly as staged (carefully framed or already moving a lot)
MOVE = {"I4W": {"off": True}, "K1W": {"off": True}, "B1": {"off": True}, "C1F": {"truck": 0.0, "dolly": 0.08},
        "B4a": {"off": True}, "J2": {"dolly": 0.10, "truck": 0.04, "crane": 0.0}, "J3": {"dolly": 0.10, "truck": 0.05}}


def _path_ok(sc, dg, pts, tgt_pts):
    for p, t in zip(pts, tgt_pts):
        for d in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((0, 0, -1))):
            hit, loc, *_ = sc.ray_cast(dg, p, d, distance=0.3)
            if hit:
                return False
        v = t - p
        L = v.length
        if L > 0.6:
            hit, loc, nrm, idx, ob, mw = sc.ray_cast(dg, p, v.normalized(), distance=L)
            if hit and (loc - p).length < 0.35 * L and (loc - p).length < L - 1.0:
                return False                       # something new would block the view of the subject
    return True


def camera_move(cam, sid, n):
    import af
    cfg = MOVE.get(sid, {})
    if cam is None or cfg.get("off") or n < 24:
        return None
    tt = next((c for c in cam.constraints if c.type == "TRACK_TO" and c.target is not None), None)
    ad = cam.animation_data
    if tt is None or ad is None or ad.action is None:
        return None                                # cam_up shots are framed by hand
    fcs = {fc.array_index: fc for fc in af._fcurves(ad.action) if fc.data_path == "location"}
    tfcs = {}
    if tt.target.animation_data and tt.target.animation_data.action:
        tfcs = {fc.array_index: fc for fc in af._fcurves(tt.target.animation_data.action) if fc.data_path == "location"}
    if len(fcs) < 3:
        return None
    pos = lambda f: Vector([fcs[i].evaluate(f) for i in range(3)])
    tpos = lambda f: Vector([tfcs[i].evaluate(f) if i in tfcs else tt.target.location[i] for i in range(3)])
    p0, t0, p1 = pos(1), tpos(1), pos(n)
    d = (t0 - p0).length
    if d < 0.3 or (p1 - p0).length > 0.15 * d:
        return None                                # already a real move
    fwd = (t0 - p0).normalized()
    lat = fwd.cross(Vector((0, 0, 1)))
    if lat.length < 1e-3:
        lat = Vector((1, 0, 0))
    lat.normalize()
    side = 1 if af.stable_seed(sid, "side") % 2 else -1
    D = fwd * (cfg.get("dolly", 0.12) * d) + lat * (cfg.get("truck", 0.08) * d * side) + Vector((0, 0, cfg.get("crane", 0.03) * d))
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    s_ = lambda f: (lambda t: t * t * (3 - 2 * t))((f - 1) / (n - 1))
    frames = [1 + (n - 1) * k / 10 for k in range(11)]
    scale = 1.0
    for _ in range(4):
        pts = [pos(f) + D * scale * s_(f) for f in frames]
        if _path_ok(sc, dg, pts, [tpos(f) for f in frames]):
            break
        scale *= 0.5
    else:
        return None
    D = D * scale
    for i in range(3):
        fc = fcs[i]
        if not any(abs(kp.co.x - n) < 0.5 for kp in fc.keyframe_points):
            fc.keyframe_points.insert(n, fc.evaluate(n))
        for kp in fc.keyframe_points:
            w = s_(min(max(kp.co.x, 1), n))
            kp.co.y += D[i] * w
            kp.handle_left.y += D[i] * w
            kp.handle_right.y += D[i] * w
        fc.update()
    return f"{D.length:.2f} m (scale {scale:g}, subject at {d:.1f} m)"


def apply(sid, n_frames):
    """call from Shot.finish() after all acting is baked"""
    import af
    scene = bpy.context.scene
    rigs = [o for o in scene.objects if o.type == "ARMATURE" and "spine03" in o.pose.bones]
    for i, r in enumerate(rigs):
        base = r.name.split(".")[0]
        breathe_and_idle(r, sid, base, n_frames, seed=af.stable_seed(sid, base, i))
    env = environment_life(n_frames, seed=af.stable_seed(sid, "env"))
    cam = scene.camera
    moved = camera_move(cam, sid, n_frames) if af.v4() else None
    camera_life(cam, sid, n_frames, seed=af.stable_seed(sid, "cam"))
    depth_of_field(cam, sid, rigs)
    if moved:
        print("AF: camera move", sid, moved)
    print("AF: life pass", sid, [r.name for r in rigs], "env", env, "dof" if SHOT.get(sid, {}).get("dof") else "")
