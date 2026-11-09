# ALWAYS FALLING: defect tracker (V2 to final)

Rule: every character shot is checked at full resolution for limbs through furniture, crossed or twisted arms,
hands that do not touch what they hold, floating props, clipping, missing props, cut-off heads, and wrong facing.
Status: FIXED = code changed and preview verified · CODE = code changed, preview pending · OPEN = not fixed yet.

| Shot | Defect | Status |
|---|---|---|
| ALL | Anime eye decals sat 34 mm inside the head (eyes looked like slits) | FIXED (face.py conform) |
| ALL | No facial expressions; no blinks; no lip-sync | FIXED (face.py + acting.py) |
| ALL | Eyes and tears glowed (sci-fi look) | FIXED (toned down) |
| ALL | Relaxed hands looked like stiff claws | FIXED (HANDS_RELAX 24/12; pointing index straightened) |
| ALL | EEVEE speckle and too much grain | FIXED (bilateral denoise in post, grain 0.011) |
| Boys | Read as girls from behind (bob hair, skirt-like shorts) | FIXED (tucked shirts, narrow shorts, short haircut) |
| Adults outdoors | Barefoot in the lane and Abu Dhabi | FIXED (shoes) |
| FATHER_75_WORK | Skin sliver at the waist | FIXED (wider belt) |
| Abu Dhabi | Father looked shirtless (shirt colour close to skin) | FIXED (night and sunset palettes) |
| B1 | Black noisy tree blobs; boy cut off; arms leaning on air | FIXED |
| B2/B3 | Pointing hand reads as a claw | FIXED |
| B4a/B4b | Father turned his head away from the boy | FIXED |
| B4b | Hand on face, punching gesture | FIXED (face-to-face promise) |
| B5 | Figures not in frame | FIXED |
| C1F | Suitcase missing (attach bug), barefoot | FIXED |
| E1R | Lamp blocked the frame; arms crossed | FIXED |
| E2R | Head cut off; claw hands | FIXED |
| E3L | Note floated beside head (hand hidden) | FIXED (note in the raised fist) |
| F1L | Legs through the charpai; hands holding nothing | FIXED |
| F2L | Player covered the face | FIXED |
| F2R | Only a giant hand; lamp shade blocking | FIXED |
| F4L | Umbrella not held | FIXED |
| F5L/G1L | Shins through the bed; player floating | FIXED |
| F5R | Hands floating | FIXED |
| G2L | Hands never reach the shutters | FIXED |
| Rooms | Lamp hotspot ring on the wall | FIXED (bulb casts no shadow) |
| I1L | Legs through the parapet; hands floating | FIXED |
| I3R | Upturned face not visible | FIXED (sky POV) |
| I4W | Unreadable ultra-wide | FIXED (top-down) |
| J1 | Father tiny in frame | FIXED (long lens) |
| J3 | Facing away from door; stiff arm; suitcase vanished; door through camera | FIXED |
| C3a-c | Launch blown out; trail of separate beads | FIXED (dense plume) |
| H1 / all space | Photo-like Earth, white blob clouds | FIXED (cel map everywhere) |
| Post | Thesis text over final image; dense credits; subtitles hard to read | FIXED |
| ALL | Salt-and-pepper speckle in lit cel areas | FIXED (soft ramp edges, hard light shadows, 48 samples on close-ups) |
| Faces | Dark mouth-cavity patches at the mouth corners | FIXED (cavity smaller, set back) |
| I1L/I3L | Sitting through the parapet; hands floating | FIXED (on the parapet, palms down) |
| C2R | Moon out of frame | FIXED |
| E2L | Plain flat door | FIXED (Old City panels, studs, bolt, brass plate) |
| F3L | Empty wall; cassettes unlabelled | FIXED (calendar 1977-1980, labels) |
| FX | Not enough anime energy | FIXED (panel slam, focus lines, sweeps, glints, kirakira, audio cues) |
