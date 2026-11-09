# Preview the V3 life pass without touching lib/shot.py (renders in progress use it):
#   blender -b --factory-startup -P tests/life_test.py -- <shot script or preset> preview frames=... scale=...
# e.g. -- shots/b4a.py preview frames=1,13,25,37 scale=40     or     -- preset=J2 preview frames=...
import sys, os, runpy
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "lib"))
import shot, life

_orig = shot.Shot.finish


def _finish(self, *a, **k):
    life.apply(self.sid, self.n)          # additive modifiers; the original finish still runs acting + face bake
    return _orig(self, *a, **k)


shot.Shot.finish = _finish
argv = sys.argv[sys.argv.index("--") + 1:]
target = argv[0]
if target.startswith("preset="):
    script = os.path.join(ROOT, "shots", "half.py")
else:
    script = os.path.join(ROOT, target)
    sys.argv = sys.argv[:sys.argv.index("--") + 1] + argv[1:]
runpy.run_path(script, run_name="__main__")
