# Tests

All tests use synthetic media (generated gradients, a fractal photo, sine-tone music, macOS system voices)
and fictional brands. No real people, private footage or licensed music is involved.

```bash
# 1. generate test media (≈1 minute)
python3 tests/make_fixtures.py /tmp/urm-fixtures

# 2. run the acceptance suite in an isolated workspace (≈10–15 minutes; renders real videos)
python3 tests/run_acceptance.py --fixtures /tmp/urm-fixtures --out /tmp/urm-acceptance

# run selected scenarios only
python3 tests/run_acceptance.py --fixtures /tmp/urm-fixtures --out /tmp/urm-acc --only 3,5,x1
```

```bash
# 3. creative-led, mixed and audio matrix (≈15 minutes on an 8 GB Mac; C1/C2 render the 30 s acceptance briefs at full size;
#    add --full for ≈25 minutes)
python3 tests/regression_creative_led.py --fixtures /tmp/urm-fixtures --out /tmp/urm-creative
```
Owner acceptance matrix (14 scenarios; C1 and C2 always render at full size, `--full` renders the rest at full size):

| ID | Scenario |
|---|---|
| C1 | asset-free English brief: 30 s language-school promo (no logo, colours, footage, images or music) |
| C2 | asset-free Arabic version of the same brief (RTL, joined letters, Latin levels inside Arabic layout) |
| C2B | Arabic asset-free brief without a business name |
| C3 | mixed: user footage + user photo + AI-registered photo (provenance), no brand, no music |
| C4 | existing brand: real logo + brand colours + footage; motion scenes follow the brand |
| C5 / C5B | slideshow plan FAILS in creative mode / the same slideshow from the user's own assets still delivers (WARN) |
| C6A–C6D | narration over the original score · user music + narration · narration longer than the video must FAIL · no music given → score composed |
| C7 / C7B | export integrity, landscape (cuts + dissolves, short final scene, no black frames, clean decode) / motion-clip cache |
| C8 | stopping a render leaves no helper browsers or temporary folders; the next render still works (run the suite alone) |

Every scenario that writes `production.json` also checks it contains no absolute paths (no user or folder names).

Results: `<out>/RESULTS.md`, `<out>/results.json`, and `<out>/frames/*.png`, one QC frame sheet per scenario.
**Open the frame sheets and look at the Arabic text**; automatic checks can't tell whether letters join.

| ID | Scenario |
|---|---|
| 1 | Device check in Arabic (Arabic-speaking beginner) |
| 2 | Device check in English (English-speaking beginner) |
| 3 | Arabic business with an Arabic logo: vertical reel, Arabic captions, lower third, music, sfx |
| 4 | English creator brand: talking clip, local transcription, burned English captions |
| 5 | Bilingual Arabic-English brand: square post with mixed-direction text |
| 6 | Brand without a logo: typographic wordmark intro/outro, Arabic-Indic numerals |
| 7 | User with no brand configured: neutral style, no intro/outro, landscape |
| 8 | Arabic social video: Arabic speech, local transcription, burned Arabic captions |
| 9 | English social video: product ad exported vertical, square and landscape |
| 10 | Mixed-language video: English speech with burned Arabic subtitles plus .srt/.vtt files |
| X1 | Negative test: QC must FAIL when another brand's handle appears in a video |
| X2 | Original media byte-identical (SHA-256) after all renders |
| X3 | Every render scanned for other recipients' names and handles and for URM ENROLL text |
| X4 | Burned-in English and Arabic captions are **visible in rendered frames** (pixel check, not exit codes), including hard cuts + brand intro + bt709-tagged footage, the case that dropped captions in 1.0.0. Runs `tests/regression_captions_hardcut.py`, which can also be run on its own |

Beginner onboarding conversations (scenarios 1 and 2 in full) were tested as simulated sessions: an agent
followed the skill exactly against a scripted persona and ran the real engine. Reports are in `onboarding/`.
Real-user testing with members of the target audience is still recommended before a wide launch.
