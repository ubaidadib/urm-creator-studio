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

## Visual inspection (you, every time)
1. Read `QC_REPORT.md`.
2. Open `qc/text_frames.png` (Read tool). Apply the Arabic checklist in `arabic-typography.md`.
3. Open `qc/overview.png`: framing (heads not cut), no black frames, colours natural, logo visible.
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
