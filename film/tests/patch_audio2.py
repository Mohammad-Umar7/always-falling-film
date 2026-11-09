ROOT = __file__.rsplit("tests", 1)[0]
p = ROOT + "post/audio.py"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert a in s, "MISSING: " + a[:90]
    s = s.replace(a, b, 1)


# launch: big but not a wall (target ~ -14 dBFS rms)
rep('''    put(boom(3.0, 0.7, 40), S(1452))''', '''    put(boom(3.0, 0.5, 40), S(1452))''')
rep('''    A(rumble(10.5, 0.33), S(1452), fade=0.05)
    for k in range(12):
        put(taiko(1.2, 0.30 + 0.03 * k, 80), S(1489) + k * 0.6)
    put(pad(["D2", "A2", "D3", "F#3"], 10.0, 0.11, 2400, 2.0, 1.0), S(1452))''', '''    A(rumble(10.5, 0.22), S(1452), fade=0.05)
    for k in range(12):
        put(taiko(1.2, 0.22 + 0.025 * k, 80), S(1489) + k * 0.6)
    put(pad(["D2", "A2", "D3", "F#3"], 10.0, 0.08, 2400, 2.0, 1.0), S(1452))''')
# the satellite dies
rep('''    put(boom(4.0, 1.0, 36), S(2101))''', '''    put(boom(4.0, 0.7, 36), S(2101))''')
# re-entry
rep('''    A(roar(15.0, 0.36), S(5353), fade=1.0)''', '''    A(roar(15.0, 0.27), S(5353), fade=1.0)''')
rep('''        put(taiko(1.0, 0.30 + 0.025 * k, 75), S(5400) + k * 0.55)''', '''        put(taiko(1.0, 0.22 + 0.02 * k, 75), S(5400) + k * 0.55)''')
rep('''        put(boom(2.0, 0.55, 50), S(f))''', '''        put(boom(2.0, 0.4, 50), S(f))''')
# the divider burns
rep('''    put(reverse_swell(2.0, 0.4, "D5"), S(5881) - 2.0)''', '''    put(reverse_swell(2.0, 0.28, "D5"), S(5881) - 2.0)''')
rep('''    put(boom(5.0, 1.0, 34), S(5881))''', '''    put(boom(5.0, 0.6, 34), S(5881))''')
# "Abba." is intimate, not loud
rep('''VO_GAIN = {"outdoor": 1.0, "radio": 0.8, "tape": 0.9, "tape_far": 0.72, "dry": 1.05}''',
    '''VO_GAIN = {"outdoor": 1.0, "radio": 0.8, "tape": 0.9, "tape_far": 0.72, "dry": 0.85}''')
open(p, "w", encoding="utf-8").write(s)
import ast
ast.parse(s)
print("audio patch 2 ok")
