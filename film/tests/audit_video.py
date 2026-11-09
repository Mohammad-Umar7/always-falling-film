"""Audit a finished cut: probe it, then grab the story's key beats into one contact sheet.
    python tests/audit_video.py final/AlwaysFalling_V3.mp4 final/critique/V3_audit.jpg"""
import os, sys, json, subprocess, shutil
from PIL import Image, ImageDraw

FFMPEG = shutil.which("ffmpeg") or r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE = shutil.which("ffprobe") or r"C:\ffmpeg\bin\ffprobe.exe"
BEATS = [(2.5, "opening card"), (8, "two skies"), (13, "title"), (17, "dusk + kites"), (24, "next week"), (33, "always falling"),
         (42, "the promise"), (49, "asleep"), (52, "goodbye"), (57, "the slash"), (62, "launch"), (78, "radio"), (95, "silent"),
         (104, "1976"), (122, "1977"), (132, "tapes"), (152, "rain"), (165, "1980"), (174, "last tape"), (185, "1981"),
         (205, "orbits"), (216, "radio news"), (220, "home after 17 yrs"), (230, "re-entry"), (240, "both look up"),
         (247, "the burn"), (252, "the reveal"), (258, "J1"), (267, "Abba"), (272, "the door"), (276, "I'm home"),
         (281, "every night"), (285, "so did I"), (290, "epilogue"), (296, "credits")]


def main(src, out):
    meta = json.loads(subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration,size:stream=codec_name,width,height,nb_frames",
                                      "-of", "json", src], capture_output=True, text=True).stdout)
    print(json.dumps(meta))
    tiles = []
    for t, label in BEATS:
        raw = subprocess.run([FFMPEG, "-v", "error", "-ss", str(t), "-i", src, "-frames:v", "1", "-vf", "scale=480:270",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if len(raw) < 480 * 270 * 3:
            continue
        im = Image.frombytes("RGB", (480, 270), raw[:480 * 270 * 3])
        ImageDraw.Draw(im).text((5, 3), f"{t}s {label}", fill=(255, 255, 0))
        tiles.append(im)
    W = 5
    sheet = Image.new("RGB", (480 * W, 270 * ((len(tiles) + W - 1) // W)))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % W) * 480, (i // W) * 270))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out, quality=82)
    print("sheet", out, sheet.size)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
