# Changelog

## 1.0.1 — proposed, not yet released
Maintenance release. Fixes one defect; no new features.
- **Fixed: burned-in captions could be missing from the exported video.** With hard cuts (transition "none")
  plus a brand intro, camera footage tagged bt709 (normal phone video) caused FFmpeg to re-initialise its filter
  graph partway through the video, and captions fed as a single image frame were dropped. Captions are now fed as a
  looped still for the whole video, the same way the engine already feeds lower thirds and the watermark.
  The SRT/VTT caption files were always correct.
- Added `tests/regression_captions_hardcut.py`, which checks in real frames (pixels, not exit codes) that English and
  Arabic captions are visible, including the hard-cut + tagged-footage case.
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
