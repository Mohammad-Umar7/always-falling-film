ROOT = __file__.rsplit("tests", 1)[0]
p = ROOT + "lib/build_chars.py"
s = open(p, encoding="utf-8-sig").read()


def rep(a, b):
    global s
    assert a in s, "MISSING: " + a[:90]
    s = s.replace(a, b, 1)


# boy shorts: two separate legs, not an A-line skirt
rep('''cloth.append(chars.trousers(body, rig, name + "_shorts", item[1], length="short", inflate=0.02, r_top=0.11, r_hem=0.11))''',
    '''cloth.append(chars.trousers(body, rig, name + "_shorts", item[1], length="short", inflate=0.013, r_top=0.08, r_hem=0.072))''')
# boy hair: short back and sides (nape visible), tighter shell, more and shorter spiky locks
rep('''                             hairline=0.052 if hair_style != "boy" else 0.06, side_frac=0.45 if hair_style == "70s" else 0.7,
                             nape=0.035 if hair_style == "70s" else 0.05, inflate=0.014 if hair_style == "70s" else 0.011)''',
    '''                             hairline=0.052 if hair_style != "boy" else 0.06, side_frac=0.45 if hair_style == "70s" else 0.78,
                             nape=0.035 if hair_style == "70s" else 0.095, inflate=0.014 if hair_style == "70s" else 0.008)''')
rep('''                             length=(0.07, 0.14) if hair_style == "70s" else (0.05, 0.1),''',
    '''                             length=(0.07, 0.14) if hair_style == "70s" else (0.035, 0.07),''')
for a in ('part_x=-0.02, fringe_dir=1.0, lock_count=60)', 'part_x=-0.02, fringe_dir=1.0, lock_count=60)', 'part_x=-0.025, fringe_dir=1.0, lock_count=65)'):
    rep(a, a.replace("lock_count=60", "lock_count=95").replace("lock_count=65", "lock_count=100"))
# write the new cast next to the old one (the running render queue still reads chars.blend)
rep('''af.save(os.path.join(af.ASSETS, "chars.blend"))''', '''af.save(os.path.join(af.ASSETS, os.environ.get("AF_CHARS_OUT", "chars_v2.blend")))''')
open(p, "w", encoding="utf-8").write(s)
import ast
ast.parse(s)
print("boy patch ok")
