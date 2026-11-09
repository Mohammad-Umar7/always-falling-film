# C3d (1:09–1:12, 72f): orbit — the fairing splits open, Aryabhata spins free above the Earth, a glint of sun.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import bpy
from mathutils import Vector
import af, shot, scene_space as ss

S = shot.Shot("C3d", frames=72)
o = ss.setup(sun_dir=(0.75, -0.45, 0.48), latlon=(28.0, 50.0), lights=0.6)
sat = o["sat"]
white = af.toon_mat("stage_white", "#E8E6E0", shadow="#7C7E92", light="#FFFFFF", band=0.32, light_band=0.78, rim="#FFFFFF")
# upper stage below the satellite
stage = af.cylinder("stage2", 1.2, 4.0, (0, 0, -3.0), white, 32)
af.add_outline(stage, 0.03, "#141018")
# fairing halves (half cylinders + half cones), hinged at the base, opening outward
import bmesh
def half_shell(name, sgn):
    me = bpy.data.meshes.new(name)
    bm_ = bmesh.new()
    segs = 16
    prof = [(1.28, -0.9), (1.28, 1.2), (0.9, 2.1), (0.2, 2.7)]
    rings = []
    for r, z in prof:
        ring = []
        for k in range(segs + 1):
            a = math.pi * k / segs + (0 if sgn > 0 else math.pi)
            ring.append(bm_.verts.new((math.cos(a) * r, math.sin(a) * r, z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(segs):
            bm_.faces.new((rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k]))
    bm_.to_mesh(me)
    bm_.free()
    ob = af.link(bpy.data.objects.new(name, me))
    me.materials.append(white)
    so = ob.modifiers.new("t", "SOLIDIFY")
    so.thickness = 0.05
    af.add_outline(ob, 0.03, "#141018")
    return ob
for sgn, nm in ((1, "fairA"), (-1, "fairB")):
    h = half_shell(nm, sgn)
    piv = bpy.data.objects.new(nm + "_pivot", None)
    af.link(piv)
    piv.location = (0, sgn * 1.28, -0.9)
    h.parent = piv
    h.location = (0, -sgn * 1.28, 0)
    piv.rotation_euler = (0, 0, 0)
    piv.keyframe_insert("rotation_euler", frame=8)
    piv.keyframe_insert("location", frame=8)
    piv.rotation_euler = (math.radians(-sgn * 75), 0, 0)
    piv.location = (0, sgn * 6.0, 0.5)
    piv.keyframe_insert("rotation_euler", frame=40)
    piv.keyframe_insert("location", frame=40)
    piv.rotation_euler = (math.radians(-sgn * 130), 0, math.radians(sgn * 20))
    piv.location = (0, sgn * 14.0, 1.5)
    piv.keyframe_insert("rotation_euler", frame=72)
    piv.keyframe_insert("location", frame=72)
# satellite rises free and spins up
sat.location = (0, 0, 0.0)
sat.keyframe_insert("location", frame=20)
sat.location = (0, 0, 2.2)
sat.keyframe_insert("location", frame=72)
ss.spin(sat, 20, 72, (0.0, 0.0, 4.0))
ss.blink(o["leds"], ["110110", "101010", "111000"], 1, 72, step=3)
stage.location = (0, 0, -3.0)
stage.keyframe_insert("location", frame=20)
stage.location = (0, 0, -6.0)
stage.keyframe_insert("location", frame=72)
S.cam("cam", keys=[(1, (6.5, -7.5, 2.4), (0.0, 0.0, 0.6), 30.0), (72, (5.6, -6.6, 3.0), (0.0, 0.0, 1.6), 32.0)])
S.finish(step=1, bloom=(0.75, 1.0, 0.7), streaks=(2.0, 0.35, 6))
