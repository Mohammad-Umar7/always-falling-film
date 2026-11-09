# Space shot helpers
import bpy, math
from mathutils import Vector
import af, sets_space as sp


def setup(sun_dir=(0.85, -0.25, 0.35), latlon=(20.0, 68.0), lights=0.8, sun_visible=True, rim=None, sat=True, sun_energy=4.0,
          ambient_boost=None, alt=None):
    sc = bpy.context.scene
    sc.eevee.use_raytracing = False
    sc.eevee.use_fast_gi = False
    sp.space_world()
    sd = Vector(sun_dir).normalized()
    af.add_sun("sunlight", -sd, "#FFF6E8", energy=sun_energy, angle=0.6, shadow=False)
    if rim:
        af.add_sun("rimlight", Vector(rim[0]), rim[1], energy=rim[2], angle=2.0, shadow=False)
    alt_ = sp.ALT if alt is None else alt
    objs = sp.earth(center=(0, 0, -(sp.EARTH_R + alt_)), rot=sp.face_latlon(*latlon), lights=lights)
    out = {"earth": objs}
    if sun_visible:
        out["sun"] = sp.sun_disc(sd)
    if sat:
        root, body, leds = sp.aryabhata((0, 0, 0))
        out["sat"], out["body"], out["leds"] = root, body, leds
    return out


def spin(ob, f0, f1, rpm_deg_per_frame=(0.0, 0.0, 1.2), start=(0, 0, 0)):
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = start
    ob.keyframe_insert("rotation_euler", frame=f0)
    n = f1 - f0
    ob.rotation_euler = tuple(start[i] + math.radians(rpm_deg_per_frame[i] * n) for i in range(3))
    ob.keyframe_insert("rotation_euler", frame=f1)
    af.set_interp(ob, "LINEAR")


def blink(leds, pattern, f0=1, f1=240, step=6, die_at=None):
    """pattern: list of strings per led like '1101...' cycling; LEDs go dark from die_at."""
    for k, led in enumerate(leds):
        m = led.data.materials[0]
        em = [n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeEmission"][0]
        s = af.I(em, "Strength")
        pat = pattern[k % len(pattern)]
        i = 0
        for f in range(f0, f1 + 1, step):
            on = pat[i % len(pat)] == "1"
            if die_at is not None and f >= die_at:
                on = False
            s.default_value = 8.0 if on else 0.0
            s.keyframe_insert("default_value", frame=f)
            i += 1
        if die_at is not None:
            s.default_value = 0.0
            s.keyframe_insert("default_value", frame=die_at)
        nt = m.node_tree
        if nt.animation_data and nt.animation_data.action:
            for fc in af._fcurves(nt.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
