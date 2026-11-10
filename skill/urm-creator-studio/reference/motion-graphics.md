# Motion graphics standards

## Timing
- Text in: 0.4 s (fade/slide/zoom with ease-out); text out: 0.35 s fade. Start text 0.2–0.4 s after a cut.
- Hold time ≥ 1.5 s + 0.3 s per word. Word-by-word: 0.12–0.45 s per word (auto from available time).
- Transitions: 0.3–0.4 s (energetic), 0.5–0.7 s (elegant). Never longer than 40 % of the shortest scene
  (the engine caps it).
- Intro 1.5–2.5 s, outro 2.5–4 s. Do not exceed 10 % of the video for intro+outro on social.

## Safe areas (fractions of the frame; text is laid out inside these automatically)
| Format | top | right | bottom | left | Why |
|---|---|---|---|---|---|
| vertical 9:16 | 11 % | 12 % | 20 % | 6 % | TikTok/Reels buttons on the right, caption + username at the bottom |
| square 1:1 | 6 % | 6 % | 8 % | 6 % | feed cropping |
| portrait 4:5 | 7 % | 6 % | 10 % | 6 % | feed UI |
| landscape 16:9 | 7 % | 5 % | 9 % | 5 % | TV/player overscan, YouTube controls |
QC warns when text leaves the safe area and fails when text touches the frame edge (clipping).

## Animation vocabulary (plan `animation`)
| Value | Look | Use |
|---|---|---|
| `fade` | soft appear/disappear | default, elegant |
| `slide_up` | rises 70 px with ease-out | headlines, outro CTA |
| `slide_side` | enters from the reading side | lists, corporate |
| `zoom` | grows from 86 % to 100 % | titles, prices, logo intro |
| `words` | word-by-word reveal (RTL-correct, layout never jumps) | hooks, quotes |
| `none` | hard cut | fast-paced edits |

## Transitions (plan `transition.type`)
`fade` (default), `slide` (auto direction: RTL → slides right, LTR → slides left), `dissolve`, `fadeblack`,
`fadewhite`, `wipeleft`, `wiperight`, `circleopen`, `zoomin`, `none`. Intro→content and content→outro
always use a gentle fade.

## Composition
- One focal text per moment; never stack more than 2 text blocks plus captions.
- Captions at the bottom; scene texts positioned `lower` are lifted automatically above burned captions;
  lower thirds too. Headlines: `upper` when the subject is centred, `center` on plain backgrounds.
- Contrast: white text with soft shadow on footage; use `style.box` (e.g. `"rgba(0,0,0,.55)"`) on busy shots.
- Brand colour usage: backgrounds of title cards (gradient primary→secondary), lower-third bars, CTA pill
  (accent colour). Keep 60-30-10: neutral/footage 60 %, primary 30 %, accent 10 %.
- Logos: intro centred up to 42 % width; watermark ≤ 16 % width at the top corner opposite the reading
  start (top-left for Arabic, top-right for English), 85 % opacity, hidden during intro/outro.

## Motion presets by style (Creator mode shortcuts)
- elegant: fade 0.6 s transitions, fade/zoom texts, title backgrounds gradient, music low (0.15).
- energetic: slide 0.3 s, words/slide_up, sfx on, scenes 1.5–2 s.
- minimal: fade or none, fade texts, solid backgrounds, no sfx.
- bold: fadeblack, zoom texts, accent-coloured `style.box`, scenes 1–2 s.
