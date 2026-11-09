ROOT = __file__.rsplit("tests", 1)[0]


def patch(rel, pairs):
    p = ROOT + rel
    s = open(p, encoding="utf-8-sig").read()
    for a, b in pairs:
        assert a in s, rel + " MISSING: " + a[:100]
        s = s.replace(a, b, 1)
    open(p, "w", encoding="utf-8").write(s)
    import ast
    ast.parse(s)


# B5: moon, Charminar and the two figures on one axis; roof in the lower third, horizon in the upper third
patch("shots/b5.py", [('''S.cam("cam", keys=[(1, (6.0, -18.0, 12.5), (-3.0, 22.0, 4.5), 28.0),
                   (120, (7.0, -21.0, 16.0), (-4.0, 26.0, 7.0), 28.0)])''',
                       '''S.cam("cam", keys=[(1, (6.0, -16.0, 7.0), (-0.4, 2.94, 4.2), 24.0),
                   (120, (6.7, -18.0, 7.8), (-0.3, 2.9, 4.6), 24.0)])''')])
# B1: end on both figures whole, from behind-side, the low sun beyond them
patch("shots/b1.py", [('''                   (144, (2.6, 0.2, 1.75), (-12.0, -11.0, 3.2), 30.0)])''',
                       '''                   (144, (3.6, 1.6, 2.3), (-12.0, -11.0, 1.2), 28.0)])''')])
# trees: coloured foliage that does not self-shadow into black noisy blobs
patch("lib/sets_hyd.py", [
    ('''        leaf=("#1E5A56", "#0C2428", "#3E9A84"), trunk=("#2A2A48", "#10101E", "#46467A"),''',
     '''        leaf=("#2A7C6C", "#1A4652", "#52B898"), trunk=("#2A2A48", "#10101E", "#46467A"),'''),
    ('''        leaf=("#3A4A3A", "#1C2230", "#6A7A50"), trunk=("#3A2A2A", "#1A1218", "#5E4440"),''',
     '''        leaf=("#5C6E44", "#3A3A4C", "#8EA05A"), trunk=("#3A2A2A", "#1A1218", "#5E4440"),'''),
    ('''            tr, tk = af.tree_blob(f"neem{i}", (x, y, LANE_Z), radius=rnd.uniform(3.0, 5.0), blobs=10, seed=i + 20,
                                  mat=self.m_leaf, trunk_mat=self.m_trunk, trunk_h=rnd.uniform(5.0, 8.0))''',
     '''            tr, tk = af.tree_blob(f"neem{i}", (x, y, LANE_Z), radius=rnd.uniform(3.0, 5.0), blobs=10, seed=i + 20,
                                  mat=self.m_leaf, trunk_mat=self.m_trunk, trunk_h=rnd.uniform(5.0, 8.0))
            tr.visible_shadow = False'''),
])
# C1F: camera across the lane on the father's right, so the suitcase in his right hand is seen
patch("shots/half.py", [
    ('''    S.cam("cam", keys=[(1, (0.2, -6.5, sets_hyd.LANE_Z + 0.95), (8.0, -7.2, sets_hyd.LANE_Z + 1.2), 34.0), (144, (0.25, -6.5, sets_hyd.LANE_Z + 0.95), (8.0, -7.2, sets_hyd.LANE_Z + 1.25), 36.0)])''',
     '''    S.cam("cam", keys=[(1, (0.1, -7.75, sets_hyd.LANE_Z + 0.95), (8.0, -6.8, sets_hyd.LANE_Z + 1.2), 34.0), (144, (0.15, -7.75, sets_hyd.LANE_Z + 0.95), (8.0, -6.8, sets_hyd.LANE_Z + 1.25), 36.0)])'''),
    # E1R: no table lamp between the lens and the letter; keep its warm light; see his face as he folds the note in
    ('''    A = sets_auh.Auh(time="night", seed=12, year=1976)
    A.sky()
    A.room()
    r = poses.load_chars(["FATHER_75_WORK"], palette=scene_auh.NIGHT_CAST)
    fa = r["FATHER_75_WORK"]
    place(fa, (0.85, 0.32, 0.0), 180)
    poses.apply(fa, poses.merge(poses.SIT, {"head": (18, 0, 0), "neck01": (10, 0, 0)}), frame=1)''',
     '''    A = sets_auh.Auh(time="night", seed=12, year=1976)
    A.sky()
    A.room(lamp=False)
    af.add_point("room_lamp", (1.25, 1.05, 1.05), "#FFD49A", energy=60.0, radius=0.08)
    r = poses.load_chars(["FATHER_75_WORK"], palette=scene_auh.NIGHT_CAST)
    fa = r["FATHER_75_WORK"]
    place(fa, (0.85, 0.32, 0.0), 180)
    poses.apply(fa, poses.merge(poses.SIT, {"head": (18, 0, 0), "neck01": (10, 0, 0)}), frame=1)'''),
    ('''    S.cam("cam", keys=[(1, (1.45, 1.35, 1.12), (0.95, 0.88, 0.8), 34.0), (144, (1.42, 1.32, 1.1), (0.95, 0.88, 0.8), 36.0)])''',
     '''    S.cam("cam", keys=[(1, (1.75, 0.55, 1.22), (0.9, 0.78, 0.98), 32.0), (144, (1.72, 0.57, 1.2), (0.9, 0.8, 0.96), 34.0)])'''),
])
print("shot fixes patched")
