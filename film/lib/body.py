# ALWAYS FALLING - body acting helpers shared by shot scripts (V3)
import bpy
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
