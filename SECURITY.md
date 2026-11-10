# Security policy / سياسة الأمان

## Supported versions
| Version | Supported |
|---|---|
| 1.0.x | ✅ |

## Reporting a vulnerability
Please **do not** open a public issue for security problems. Use GitHub's private
[security advisory form](https://github.com/ubaidadib/urm-creator-studio/security/advisories/new) for this
repository. We aim to acknowledge reports within 7 days.

<div dir="rtl" lang="ar">

للإبلاغ عن مشكلة أمنية، لا تفتح بلاغًا عامًا. استخدم نموذج الإبلاغ الخاص في GitHub (الرابط أعلاه)، وسنرد خلال 7 أيام تقريبًا.

</div>

## Security model (what the software does and doesn't do)
- The engine runs locally. It makes **no network requests** and never uploads media.
- It invokes FFmpeg, ffprobe, a local Chromium browser (headless, with a temporary profile) and, optionally,
  whisper.cpp and the macOS `say` command, always with argument lists and never through a shell.
- Text cards are local HTML files rendered from your own text; they load only bundled or brand fonts from disk.
- User media is copied read-only into the project; renders never write over source files.
- The installers copy files into `~/.claude/skills` and ask before installing third-party software
  (FFmpeg/Python via Homebrew or winget).
- Your conversation with Claude, and any images the assistant opens, are processed by Anthropic under its terms.

## Out of scope
Vulnerabilities in Claude Code, FFmpeg, Chrome/Edge or whisper.cpp should be reported to their maintainers.
