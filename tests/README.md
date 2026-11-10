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

Beginner onboarding conversations (scenarios 1 and 2 in full) were tested as simulated sessions: an agent
followed the skill exactly against a scripted persona and ran the real engine. Reports are in `onboarding/`.
Real-user testing with members of the target audience is still recommended before a wide launch.
