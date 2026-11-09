# ALWAYS FALLING — production bible

DADC Short Film Festival 2026 (IIT Delhi Abu Dhabi). Theme: GRAVITY. Team FirstCommit.
Deadline: formal 6 Nov 2026 23:59 GST, extended by WhatsApp "within 2 days" (≈ 11 Nov). Confirm with secretary.
Submission: Google Drive link ("anyone with link"), file `FilmTitle_TeamLead.mp4`, docket PDF 1–2 pages
(synopsis ≤200 words + process notes + DECLARE ALL AI USE). Specs: 3–15 min incl. credits, MP4/MOV,
≥1080p landscape, non-English speech needs burned-in English subtitles.
Content rules: no smoking/alcohol on screen (else age advisory), respect UAE/India, original or licensed assets only.

## Logline
1975: the week India launches its first satellite, a father leaves Hyderabad (Old City) to work in Abu Dhabi and promises
his 5-year-old son they will both look up at it every night. The satellite goes silent after four days but
keeps circling for seventeen years — the only thing that crosses between two drifting lives — until in
February 1992 it finally falls home.

Thesis line (father, 1975): "It is always falling toward home… and always missing."
End card: "17 YEARS FALLING TOWARD HOME. / THIS TIME, IT DIDN'T MISS."

## True facts used (keep accurate)
- Aryabhata launched 19 Apr 1975 (Kosmos-3M rocket, USSR). 26-sided polyhedron, 1.4 m, body-mounted solar cells.
- Power failure after ~4 days (60 orbits): experiments halted, signals lost after ~5 days (NASA HEASARC).
- ISRO: "spacecraft mainframe active till March 1981".
- Re-entered Earth's atmosphere Feb 1992 (10 or 11 Feb, sources differ). ~92,000 orbits.
- Pictured on the ₹2 note from 1976 (so the note arrives by post in 1976, NOT given in 1975).
- Poetic licence (say so in docket): re-entry visibility over Hyderabad is not documented; the heartbeat beep is
  non-diegetic sound design, not received telemetry; the family is fictional.

## Formal device: THE SPLIT
- On Earth, after the father leaves, the frame is split: LEFT = Hyderabad (cool teal/blue/green), RIGHT = Abu Dhabi (gold/amber).
- The ONLY thing that ever crosses the divider is the satellite's moving dot. (The letter does NOT cross:
  posted on the right, match-cut to it landing on the left.)
- Divider widens 6 px (1975) → ~240 px (Mar 1981), with the drift.
- Space shots are FULL frame: only from orbit is the world whole.
- Climax: the burning satellite burns THROUGH the divider (fire-dissolve, no glass shatter) and the halves
  collapse into one frame: son on the roof, father in the lane below at the door with his suitcase.
- Opening = final image cropped into two halves with two different grades (misdirection). Final = same shot,
  divider dissolves, grades merge, camera widens: same rooftop, suitcase beside them.

## Style
- Anime 3DCG: cel shading (Shader-to-RGB → constant ramps), tinted shadows, rim light, inverted-hull outlines.
- Characters: MPFB humans, mostly silhouettes / backs / hands. Character poses stepped (on twos/threes);
  camera moves smooth (on ones). Climax re-entry fully on ones.
- Painted skies: gradient world + cel-shaded procedural cloud cards + star field + moon.
- Post (Python/numpy/cv2): speed lines, impact frames (B/W inverted 1–3 f), chromatic aberration, bloom,
  grain, vignette, camera shake, burn-dissolve divider, mission-log typewriter text, subtitles.
- Mission log font: monospace (DejaVu Sans Mono from Blender, Bitstream Vera licence) or OFL font.

## Palettes
- Hyderabad night: zenith #0B1A3A, horizon #2E6F8E, moon key #9FC7FF, shadow #1B2340, silhouettes #06121F, window #FFB35C
- Hyderabad dusk: zenith #1C2B5A, mid #7A4F8C, horizon #FF9A5A, sun glow #FFD9A0
- Abu Dhabi day/sunset: zenith #6B4FA0 → #FFB347 → horizon #FF7A3D, shadow #6B3A2A, silhouettes #2A140C
- Abu Dhabi night: zenith #1A1030, horizon #8A4A2A (sodium glow)
- Space: #02030A, ocean #0E3D8C/#1F6FD1, atmosphere rim #6FD3FF, sun #FFF6E0, cells #1B2A6B/#8FB4FF, foil #E8B04A
- Re-entry plasma: #FFFFFF → #FFD27A → #FF6A2A → #B0247A, smoke #3A2030

## Timeline (24 fps, 7200 frames = 5:00). F = full frame, S = split (L|R)
| id | time | frames | lay | content |
|---|---|---|---|---|
| A1 | 0:00–0:04 | 1–96 | F | black, one soft beep, tanpura drone fades in |
| A2 | 0:04–0:12 | 97–288 | S | two silhouettes looking up (son L cool, father R warm); a dot crosses L→R |
| A3 | 0:12–0:15 | 289–360 | F | title ALWAYS FALLING (letters settle downward) |
| B1 | 0:15–0:21 | 361–504 | F | dusk Old City Hyderabad, pigeons circling, crane up to the terrace; "HYDERABAD, APRIL 1975" |
| B2 | 0:21–0:29 | 505–696 | F | father+boy lying on a charpai on the terrace (hot April night), father points up (sub: satellite next week) |
| B3 | 0:29–0:37 | 697–888 | F | side angle; glowing line drawn across the sky shows an orbit; thesis line |
| B4 | 0:37–0:45 | 889–1080 | F | the promise, two-shot rim-lit; suitcase by the water tank |
| B5 | 0:45–0:50 | 1081–1200 | F | high wide: two tiny figures under the stars |
| C1 | 0:50–0:56 | 1201–1344 | F→S | boy at the house door in the lane, father walks away down the gali; white SLASH splits frame; R becomes Abu Dhabi "ABU DHABI, 1975" |
| C2 | 0:56–1:00 | 1345–1440 | S | both look up at night, no dot yet; "19 APRIL 1975" |
| C3 | 1:00–1:12 | 1441–1728 | F | LAUNCH: ignition impact frame, smoke, climb, stage sep, satellite released, "ORBIT 1" |
| C4 | 1:12–1:20 | 1729–1920 | F | satellite over India/Gulf at night, telemetry voice begins |
| D1 | 1:20–1:30 | 1921–2160 | F | telemetry: "day four… power bus vol—" CUT, impact frame, silence, lights die |
| D2 | 1:30–1:40 | 2161–2400 | F | silent tumbling; log "DAY 4. POWER FAILURE." "STATUS: SILENT." "STILL IN ORBIT." heartbeat starts |
| E1 | 1:40–1:46 | 2401–2544 | S | R: father folds ₹2 note into letter; L: boy looks up, dot crosses; "1976" |
| E2 | 1:46–1:52 | 2545–2688 | S | R: envelope into post box slot; L: match-cut, envelope lands inside the house |
| E3 | 1:52–2:00 | 2689–2880 | S | L: boy holds note to the sky, printed satellite aligns with real dot; R: father looks up |
| F1 | 2:00–2:10 | 2881–3120 | S | R: father on scaffolding, skyline grows; L: boy (8) homework on terrace; 1977–78 |
| F2 | 2:10–2:20 | 3121–3360 | S | cassette: R records, L listens (VO on tape); 1979 |
| F3 | 2:20–2:30 | 3361–3600 | S | walls: note pinned, cassette row stops growing; calendars flip; gap visibly wider |
| F4 | 2:30–2:40 | 3601–3840 | S | ritual montage: monsoon night L / hazy night R, dot crossing each time |
| F5 | 2:40–2:50 | 3841–4080 | S | boy (11) plays a tape, voice fainter |
| G1 | 2:50–2:58 | 4081–4272 | S | last tape: "Beta… next year, maybe—" hiss, click; beep STOPS; "MARCH 1981. MAINFRAME SILENT." |
| G2 | 2:58–3:04 | 4273–4416 | S | L: boy closes the wooden shutters; R: father still looks up, dot passes, no beep |
| G3 | 3:04–3:10 | 4417–4560 | S | silence; "STILL IN ORBIT." |
| H1 | 3:10–3:35 | 4561–5160 | F | 92,000 ORBITS: trails wrap Earth in gold+blue cocoon, counter races, years 1982–1991 |
| I1 | 3:35–3:43 | 5161–5352 | S | L: son (22) on terrace not looking up; R: father in shadow vs plain wall, suitcase handle; "10 FEBRUARY 1992" |
| I2 | 3:43–3:58 | 5353–5712 | F | RE-ENTRY sakuga on ones: plasma, panels tear off, smears, impact frames, fireball |
| I3 | 3:58–4:05 | 5713–5880 | S | L: streak blazes, son looks up (lit orange); R: father's face lit, looking up |
| I4 | 4:05–4:15 | 5881–6120 | F | fireball burns through divider; halves collapse: son on roof, father in the lane below with suitcase |
| J1 | 4:15–4:23 | 6121–6312 | F | son's POV down into the lane, father lowers his gaze; silence |
| J2 | 4:23–4:30 | 6313–6480 | F | close on son: "Abba." (sub: Father.) |
| J3 | 4:30–4:35 | 6481–6600 | F | hand on the door chain-knocker, door opens |
| K1 | 4:35–4:45 | 6601–6840 | S→F | opening shot replays; divider dissolves, grades merge, pull back: both on the roof + suitcase; end card |
| L1 | 4:45–5:00 | 6841–7200 | F | title + credits + facts + AI declaration |

## Dialogue — Hindi/Urdu (Hindustani), AI voice via ElevenLabs (declared), burned-in English subs
- B2: "Next week, our country sends a satellite up there."
- B3: "It is always falling toward the Earth. But it moves so fast, it keeps missing. Always falling toward home… and always missing."
- B4: "Every night when it passes, I'll look up. You look up too. Then we'll be looking at the same thing."
- F2 (tape): "Beta… Abba is fine. The building is very tall now. You look up at night, don't you?"
- F5 (tape, fainter): "Beta… study hard… look after Ammi…"
- G1 (last tape): "Beta… forgive me… next year, maybe—" (hiss)
- D1 (telemetry, English radio): "Telemetry nominal… spin rate stable… day three, panel current dropping… day four… power bus vol—"
- J2 (son): "Abba."

## Pipeline
- `lib/af.py` shared Blender helpers (toon mats, outlines, skies, clouds, stars, render setup).
- `shots/<id>.py` builds + renders a shot in background Blender (`blender -b -P`). Renders → `renders/<id>/####.png`.
- `assets/` humans.blend (MPFB), downloaded textures (NASA Blue/Black Marble, public domain), fonts.
- `post/` numpy/cv2 FX + split compositor + text → `final/frames`, audio synth → `audio/`, ffmpeg → `final/`.

## Setting update (9 Nov): Hyderabad Old City, Hindi/Urdu
- Home = Old City Hyderabad: flat terraces with parapets, charpai rope cots (families sleep on roofs on hot nights),
  clotheslines, clay matka, pigeon coop + pigeon flocks circling at dusk (they always come home = orbit rhyme),
  neem trees, a few palms, domes/minarets, Charminar on the skyline, narrow gali (lane) with a wooden double door.
- Son calls him "Abba". Mother = "Ammi". Father's lines in Hindustani (Devanagari for TTS):
  B2 अगले हफ़्ते, अपने मुल्क का पहला सैटेलाइट ऊपर जाने वाला है।
  B3 वो हमेशा ज़मीन की तरफ़ गिरता रहता है… लेकिन इतनी तेज़ी से चलता है कि हर बार चूक जाता है। हमेशा घर की तरफ़ गिरता है… और हमेशा चूक जाता है।
  B4 हर रात जब वो गुज़रेगा, मैं ऊपर देखूँगा। तुम भी ऊपर देखना। फिर हम दोनों एक ही चीज़ देख रहे होंगे।
  F2 बेटा… अब्बा ठीक हैं। बिल्डिंग अब बहुत ऊँची हो गई है। रात को ऊपर देखते हो ना?
  F5 बेटा… दिल लगा के पढ़ना… अम्मी का ख़्याल रखना…
  G1 बेटा… माफ़ करना… अगले साल, शायद—
  J2 (son) अब्बा।
- Approvals (user, 9 Nov): ElevenLabs for father voice + telemetry + SFX (declare AI); upload stills to ChatGPT/Gemini
  for critique; private GitHub backup (scripts only); at the end upload MP4 + docket to Google Drive and set the
  film link to "anyone with the link" (user submits the form themselves). Team names: user will send later.
- Characters: MPFB base humans (CC0) + procedural anime hair/clothes + cel shading + outlines; audit/refine loop
  (own checklist + ChatGPT + Gemini critiques on stills).