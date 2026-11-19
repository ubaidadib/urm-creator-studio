# Quality control

`render` runs QC automatically (`qc` re-runs it). Results: `output/vNNN/QC_REPORT.md`,
`qc/report.json`, `qc/text_frames.png` (one frame for every text moment), `qc/overview.png`
(8 evenly spaced frames), `thumbnail.jpg`.

## Automatic checks
| Check | Fails / warns when |
|---|---|
| file, resolution, duration | file missing, wrong size, duration differs from plan by > 0.5 s |
| codec | not H.264 / yuv420p (platform compatibility) |
| audio track | missing |
| file plays cleanly | a full decode of every stream reports an error → **FAIL** |
| picture runs to the end | the video stream is shorter than the planned duration (e.g. the last scene was lost) → **FAIL** |
| no black frames | ≥ 0.4 s of (near) pure black inside the video → **FAIL** in creative/mixed, warn in asset-led (fades at the very start/end are fine; dark looks are not black) |
| narration heard to the end | a voice-over is longer than the time left in the video → **FAIL** (lengthen scenes or shorten the narration; never deliver a cut-off voice) |
| no accidental silence | a video with sound goes silent for ≥ 2 s in the middle → warn |
| loudness | outside −16.5…−11.5 LUFS (silent videos pass) |
| text not clipped | any text pixel touches the frame edge → **FAIL** |
| safe area | text outside the safe area → warn |
| text overlap | two texts overlap on screen for > 0.5 s → warn |
| numerals | a text mixes ٠-٩ and 0-9 → warn |
| reading time | a text is fully visible for less than 1 s + 0.25 s per word → warn (aim for 1.5 s + 0.3 s/word) |
| quiet original audio | source sound below −30 LUFS with no music/voice → not boosted, warn |
| originals untouched | any source file changed during the render → **FAIL** |
| brand isolation | another brand's name/handle/asset or URM ENROLL in a recipient video → **FAIL** |
| caption readability | too fast / too short / too long / overlapping / unclear `[؟]` cues → warn |
| HDR footage | HDR clips were converted without full tone-mapping → warn (check colours) |
| picture keeps moving | the picture is completely still for ≥ 2 s → **FAIL** in creative/mixed mode, warn in asset-led; 1.2–2 s → warn |
| not a slideshow | > 50 % of the content is stills without motion design or plain title cards → **FAIL** in creative/mixed mode, warn in asset-led; > 30 % → warn |
| creative structure (creative mode) | fewer than 3 scene types (≥ 15 s), no CTA, no sound, or no on-screen hook in the first 2 s → **FAIL** (mixed: warn) |

Motion-scene texts are checked from the layout the runtime reports (exact boxes), with the same clipping,
safe-area, overlap and reading-time rules. Every render also writes `cover.jpg`, `production.json` (mode,
look, identity, scenes, every asset with origin/provider/licence, deliverables, QC result) and, when there is
no speech, `onscreen_text.srt` (the on-screen words as a subtitle file).

## Visual inspection (you, every time)
1. Read `QC_REPORT.md`.
2. Open `qc/text_frames.png` (Read tool). Apply the Arabic checklist in `arabic-typography.md`.
3. Open `qc/overview.png`: framing (heads not cut), no black frames, colours natural, logo visible.
   Creative-led: does it look professionally designed — one consistent look, varied scenes, clear hierarchy,
   nothing that reads as a slide deck? Check highlighted words are readable and nothing important sits under
   the platform buttons.
4. For anything doubtful, extract a specific frame:
   `ffmpeg -ss <t> -i <video> -frames:v 1 <project>/work/check.png` and look at it.
5. Fix → re-render (new version) → re-inspect. Never deliver a FAIL.

## Reporting to the user
- PASS: one sentence on what you verified («راجعتُ النصوص: متصلة وواضحة، والصوت بمستوى مناسب»).
- WARN: say what and whether it matters, e.g. «النص الأخير قريب من أزرار تيك توك، يمكنني رفعه قليلًا».
- FAIL: do not deliver; explain the problem simply and fix it.
- Mention it is the user's job to watch the video once before posting (only they can judge their message).

## Versions
Each final render is a new folder (v001, v002…); previews go to preview-001, preview-002… so the first final is always v001. Never delete old versions unless the user asks. When the user
says "the previous one was better", point to that folder. The `work/` folder can be deleted to save
space (ask first).
