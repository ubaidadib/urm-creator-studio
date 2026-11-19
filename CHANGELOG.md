# Changelog

## 1.1.0 — 2026-11-19: creative-led production
Core capability: an ordinary user can start with an idea and finish with a professionally designed video,
even with no logo, brand colours, footage, images or music.
- **Two production modes.** Asset-led (unchanged) and creative-led; mixed productions combine both. The skill
  chooses the mode from what the user has (`reference/creative-production.md`).
- **Motion design engine** (`motion/runtime.js`, `scripts/urmstudio/motion.py`): new `motion` scene kind with 11
  templates (kinetic title, word cloud, globe, features, stats, journey, contrast, quote, showcase, CTA, logo
  reveal), kinetic typography with correct Arabic shaping, a continuous animated background world, simulated
  camera moves, designed transitions (swap, slide, colour panels, iris) that hide every cut, film grain and
  vignette. Rendered frame by frame in headless Chromium on 127.0.0.1 and piped into FFmpeg; standard library
  only, nothing uploaded. Clips are cached per scene.
- **Looks and temporary identity** (`looks.py`): 8 visual looks for unbranded videos, brand-derived looks for
  branded ones, and a monogram placeholder mark when there is no logo (clearly marked temporary).
- **Original soundtrack** (`motion/score.js`): `audio.score` composes music for the edit (6 moods) with sound
  design synced to on-screen events; generated locally, no licence needed.
- **Provenance**: `asset register` records user / AI-generated / stock / engine origin with provider and licence;
  every render writes `production.json`. The engine never claims third-party or generated media as its own.
- **New deliverables**: `cover.jpg`, `onscreen_text.srt` (on-screen words as subtitles when there is no speech).
- **Creative QC gates**: picture keeps moving (freezedetect), not a slideshow (still-content share), complete
  creative structure (≥ 3 scene types, hook in 2 s, sound, CTA). Fail in creative mode, warn in asset-led mode,
  so existing asset-led videos (e.g. a personal photo album) still deliver.
- Per-boundary transitions in the joiner (motion↔motion cuts, footage dissolves, gentle intro/outro).
- **Export and audio integrity checks** (all modes): the file must decode cleanly; the picture must run to the
  end (a mixed-mode bug that dropped the last scene's picture was found and fixed); no black frames inside the
  video; a voice-over that runs past the end FAILS instead of being cut off silently; silence of 2 s or more in
  the middle of a video with sound is flagged.
- **No accidental silence**: a creative or mixed production without music gets an original score automatically
  (`"score": false` opts out).
- **Mixed productions look like one film**: footage or photos that don't fill the frame sit on a blurred
  surround tinted with the look's stage colour (asset-led framing is unchanged).
- Visual fixes from frame-by-frame review: greeting words no longer cut off at the frame edge, larger
  kicker/subtitle text on vertical videos, shorter scene-to-scene hand-over (no near-empty beat).
- Resource use: at most 2 headless browsers render motion scenes at once on machines with 8 GB RAM or less
  (`URM_MOTION_WORKERS` overrides); browsers and temporary folders are always cleaned up.
- `tests/regression_creative_led.py`: owner acceptance matrix C1–C8 (14 scenarios): English and Arabic
  asset-free briefs, mixed, existing brand, slideshow rejection, four narration/music cases, export integrity.

## 1.0.1 — 2026-11-16
Maintenance release. Fixes one defect; no new features.
- **Fixed: burned-in captions could be missing from the exported video.** With hard cuts (transition "none")
  plus a brand intro, camera footage tagged bt709 (normal phone video) caused FFmpeg to re-initialise its filter
  graph partway through the video, and captions fed as a single image frame were dropped. Captions are now fed as a
  looped still for the whole video, the same way the engine already feeds lower thirds and the watermark.
  The SRT/VTT caption files were always correct.
- Added `tests/regression_captions_hardcut.py`, which checks in real frames (pixels, not exit codes) that English and
  Arabic captions are visible, including the hard-cut + tagged-footage case. It runs as acceptance scenario X4.
- Final pass is slower when captions are burned in, because each caption image is now fed for the whole video
  (measured on a 31 s Reel with 9 captions, 1080x1920, FFmpeg 9.0.2, 8 GB Mac: 90 s → 115 s, +28%;
  videos without burned-in captions are unaffected).
- Skill rule: the assistant must never edit the installed engine during a user's session; it reports problems
  instead.

## 1.0.0 — 2026-11-10
First public release.
- Documentation states verified platforms honestly (tested on macOS; Windows/Linux not yet verified).
- Added CONTRIBUTING.md, SECURITY.md and bilingual release notes; recipient ZIP ships with a SHA-256 checksum.
- Arabic-first conversational onboarding with Beginner, Creator and Pro modes; English supported.
- Brand profiles (logo or typographic wordmark, colours, fonts, handles, intro/outro, watermark, numerals).
- Video engine: FFmpeg + headless Chromium text rendering for correct Arabic shaping and RTL/mixed text.
- Scene types (video, image with motion, title cards), animated text (fade, slide, zoom, word-by-word),
  lower thirds, burned-in captions + SRT/VTT, music with ducking, transition whooshes, loudness to −14 LUFS.
- Vertical, portrait, square and landscape exports; versioned outputs; originals never modified.
- Automatic QC (clipping, safe areas, overlaps, numerals, loudness, codec, originals, brand isolation) plus
  frame sheets for visual inspection.
- Local speech-to-text via whisper.cpp (optional), macOS system-voice narration with explicit consent.
- Bundled OFL fonts: Cairo, Tajawal, Noto Naskh Arabic, Noto Kufi Arabic, Amiri, Inter.
- Complete Arabic and English documentation, examples, installers for macOS/Linux/Windows.
