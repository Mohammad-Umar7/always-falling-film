ROOT = __file__.rsplit("tests", 1)[0]
p = ROOT + "shots/half.py"
s = open(p, encoding="utf-8-sig").read()


def rep(a, b):
    global s
    assert a in s, "MISSING: " + a[:80]
    s = s.replace(a, b, 1)


# F3L: camera on the left wall where the note is pinned; shelf moved below the note (done in sets_room)
rep('''    S.cam("cam", keys=[(1, (0.9, -0.2, 1.62), (1.62, 0.15, 1.65), 34.0), (240, (0.95, -0.15, 1.62), (1.62, 0.2, 1.65), 36.0)])''',
    '''    S.cam("cam", keys=[(1, (-0.55, 0.05, 1.42), (-1.62, 0.25, 1.42), 30.0), (240, (-0.6, 0.08, 1.42), (-1.62, 0.25, 1.44), 33.0)])''')
# I3R: three-quarter view of the upturned, orange-lit face
rep('''    S.cam("cam", keys=[(1, (1.75, -5.75, sets_hyd.LANE_Z + 1.2), (1.5, -7.2, sets_hyd.LANE_Z + 1.7), 42.0),
                       (168, (1.74, -5.77, sets_hyd.LANE_Z + 1.2), (1.5, -7.2, sets_hyd.LANE_Z + 1.75), 44.0)])''',
    '''    S.cam("cam", keys=[(1, (2.3, -5.95, sets_hyd.LANE_Z + 1.55), (1.52, -6.6, sets_hyd.LANE_Z + 1.62), 50.0),
                       (168, (2.28, -5.97, sets_hyd.LANE_Z + 1.55), (1.52, -6.6, sets_hyd.LANE_Z + 1.66), 54.0)])''')
# I4W: from the son's side so the father below is visible
rep('''    S.cam("cam", keys=[(1, (1.8, -5.15, 2.55), (1.5, -6.9, -5.7), 26.0), (240, (1.95, -4.95, 2.95), (1.5, -6.9, -5.9), 23.0)])''',
    '''    S.cam("cam", keys=[(1, (2.55, -5.1, 2.3), (1.45, -6.75, -5.6), 26.0), (240, (2.75, -4.9, 2.7), (1.45, -6.75, -5.8), 23.0)])''')
# J1: tighter on the father
rep('''    S.cam("cam", keys=[(1, (1.35, -5.65, 1.55), (1.5, -6.7, sets_hyd.LANE_Z + 1.4), 30.0), (192, (1.35, -5.68, 1.5), (1.5, -6.7, sets_hyd.LANE_Z + 1.5), 36.0)])''',
    '''    S.cam("cam", keys=[(1, (1.35, -5.65, 1.55), (1.5, -6.65, sets_hyd.LANE_Z + 1.2), 52.0), (192, (1.35, -5.68, 1.5), (1.5, -6.65, sets_hyd.LANE_Z + 1.3), 62.0)])''')
# K1W: end closer
rep('''(240, (-0.3, -4.2, 2.4), (-6.0, 60.0, 8.0), 26.0)])''', '''(240, (-0.3, -3.0, 2.0), (-6.0, 60.0, 8.0), 28.0)])''')
# F2L: bigger player
rep('''    rec, reels = A.cassette_recorder(Vector((0, 0, 0)), name="boyplayer")
    hand = bone_tail(boy, "lowerarm02.L")''', '''    rec, reels = A.cassette_recorder(Vector((0, 0, 0)), name="boyplayer")
    rec.scale = (1.3, 1.3, 1.3)
    hand = bone_tail(boy, "lowerarm02.L")''')
# render quieter shots on twos
rep('''S = globals()["P_" + PRESET]()
S.finish(step=1)''', '''S = globals()["P_" + PRESET]()
S.finish(step=2)''')
open(p, "w", encoding="utf-8").write(s)

p = ROOT + "lib/sets_room.py"
s = open(p, encoding="utf-8-sig").read()
a = '''        parts.append(box("br_shelf", (0.12, 0.9, 0.03), (1.6, 0.0, 1.65), self.m_wood))'''
assert a in s
s = s.replace(a, '''        parts.append(box("br_shelf", (0.12, 0.9, 0.03), (-1.6, 0.25, 1.22), self.m_wood))''')
a = '''            c = box(f"br_cas{k}", (0.07, 0.017, 0.11), (1.6, -0.4 + k * 0.022, 1.72), cas)'''
assert a in s
s = s.replace(a, '''            c = box(f"br_cas{k}", (0.07, 0.017, 0.11), (-1.6, -0.15 + k * 0.022, 1.29), cas)''')
open(p, "w", encoding="utf-8").write(s)
import ast
ast.parse(open(ROOT + "shots/half.py", encoding="utf-8").read())
print("patch2 ok")
