# Troubleshooting (for you; explain fixes to the user in their language, one step at a time)

Always ask before installing software. Explain what it is, that it is free, and roughly how long it takes.

| Symptom / error | Plain explanation | Fix |
|---|---|---|
| macOS: "cannot be opened because it is from an unidentified developer" (installer) | «ماك يحمي جهازك من الملفات المنزّلة» | Right-click the `.command` file → Open → Open. On newer macOS: System Settings › Privacy & Security › scroll down › "Open Anyway", then double-click again. |
| doctor: FFmpeg missing (macOS) | «محرّك الفيديو غير مثبّت» | Homebrew installed? `brew --version`. If yes: `brew install ffmpeg`. If no: guide to https://brew.sh (copy one line into Terminal, enter Mac password — they type it, you never see it), then `brew install ffmpeg`. |
| FFmpeg missing (Windows) | same | `winget install --id Gyan.FFmpeg -e` in PowerShell, then reopen the terminal. If winget missing: download "release essentials" zip from gyan.dev, extract to `C:\ffmpeg`, add `C:\ffmpeg\bin` to PATH (walk them through). |
| FFmpeg missing (Linux) | same | `sudo apt install ffmpeg` (or distro equivalent). |
| doctor: browser missing | «نحتاج متصفحًا لرسم الحروف العربية» | Install Google Chrome. Or point to another Chromium browser: env `URM_BROWSER=/path/to/browser`. |
| `no_browser` during render | same | as above |
| fonts missing | «ملفات الخطوط ناقصة» | Re-install the package (the `fonts/` folder must be next to SKILL.md). |
| `python3` not found (macOS) | «بايثون غير موجود» | Run `xcode-select --install` (Apple's free developer tools include Python) or install from python.org. |
| `python` not found (Windows) | same | `winget install Python.Python.3.12`; use `py` to run scripts. |
| render very slow | «الجهاز يعمل بجد» | Use `--preview` first; shorten long clips; close other apps. Text cards are cached after the first render. |
| `bad_plan … file not found` | «لم أجد أحد الملفات» | `project show <slug>` → media list; fix `src` paths (relative to the project). |
| QC FAIL text clipped | «نص مقصوص» | Shorten text, add `\n`, change position, or smaller role (subtitle). |
| QC FAIL originals changed | serious — stop | Do not continue; tell the user; check what else touched the file (another app syncing?). |
| QC FAIL brand isolation | serious — stop | Wrong brand in plan/project; fix `brand` and re-render. |
| Arabic shows boxes ☐ or disconnected letters | font lacks Arabic | Switch to a bundled Arabic font; verify with `card`. |
| colours washed out (iPhone HDR) | «تصوير HDR» | Ask the user to export the clip as SDR or turn off HDR video (Settings › Camera › Formats › HDR Video) for future recordings. QC warns about HDR sources. |
| Video has no sound | | Check `inspect`: clip has no audio, or `volume: 0`, or `original_volume: 0`. |
| Music too loud | | Lower `audio.music.volume` (0.12–0.18) and keep `duck: true`. |
| transcription missing | «ميزة تحويل الكلام غير مثبتة» | macOS: `brew install whisper-cpp`, then download `ggml-large-v3-turbo.bin` (~1.6 GB) from the official whisper.cpp model page on Hugging Face into `~/URM-Creator-Studio/models/`. Or set `URM_WHISPER_MODEL`. Ask first; show size. |
| transcription poor | | Background noise or music; ask for clean audio or the script. Never fill gaps by guessing. |
| Windows paths with Arabic names | | Supported; if a tool fails, move the project to a folder without special characters. |
| "Permission denied" writing | | The workspace is in the user's home folder; check disk space and that the folder isn't read-only (cloud-sync placeholders). |
| Out of disk space | | Delete `projects/*/work/` folders (ask first) and old versions the user no longer needs. |

When a command fails, read its message (`--json` gives `error`, `message`, `detail`) and the version's
`render.log`. Translate the cause; never paste raw logs to beginners.
