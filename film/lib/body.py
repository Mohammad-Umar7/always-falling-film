# ALWAYS FALLING - body acting helpers shared by shot scripts (V3)
import bpy, math
import af, poses

HEAD_YAW = 1.0          # +1: positive head Y turns the head to the character's LEFT (verified in previews)


def look_track(rig, base, f0, f1, n, yaw0, yaw1, pitch=None, step=2):
    """the head (and a little of the neck) follows the satellite across the sky between f0 and f1"""
    def P(y):
        hx, _, hz = base.get("head", (0, 0, 0))
        nx, _, nz = base.get("neck02", (0, 0, 0))
        return poses.merge(base, {"head": (hx if pitch is None else pitch, y * HEAD_YAW, hz), "neck02": (nx, y * 0.35 * HEAD_YAW, nz)})
    poses.key_sequence(rig, [(1, P(yaw0)), (f0, P(yaw0)), (f1, P(yaw1)), (n, P(yaw1))], step=step)


def reach_bone(rig, side, target_rig, target_bone, keys, chain=4):
    """IK the hand to a bone of another character (follows it); keys: [(frame, influence)]"""
    e = bpy.data.objects.new(f"{rig.name}_reach_{side}", None)
    af.link(e)
    e.parent = target_rig
    e.parent_type = "BONE"
    e.parent_bone = target_bone
    e.location = (0, 0, 0)
    c = rig.pose.bones[f"lowerarm02.{side}"].constraints.new("IK")
    c.target = e
    c.chain_count = chain
    c.use_tail = True
    for f, v in keys:
        c.influence = v
        c.keyframe_insert("influence", frame=f)
    return e


def speech_gesture(rig, clip, start, n_frames, head=(5.0, 2.5), arm=None, step=2, fps=24):
    """V4: the speaker moves with the words. From the voice clip (audio/vo/<clip>.wav, placed at local frame `start`):
    a head nod on every stressed syllable (energy onsets), a slow head drift between phrases, and optionally one forearm
    lifting on emphasis (arm=("lowerarm01.L", degrees)). Added on top of the shot's stepped poses, on twos."""
    import os, wave
    import numpy as np
    import af
    p = os.path.join(af.ROOT, "audio", "vo", clip + ".wav")
    if not os.path.exists(p):
        return 0
    with wave.open(p) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if ch > 1:
        x = x.reshape(-1, ch).mean(1)
    hop = sr / fps
    nf = int(len(x) / hop)
    if nf < 4:
        return 0
    env = np.array([np.sqrt(np.mean(x[int(i * hop):int((i + 1) * hop)] ** 2) + 1e-12) for i in range(nf)])
    env = env / (np.percentile(env, 95) + 1e-9)
    sm = np.convolve(env, np.ones(3) / 3, mode="same")
    onset = np.clip(np.diff(sm, prepend=sm[0]), 0, None)
    onset = np.convolve(onset, np.ones(5) / 5, mode="same")
    onset = onset / (onset.max() + 1e-9)
    act = np.clip(np.convolve(sm, np.ones(7) / 7, mode="same"), 0, 1.2)
    chans = [("head", 0), ("head", 1)] + ([(arm[0], 0)] if arm else [])
    fcs = {}
    for bone, axis in chans:
        if bone not in rig.pose.bones:
            continue
        path = f'pose.bones["{bone}"].rotation_euler'
        fc = next((c for c in af._fcurves(rig.animation_data.action) if c.data_path == path and c.array_index == axis), None) \
            if rig.animation_data and rig.animation_data.action else None
        if fc is None:
            rig.pose.bones[bone].rotation_mode = "XYZ"
            rig.pose.bones[bone].keyframe_insert("rotation_euler", index=axis, frame=1)
            fc = next(c for c in af._fcurves(rig.animation_data.action) if c.data_path == path and c.array_index == axis)
        fcs[(bone, axis)] = fc
    frames = [start + i for i in range(0, nf + 8, step) if 1 <= start + i <= n_frames]
    base = {k: [fc.evaluate(f) for f in frames] for k, fc in fcs.items()}          # sample the pose BEFORE adding keys
    for j, f in enumerate(frames):
        k = min(f - start, nf - 1)
        fade = min(1.0, (nf + 8 - (f - start)) / 8.0)                                # settle back after the line
        d = {("head", 0): math.radians(head[0] * (onset[k] + 0.3 * act[k]) * fade),     # + X = nod down
             ("head", 1): math.radians(head[1] * math.sin((f - start) / 37.0) * fade)}
        if arm:
            d[(arm[0], 0)] = math.radians(arm[1] * act[k] * fade)
        for key, fc in fcs.items():
            kp = fc.keyframe_points.insert(f, base[key][j] + d.get(key, 0.0))
            kp.interpolation = "CONSTANT"
    return len(frames)
