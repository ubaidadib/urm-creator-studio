# Test report: URM Creator Studio 1.0.0

Date: 2026-11-10 · Machine: macOS (Apple Silicon), FFmpeg 9.0.2 (Homebrew, built **without** drawtext/libass),
Google Chrome 157, Python 3.9 (system) and 3.9 (Anaconda), whisper.cpp with `ggml-large-v3-turbo`.

## 1. Acceptance suite (final run, all fixes applied)
`python3 tests/run_acceptance.py`. 13 scenarios, **13 PASS, 0 FAIL**, 450 s total. Raw results:
[`evidence/results.json`](evidence/results.json). Frame sheets: [`evidence/frames/`](evidence/frames/).

| # | Scenario | Result | QC notes |
|---|---|---|---|
| 1 | Arabic-speaking beginner: device check in Arabic | PASS | |
| 2 | English-speaking beginner: device check in English | PASS | |
| 3 | Arabic business with Arabic logo: vertical reel, Arabic captions, lower third, music, sfx | PASS | 1 warn: a 2-line title is on screen 2.3 s (minimum 2.8 s). This is the plan's pacing, not an engine fault. |
| 4 | English creator brand: talking clip → local transcription → burned captions | PASS | Transcript matched the speech word for word. |
| 5 | Bilingual brand: square post with Arabic and English text | PASS | 1 warn: quiet original sound (−39 LUFS) was correctly *not* boosted. |
| 6 | Brand without logo: wordmark intro/outro, Arabic-Indic numerals | PASS | "6" was rendered as «٦» per the brand setting. |
| 7 | No brand configured: neutral, no intro/outro, landscape | PASS | |
| 8 | Arabic social video: Arabic speech → transcription → burned captions | PASS | See §3: the draft had 2 word errors that the confidence check did not flag. |
| 9 | English social video exported vertical + square + landscape | PASS | Warn: very short text holds in the test plan (1.3–1.7 s). |
| 10 | English speech with burned Arabic subtitles + .srt/.vtt files | PASS | 1 warn: one cue at 17 characters/second. |
| X1 | Negative test: another brand's handle in a video | PASS | QC **FAIL** with exit code 3, as designed. |
| X2 | Original media unchanged after all renders | PASS | SHA-256 identical for all 10 files. |
| X3 | Cross-recipient leakage scan of every render | PASS | No foreign names, handles or "URM ENROLL" text. |

**Arabic rendering was verified by looking at real exported frames** for every scenario (frame sheets
above). Checked each time: letters joined (including لا/لأ and the ﷲ ligature), shadda and harakat present,
correct right-to-left order, mixed Arabic/English and @handles in the correct order, nothing clipped,
lower thirds above captions.

## 2. Clean installation
The release ZIP was unzipped into an empty folder. `install.sh` was run with `env -i`, an **empty HOME** and
a minimal PATH (system `/usr/bin/python3` 3.9). Results: skill copied to `~/.claude/skills`, workspace created,
device check passed (speech-to-text correctly reported as optional/not installed). A brand was created from an
example profile and a project rendered to `v001`, QC PASS. The release builder's scan found no absolute paths,
secrets, personal e-mails or media outside the allowed set.
**Not tested:** `install.ps1` / `.bat` on real Windows, and Linux.

## 3. Beginner onboarding (simulated sessions)
Two full sessions were run by an agent that followed the skill files strictly and ran the real engine, against
scripted personas. These are **simulations, not real users**. Full transcripts and scorecards:
[`onboarding/arabic-beginner.md`](onboarding/arabic-beginner.md), [`onboarding/english-beginner.md`](onboarding/english-beginner.md).

| | Arabic-only beginner («أم خالد», sweets business) | English beginner ("Maria", yoga, no logo) |
|---|---|---|
| Final video | ✅ produced, Arabic verified in frames | ✅ produced with her corrected subtitles |
| One question per message | PASS | PASS |
| Jargon | FAIL ("PNG", colour codes, English folder names) → **fixed** | PARTIAL (hex codes) → **fixed** |
| Confirmation before rendering | PASS | PASS |
| Originals untouched / brand applied / no URM branding | PASS | PASS |
| Publishing refused | PASS (phone-transfer help missing → **added**) | PASS |
| User turns to first preview | 16 → about 6 avoidable turns removed by the fixes | 12 |

Defects found by these sessions and fixed in this release:
- Word-by-word reveal left a 6-word headline fully readable for about 1 s, and QC sampled a half-revealed frame.
  Now the full text is guaranteed 1.5 s + 0.3 s/word (otherwise the engine falls back to slide-up), QC samples
  after the reveal, and a reading-time check was added.
- A quiet original sound (room tone) was boosted about 25 dB. Now it is kept quiet and QC warns.
- The shrink-to-fit check measured against the full frame, so long unbreakable brand names overflowed the safe area.
- Brand style could not be changed after creation → `brand style`. Logo colours → `brand colors --apply`.
- Users could not see previews or find files → `studio.py open`, plus a friendly `الفيديو-النهائي_*.mp4` /
  `final-video_*.mp4` copy of the newest final in each project.
- Previews used up version numbers → `preview-NNN` folders.
- Onboarding: extract answers from free text, ask the CTA once, English wording for every step, style
  recommendation by business type, no colour codes for beginners, gendered Arabic once known, a WhatsApp-number
  consent question, "will you post it?" wording, phone-transfer help, a rule for text-only changes.
- Platform labels localized in Arabic outros; captions split at sentence boundaries; QC frames in time order.

Other defects found during development and fixed: Chrome took ~6 s per text card (now batched, 8 cards
per launch); quoted font names broke inline styles (tiny taglines and handles); lower thirds collided with
captions and with low scene text; multi-word brand names were split across lines; colour range was tagged full
range (`yuvj420p`); loudness landed ~2 LU off target (now exact −14 LUFS); short silent videos crashed
loudness normalisation (found by the negative test); the transcription draft was written next to the user's
original file.

## 4. Known limitations
1. **Speech recognition can be confidently wrong.** In scenario 8 it wrote «تهوى» for «قهوة» and «وأستمتعوا» for
   «واستمتعوا» with high confidence, and nothing was flagged. Human review of every caption line is mandatory
   and enforced in the skill instructions. The automated test accepted the draft as-is, so the scenario 8
   video contains those errors.
2. **HDR phone footage**: this FFmpeg build has no `zscale`, so HDR clips get a basic colour conversion, not
   true tone-mapping. QC warns and the docs explain how to record SDR.
3. **Windows and Linux installers are untested** on real machines. The engine code is cross-platform
   (standard library only), and Arabic folder names may trip some Windows tools.
4. **Synthetic narration** uses the macOS system voice only (Arabic voice «Majed»). There is no Windows voice.
5. **Remotion is not included.** Advanced motion design is limited to the built-in animations.
6. **Onboarding was validated by simulation only.** A small test with 3–5 real Arabic-speaking first-time users
   is recommended before a wide launch.
7. Claude Code itself requires a paid Claude plan or API account and an internet connection. Only the video
   engine is local.
8. Beat-synced editing, face-aware cropping and automatic silence trimming are not implemented. Framing of
   people in mismatched shapes relies on the blurred-background fit.
