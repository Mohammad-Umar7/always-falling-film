# ALWAYS FALLING — shot framework
# usage inside a shot script:
#   S = shot.Shot("B2", frames=192, w=1920, h=1080)
#   ... build ...
#   S.finish(step=2)
# CLI: blender -b --factory-startup -P shots/b2.py -- [preview|final|frames=1,96,192] [scale=50]
import bpy, os, sys, math
import af

RENDERS = os.path.join(af.ROOT, "renders")
PREVIEWS = os.path.join(RENDERS, "_previews")


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = {"mode": "preview", "frames": None, "scale": 50}
    for x in a:
        if x in ("preview", "final", "still"):
            out["mode"] = x
        elif x.startswith("frames="):
            out["frames"] = [int(v) for v in x[7:].split(",") if v]
        elif x.startswith("scale="):
            out["scale"] = int(x[6:])
    return out


class Shot:
    def __init__(self, sid, frames, w=1920, h=1080, samples=16):
        self.sid = sid
        self.n = frames
        self.w, self.h = w, h
        self.A = args()
        af.clear_scene()
        self.sc = af.setup_scene(w=w, h=h, samples=samples, f0=1, f1=frames)
        self.sc.frame_set(1)

    def cam(self, name="cam", loc=(0, 0, 0), target=(0, 1, 0), lens=35.0, keys=None, roll=0.0):
        """keys: list of (frame, loc, target, lens) for an animated camera (bezier eased)."""
        c = af.add_camera(name, loc, target, lens=lens, roll=roll)
        if keys:
            tgt = bpy.data.objects.new(name + "_tgt", None)
            af.link(tgt)
            con = c.constraints.new("TRACK_TO")
            con.target = tgt
            con.track_axis = "TRACK_NEGATIVE_Z"
            con.up_axis = "UP_Y"
            for f, l, t, ln in keys:
                c.location = l
                tgt.location = t
                c.data.lens = ln
                c.keyframe_insert("location", frame=f)
                tgt.keyframe_insert("location", frame=f)
                c.data.keyframe_insert("lens", frame=f)
            for ob in (c, tgt):
                for fc in af.fcurves_of(ob):
                    for kp in fc.keyframe_points:
                        kp.interpolation = "BEZIER"
                        kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
            for fc in af.fcurves_of(c.data) if c.data.animation_data else []:
                for kp in fc.keyframe_points:
                    kp.interpolation = "BEZIER"
        return c


    def cam_up(self, name, keys, up=(0, -1, 0)):
        """Camera with an explicit up vector (e.g. looking straight down). keys: [(frame, loc, target, lens)]"""
        from mathutils import Vector, Matrix
        cd = bpy.data.cameras.new(name)
        c = af.link(bpy.data.objects.new(name, cd))
        self.sc.camera = c
        for f, l, t, ln in keys:
            z = (Vector(l) - Vector(t)).normalized()
            y = (Vector(up) - z * Vector(up).dot(z)).normalized()
            x = y.cross(z)
            m = Matrix((x, y, z)).transposed().to_4x4()
            m.translation = Vector(l)
            c.matrix_world = m
            cd.lens = ln
            c.keyframe_insert("location", frame=f)
            c.keyframe_insert("rotation_euler", frame=f)
            cd.keyframe_insert("lens", frame=f)
        return c

    def shake(self, cam, f0, f1, strength=0.05, scale=2.0):
        """add a noise shake on rotation between f0..f1 (anime impact)."""
        for a in range(3):
            cam.keyframe_insert("rotation_euler", index=a, frame=1)
        for fc in af.fcurves_of(cam):
            if fc.data_path == "rotation_euler":
                m = fc.modifiers.new("NOISE")
                m.strength, m.scale = strength, scale
                m.use_restricted_range = True
                m.frame_start, m.frame_end = f0, f1
                m.blend_in = m.blend_out = 2

    def finish(self, step=1, bloom=(0.8, 0.8, 0.6), streaks=None, dispersion=0.0, kuwahara=0, save_blend=True):
        import face, acting
        if face.REGISTRY:
            acting.apply(self.sid)
            face.bake_all(1, self.n)
        af.compositor(bloom=bloom, streaks=streaks, dispersion=dispersion, kuwahara=kuwahara)
        out_dir = os.path.join(RENDERS, self.sid)
        os.makedirs(out_dir, exist_ok=True)
        if save_blend:
            af.save(os.path.join(out_dir, self.sid + ".blend"))
        A = self.A
        sc = self.sc
        if A["mode"] == "final":
            sc.render.resolution_percentage = 100
            af.render_anim(out_dir, 1, self.n, step)
        else:
            os.makedirs(PREVIEWS, exist_ok=True)
            sc.render.resolution_percentage = A["scale"]
            frames = A["frames"] or [1, max(1, self.n // 2), self.n]
            for f in frames:
                af.render_still(os.path.join(PREVIEWS, f"{self.sid}_{f:04d}.png"), f)
        print("AF: finished", self.sid, A["mode"])
