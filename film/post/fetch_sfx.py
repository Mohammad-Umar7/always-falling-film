"""Fetch real recorded sound effects for V3 (team feedback: "bad sound", "sfx").
Only CC0 (public-domain) sounds from Freesound, the high-quality previews. A manifest with every title, author
and link is written next to them for the credits / AI-and-assets declaration.
    python post/fetch_sfx.py
"""
import os, re, json, html, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "dl", "sfx")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

# key: (query, how many, min seconds, max seconds, words that must NOT be in the title)
WANT = {
    "crickets":      ("crickets night", 3, 20, 120, ("car", "traffic", "music", "rain", "wind", "mountain")),
    "night_city":    ("night ambience city distant", 2, 30, 120, ("music", "siren")),
    "pigeons":       ("pigeons cooing", 2, 8, 200, ("music",)),
    "birds_evening": ("birds evening india", 2, 15, 120, ("music",)),
    "crows":         ("crows cawing", 2, 5, 120, ("music",)),
    "street_india":  ("india street ambience", 2, 20, 120, ("music",)),
    "footsteps":     ("footsteps dirt walking", 2, 4, 60, ("run", "music")),
    "construction":  ("construction site ambience", 2, 20, 120, ("music",)),
    "wind_desert":   ("desert wind", 2, 15, 120, ("music",)),
    "rocket":        ("rocket launch", 3, 10, 120, ("music", "firework", "toy", "model")),
    "rumble":        ("deep rumble earthquake", 2, 8, 120, ("music",)),
    "radio_static":  ("radio static noise", 2, 4, 120, ("music", "voice", "speech")),
    "rain_roof":     ("rain on roof", 2, 20, 120, ("thunder", "music")),
    "cassette":      ("cassette tape play button", 3, 0.5, 30, ("music",)),
    "paper":         ("paper rustle letter", 2, 1, 30, ("music",)),
    "knock":         ("knocking wooden door", 3, 1, 20, ("music",)),
    "door_creak":    ("old door creak open", 2, 1, 20, ("music",)),
    "fire_roar":     ("fire roar burning", 2, 8, 120, ("music",)),
    "whoosh":        ("whoosh swoosh", 3, 0.4, 6, ("music",)),
    "train_horn":    ("train horn distant", 2, 3, 60, ("music",)),
    "flyby":         ("jet fly by", 2, 4, 40, ("music",)),
    "fan_hum":       ("ceiling fan hum", 1, 10, 120, ("music",)),
}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()


def search(q):
    url = ("https://freesound.org/search/?q=" + urllib.parse.quote_plus(q) +
           "&f=" + urllib.parse.quote('license:"Creative Commons 0"') + "&s=" + urllib.parse.quote("Downloads (most first)"))
    s = get(url).decode("utf-8", "ignore")
    items = []
    for blk in s.split('class="bw-player"')[1:]:
        g = lambda k: (re.search(k + r'="([^"]*)"', blk) or [None, ""])[1]
        sid, mp3 = g("data-sound-id"), g("data-mp3")
        if not sid or not mp3:
            continue
        items.append(dict(id=int(sid), user=html.unescape(g("data-username")), title=html.unescape(g("data-title")),
                          dur=float(g("data-duration") or 0), sr=g("data-samplerate"),
                          downloads=int(g("data-num-downloads") or 0),
                          preview=mp3.replace("-lq.mp3", "-hq.mp3"),
                          page=f"https://freesound.org/people/{urllib.parse.quote(g('data-username'))}/sounds/{sid}/"))
    return items


def main():
    os.makedirs(OUT, exist_ok=True)
    man_p = os.path.join(OUT, "manifest.json")
    man = json.load(open(man_p, encoding="utf-8")) if os.path.exists(man_p) else {}
    for key, (q, n, dmin, dmax, bad) in WANT.items():
        if key in man and len(man[key]) >= 1:
            continue
        try:
            items = search(q)
        except Exception as e:
            print("search failed", key, e)
            continue
        ok = [it for it in items if dmin <= it["dur"] <= dmax and not any(b in it["title"].lower() for b in bad)]
        got = []
        for it in ok[:n]:
            fn = f"{key}_{it['id']}.mp3"
            p = os.path.join(OUT, fn)
            try:
                if not os.path.exists(p):
                    open(p, "wb").write(get(it["preview"]))
                it["file"] = fn
                got.append(it)
            except Exception as e:
                print("  dl failed", it["preview"], e)
        man[key] = got
        print(f"{key:14s} {len(items):2d} hits -> {len(got)} kept: " + " | ".join(f"{g['title'][:38]} ({g['dur']:.0f}s)" for g in got))
        json.dump(man, open(man_p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        time.sleep(0.6)
    print("files:", len([f for f in os.listdir(OUT) if f.endswith(".mp3")]))


if __name__ == "__main__":
    main()
