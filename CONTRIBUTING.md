# Contributing

Thank you for helping! Issues and pull requests in **Arabic or English** are welcome.

## Most useful right now
- **Windows and Linux reports.** Did the installer and a first render work? Please share your OS version, Python
  version, the output of `python3 ~/.claude/skills/urm-creator-studio/scripts/studio.py doctor`, and any error.
- **Arabic rendering problems.** Attach a screenshot of the frame and the exact text you used.
- **Wording.** Arabic or English phrasing in the onboarding that confused a beginner.

## Ground rules
- Never include real people's footage, private media, secrets or personal data in issues, tests or PRs.
  Use the synthetic generator in `tests/make_fixtures.py`.
- Keep the engine dependency-free (Python standard library, FFmpeg, a Chromium browser).
- Arabic text must always go through the browser renderer (`textrender.py`). Never use FFmpeg drawtext for Arabic.
- Don't add features that generate synthetic people, clone voices or post to social networks.
- Recipient videos must never contain distributor (URM ENROLL) branding.

## Development
```bash
python3 tests/make_fixtures.py /tmp/urm-fixtures
python3 tests/run_acceptance.py --fixtures /tmp/urm-fixtures --out /tmp/urm-acceptance
```
Open the frame sheets in `/tmp/urm-acceptance/frames/` and check the Arabic text by eye; automatic checks can't
judge letter joining. Build the release ZIP with `python3 tools/build_release.py`. It refuses to package
absolute paths, secrets or private media.

## Pull requests
Describe what changed and why, how you tested it (including frame screenshots for anything visual), and update
both `docs/en` and `docs/ar` when user-facing behaviour changes.
