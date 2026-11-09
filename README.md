# ALWAYS FALLING

Short film for the DADC Short Film Festival 2026 (IIT Delhi Abu Dhabi), theme **GRAVITY** — team FirstCommit.

1975: the week India launches its first satellite, Aryabhata, a father leaves Hyderabad to work in Abu Dhabi and
promises his son they will both look up at it every night. The satellite goes silent after four days but keeps
circling for seventeen years — the only thing that crosses between two drifting lives — until in February 1992
it finally falls home.

Anime-style 3DCG built in Blender 5.1 with Python scripts, post-processed in Python (numpy/OpenCV), sound
designed in code + ElevenLabs. See `film/PRODUCTION_BIBLE.md` for the full shot list, palettes and pipeline.

## Layout
- `film/lib/af.py` — shared Blender helpers (cel shading, outlines, skies, clouds, vegetation, compositor)
- `film/shots/` — one build + render script per shot
- `film/post/` — 2D FX (impact frames, speed lines, split screen, text), audio, final assembly
- `film/tests/` — look-development scripts
- `film/assets/` — downloaded and generated assets (not committed; sources below)

## Third-party assets (all free licences)
- Earth day map: "Whole world - land and oceans" (NASA, public domain) via Wikimedia Commons
- Earth night lights: "Earth's City Lights by DMSP, 1994–1995" (NASA, public domain) via Wikimedia Commons
- Fonts (SIL Open Font License): IBM Plex Mono, Shippori Mincho, Noto Sans
- Human base meshes: MPFB / MakeHuman (CC0)

## AI use (declared)
Concept developed with Claude, ChatGPT and Gemini; scenes scripted by Claude (Anthropic); voices and some sound
effects generated with ElevenLabs.
