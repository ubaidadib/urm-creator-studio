# Implementation notes: URM Creator Studio 1.0.0

## What was built
| Deliverable | Where |
|---|---|
| Claude Code skill (concise `SKILL.md` + 13 reference files loaded on demand) | `skill/urm-creator-studio/` |
| Arabic-first onboarding, English onboarding, language detection and switch | `SKILL.md` §1–2, `reference/onboarding.md`, `language-ar.md`, `language-en.md` |
| Beginner / Creator / Pro modes | `reference/modes.md`, `studio.py settings --mode` |
| Brand system (profiles, logo or wordmark, colours from logo, style presets, fonts, handles, CTA, watermark, numerals) | `scripts/urmstudio/brand.py`, `reference/brand-system.md` |
| Video engine (scenes, motion, framing, text animation, lower thirds, captions, music ducking, sfx, loudness, 4 formats, versioning) | `scripts/studio.py`, `scripts/urmstudio/render.py` |
| Arabic typography & RTL (Chromium shaping, bidi isolation, numerals, auto-fit, balanced lines) | `scripts/urmstudio/textrender.py`, `reference/arabic-typography.md` |
| Audio & captions (SRT/VTT with RLM, readability checks, local whisper.cpp transcription, consent-gated narration) | `captions.py`, `voice.py`, `reference/audio-captions.md` |
| Quality control (12+ automatic checks plus frame sheets for visual inspection) | `qc.py`, `reference/quality-control.md` |
| Bundled OFL Arabic/Latin fonts (Cairo, Tajawal, Noto Naskh/Kufi Arabic, Amiri, Inter) | `skill/urm-creator-studio/fonts/` |
| Complete Arabic and English documentation (10 docs each, with images) | `docs/ar/`, `docs/en/`, `docs/images/` |
| Examples: 4 fictional brand profiles, briefs in Arabic and English | `examples/` |
| Installers (macOS/Linux, Windows, double-click launchers in Arabic and English) | `install.sh`, `install.ps1`, `Install-*.command/.bat` |
| Tests: synthetic fixtures, 13-scenario acceptance suite, onboarding simulations, report | `tests/` |
| Licence and usage terms (Arabic and English) | `LICENSE` (MIT + OFL notice), `USAGE-TERMS*.md` |
| Release ZIP with portability/secret scan and SHA-256 | `tools/build_release.py` → `dist/` |

## Key design decisions
- **Text is rendered by headless Chrome/Edge, not FFmpeg.** Current Homebrew FFmpeg has no text filters, and
  FFmpeg's text path is unreliable for Arabic anyway. The browser gives HarfBuzz shaping and the Unicode bidi
  algorithm. Cards are full-frame transparent PNGs, so QC can measure every text's bounding box.
- **Standard library only**: Python 3.8+, FFmpeg and a Chromium browser. Nothing else to install.
- **Workspace outside the skill** (`~/URM-Creator-Studio`, or `URM_STUDIO_HOME`). Reinstalling never touches
  user brands or projects, and brands are per-folder, which makes isolation checkable.
- **Never destructive**: media is copied read-only into projects, every render is a new folder, the engine
  refuses to write over sources, and QC fingerprints the sources before and after.
- Distributor branding appears only in documentation and credits, never in recipient renders (QC enforced).

## Test results
See [tests/TEST_REPORT.md](tests/TEST_REPORT.md). Summary: 13/13 acceptance scenarios pass; Arabic was
verified in real exported frames for every scenario; clean install from the ZIP works with the system Python;
two simulated beginner sessions (Arabic and English) produced finished videos, and their 20+ findings were fixed.

## Roadmap / not yet done
- Verification of the Windows and Linux installers on real machines.
- A pilot with real first-time Arabic-speaking users (the onboarding tests so far are simulations).
- Proper HDR tone-mapping (requires an FFmpeg build with `zscale`).
- Narration voices outside macOS.
