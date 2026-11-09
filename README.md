# ALWAYS FALLING

A 5-minute anime-style short film for the **DADC Short Film Festival 2026** (IIT Delhi Abu Dhabi), theme **GRAVITY**, by Team FirstCommit.

> Hyderabad, 1975. The week India launches its first satellite, Aryabhata, a father leaves for the building sites of
> Abu Dhabi. On their last night on the rooftop he tells his son that a satellite is *always falling toward the Earth,
> but moves so fast that it keeps missing*, and promises that every night when it passes they will both look up.
> The satellite goes silent after four days but keeps circling for seventeen years, the only thing that crosses
> between two drifting lives, until in February 1992 it finally falls home.

![Split screen: Hyderabad and Abu Dhabi](docs/split_captions.jpg)

| | |
|---|---|
| ![Launch panel slam](docs/launch_panels.jpg) | ![Re-entry: both look up](docs/reentry_focus_lines.jpg) |

![Abba](docs/abba.jpg)

## How it is made

Everything is generated from code: Blender 5.1 (EEVEE) scenes built and rendered by Python scripts, with a Python
compositor and a synthesised soundtrack.

- **Characters:** MPFB/MakeHuman base meshes (CC0) with scripted garments, hair and anime eyes. `film/lib/face.py` is
  a facial-expression engine with brows, lids, mouth via face bones, blinks, lip-sync from the voice clips, tears and eye
  sparkles. `film/lib/acting.py` is the acting sheet that keys every expression to its story beat.
- **Sets:** procedural Hyderabad Old City (Charminar skyline), 1970s Abu Dhabi construction sites, the Kosmos-3M
  launch, Earth from orbit (NASA Blue/Black Marble, posterised in the shader), a 92,000-orbit "cocoon" and the
  re-entry plasma (`film/lib/sets_*.py`, `film/lib/scene_*.py`).
- **Shots:** one build + render script per shot in `film/shots/`. The split-screen halves live in `film/shots/half.py`.
- **Anime look:** cel ramps with soft edges, inverted-hull ink outlines and animation on twos. In post
  (`film/post/edit.py`): impact frames, manga focus lines, a panel-slam montage, speed lines, light sweeps for time
  jumps, god rays, ink edges, line boil and paper grain.
- **Split-screen grammar:** Hyderabad (the son) on the left and Abu Dhabi (the father) on the right, as two slanted manga
  panels on a starry gap that widens over the years. Only the satellite crosses it, until re-entry burns it away.
- **Sound** (`film/post/audio.py`): tanpura drone, a plucked "promise" motif, pads, percussion and all sound effects
  synthesised with numpy/scipy. The stereo field follows the split.
- **Timeline** (`film/post/timeline.py`): the master edit (7,200 frames at 24 fps), subtitles, captions and voice placement.

Run a shot: `blender -b --factory-startup -P film/shots/half.py -- preset=J2 final`
Assemble: `python film/post/audio.py && python film/post/edit.py --audio film/audio/mix.wav --out film/final/film.mp4`

Rendered frames, videos, `.blend` files and downloaded assets are not committed (see `.gitignore`).

## Third-party assets (free licences)
- Earth maps: NASA Blue Marble / Black Marble (public domain), via Wikimedia Commons
- Human base meshes: MPFB / MakeHuman (CC0)
- Fonts (SIL Open Font License): IBM Plex Mono, Shippori Mincho, Noto Sans
- Voices: Piper TTS models: "rohan" (IIT Madras IndicTTS), "pratham", "alan" (en_GB), used under their published licences

## AI use (declared, as required by the festival)
- **Concept and script:** developed with Claude (Anthropic), ChatGPT (OpenAI) and Gemini (Google) as brainstorming and
  critique partners. The team chose the story, setting, language and creative direction.
- **Production code:** scene, character, animation, facial-expression, compositing and audio scripts written by Claude
  (an AI coding assistant) under the team's direction. All frames are rendered locally from these 3D scenes.
- **Voices:** AI text-to-speech (Piper, offline neural TTS).
- **Not used:** no generative image or video model created any frame.

The family is fictional. Aryabhata's history is real: launched 19 April 1975, power failure after four days,
mainframe signals until March 1981, re-entry in February 1992. The re-entry being visible over Hyderabad is
poetic licence.
