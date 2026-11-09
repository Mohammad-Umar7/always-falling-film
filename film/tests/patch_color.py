# Colour overhaul for the Hyderabad night palette + cloud/milky way + character night palette.
import re
ROOT = __file__.rsplit("tests", 1)[0]

p = ROOT + "lib/sets_hyd.py"
s = open(p, encoding="utf-8-sig").read()
start = s.index('    "night": dict(')
end = s.index('    "dusk": dict(')
night = '''    "night": dict(
        sky=[(-1.0, "#120A26"), (-0.01, "#E07A6A"), (0.02, "#B0568A"), (0.07, "#4C46A0"), (0.18, "#232E8E"), (0.45, "#141A60"), (1.0, "#0A0A32")],
        ambient="#2A2A6A", amb=0.75, key_dir=(-0.55, 0.6, -0.45), key_col="#A8D8FF", key_e=2.4,
        stars=dict(density=0.07, size=0.075, scale=240, bright=5.5, color="#F0F4FF"),
        walls=[("#8A4E96", "#3A2050", "#C482D6"), ("#2E7A92", "#14384E", "#62B6D0"), ("#9A8450", "#463A2A", "#D8C07C"),
               ("#3E8A78", "#1A3E3A", "#76C8B0"), ("#5E5EAE", "#282C58", "#9A9AE6")],
        concrete=("#4E5690", "#22264C", "#8890D0"), wood=("#4A3450", "#201628", "#76567E"),
        rope=("#6E6290", "#302A4C", "#A496C8"), cloth=[("#E05A7A", "#6A2448", "#FF9AB0"), ("#F2C04A", "#7A5A30", "#FFE48A"), ("#4AC0D8", "#1E5A78", "#9AE8FF")],
        leaf=("#1E5A56", "#0C2428", "#3E9A84"), trunk=("#2A2A48", "#10101E", "#46467A"),
        far1="#3A3E86", far2="#2C2E6E", far3="#1E2054", farwin="#FFC46A", win="#FFB858", win_e=3.2,
        clay=("#A05A50", "#4A2434", "#D88A6E"), flower=("#E0408E", "#6E1A4C", "#FF7AC0"),
        outline="#0A0A22", wire="#08081A", lamp="#FFC27A"),
'''
s = s[:start] + night + s[end:]
s = s.replace('lit = (self.time == "night" and rnd.random() < 0.33) or (self.time == "dusk" and rnd.random() < 0.18)',
              'lit = (self.time == "night" and rnd.random() < 0.45) or (self.time == "dusk" and rnd.random() < 0.22)')
s = s.replace('cm = T("cloud_" + self.time, ("#3D5288", "#1E2A55", "#8FA6DA") if self.time == "night" else ("#F0A8A0", "#B0708E", "#FFE0B8"),\n                   rim="#C8DAFF" if self.time == "night" else "#FFE8C8", band=0.3)',
              'cm = T("cloud_" + self.time, ("#6A4CA6", "#2E2266", "#D08ACC") if self.time == "night" else ("#F0A8A0", "#B0708E", "#FFE0B8"),\n                   rim="#9FE8FF" if self.time == "night" else "#FFE8C8", band=0.3)')
s = s.replace('milky=dict(axis=(0.35, 0.75, 0.55), width=0.2, bright=0.22, color="#8EA2E6") if self.time == "night" else None,',
              'milky=dict(axis=(0.35, 0.75, 0.55), width=0.22, bright=0.42, color="#C8A0F0") if self.time == "night" else None,')
open(p, "w", encoding="utf-8").write(s)

p = ROOT + "lib/poses.py"
s = open(p, encoding="utf-8-sig").read()
start = s.index("NIGHT_CAST = {")
end = s.index("}", s.index('"EYE_LASH"')) + 1
cast = '''NIGHT_CAST = {
    "SKIN": ("#9A6A7E", "#3E2A50", "#D49CA6", "#A8E0FF"),
    "SKIN_BOY": ("#A07082", "#402C52", "#DAA2AC", "#A8E0FF"),
    "HAIR": ("#16163A", "#08081C", "#3A4280", "#8FD0FF"),
    "HAIR_GREY": ("#58587A", "#2A2A44", "#9A9ACC", "#BFE6FF"),
    "EYE": ("#0A0810",),
    "CLOTH_WHITE": ("#B4C0F0", "#5A5CA0", "#EEF2FF"),
    "CLOTH_SHIRT_WORK": ("#5A86C8", "#283E78", "#8EB6F0"),
    "CLOTH_TROUSER": ("#2E2C50", "#141428", "#4A4878"),
    "CLOTH_VEST": ("#8A2A54", "#3E1028", "#C04A7A"),
    "CLOTH_SHIRT_92": ("#9AA8D8", "#4A5288", "#CAD4F8"),
    "CLOTH_SHIRT_BOY": ("#A8B6EA", "#4C5690", "#DCE6FF"),
    "CLOTH_SHORTS": ("#24407A", "#10203E", "#3E64A8"),
    "CLOTH_SHIRT_SON": ("#2E8AA6", "#143E56", "#5EC0DA"),
    "CLOTH_TROUSER_SON": ("#22223E", "#0E0E1E", "#3A3A62"),
    "CLOTH_BELT": ("#140C10", "#060406", "#2A1A20"),
    "EYE_WHITE": ("#8E96C8", "#4A4E7A", "#B6BEE8"),
    "EYE_IRIS": ("#100A0C",),
    "EYE_LASH": ("#08060A",),
}'''
s = s[:start] + cast + s[end:]
open(p, "w", encoding="utf-8").write(s)
print("colour patch ok")
