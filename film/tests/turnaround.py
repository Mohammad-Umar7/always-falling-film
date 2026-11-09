# Character turnaround renders for the audit loop (run inside Blender).
import bpy, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import af

OUT = os.path.join(af.ROOT, "tests")


def stage():
    sc = bpy.context.scene
    af.setup_scene(w=700, h=1000, samples=16)
    af.sky_world([(-1, "#3A4660"), (0, "#4B5A7C"), (1, "#5A6A90")], ambient="#2A3350", ambient_strength=0.8)
    for o in list(bpy.data.objects):
        if o.type in ("CAMERA", "LIGHT"):
            bpy.data.objects.remove(o, do_unlink=True)
    af.add_sun("key", (0.5, 0.8, -0.6), "#DCE6FF", energy=3.0, angle=1.0)
    af.add_sun("rim", (-0.3, -0.9, -0.2), "#9FB6FF", energy=1.5, angle=1.0)
    return af.add_camera("tcam", (0, -4.2, 1.0), (0, 0, 0.95), lens=50)


def turnaround(rig_name, tag, height=1.7, angles=(0, 35, 90, 180), face=True, hide_prefix_except=True):
    sc = bpy.context.scene
    cam = stage()
    rig = bpy.data.objects[rig_name]
    # hide other characters
    if hide_prefix_except:
        for o in bpy.data.objects:
            if o.type in ("CAMERA", "LIGHT"):
                continue
            mine = o == rig or o.parent == rig or (o.parent and o.parent.parent == rig)
            o.hide_render = not mine
    base = rig.location.copy()
    rig.location = (0, 0, 0)
    s = height / 1.7
    cam.location = (0, -4.2 * s, 1.0 * s)
    af.look_at(cam, (0, 0, 0.95 * s))
    paths = []
    for i, ang in enumerate(angles):
        rig.rotation_euler = (0, 0, math.radians(ang))
        p = os.path.join(OUT, f"turn_{rig_name}_{tag}_{i}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    if face:
        rig.rotation_euler = (0, 0, math.radians(25))
        cam.location = (0, -1.1 * s, 1.56 * s * 0.995)
        af.look_at(cam, (0, 0, 1.53 * s * 0.995))
        sc.render.resolution_x = sc.render.resolution_y = 800
        p = os.path.join(OUT, f"turn_{rig_name}_{tag}_face.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    rig.rotation_euler = (0, 0, 0)
    rig.location = base
    for o in bpy.data.objects:
        o.hide_render = False
    return paths
