"""V2 pipeline: chars_v2.blend + faces (expressions, blinks, lip-sync) - switched on by film/faces_on.flag"""
ROOT = __file__.rsplit("tests", 1)[0]


def patch(rel, pairs):
    p = ROOT + rel
    s = open(p, encoding="utf-8-sig").read()
    for a, b in pairs:
        assert a in s, rel + " MISSING: " + a[:90]
        s = s.replace(a, b, 1)
    open(p, "w", encoding="utf-8").write(s)
    import ast
    ast.parse(s)


patch("lib/poses.py", [
    ('''CHARS_BLEND = os.path.join(af.ASSETS, "chars.blend")''',
     '''V2 = os.path.exists(os.path.join(af.ROOT, "faces_on.flag"))
CHARS_BLEND = os.path.join(af.ASSETS, "chars_v2.blend" if V2 else "chars.blend")'''),
    ('''    if palette:
        retint(palette)
    return rigs''', '''    if palette:
        retint(palette)
    if V2:
        import face
        for n, r in rigs.items():
            face.REGISTRY[n] = face.Face(r)
    return rigs'''),
    ('''    "EYE_WHITE": ("#8E96C8", "#4A4E7A", "#B6BEE8"),''', '''    "EYE_WHITE": ("#C4CAF0", "#7C82B4", "#E6EAFF"),'''),
])
patch("lib/scene_auh.py", [
    ('''              "EYE_WHITE": ("#8A7478", "#44323A", "#B09AA0")}''', '''              "EYE_WHITE": ("#CDB6B4", "#7A6068", "#EEDCD8")}'''),
])
patch("lib/face.py", [
    ('''def faces(rigs, **kw):
    return {n: Face(r, **kw) for n, r in rigs.items()}''', '''REGISTRY = {}


def get(name):
    return REGISTRY[name]


def bake_all(f0, f1):
    for F in REGISTRY.values():
        if not getattr(F, "_baked", False):
            F.bake(f0, f1)
            F._baked = True'''),
])
patch("lib/shot.py", [
    ('''    def finish(self, step=1, bloom=(0.8, 0.8, 0.6), streaks=None, dispersion=0.0, kuwahara=0, save_blend=True):
        af.compositor(''', '''    def finish(self, step=1, bloom=(0.8, 0.8, 0.6), streaks=None, dispersion=0.0, kuwahara=0, save_blend=True):
        import face
        if face.REGISTRY:
            face.bake_all(1, self.n)
        af.compositor('''),
])
print("v2 pipeline patched")
