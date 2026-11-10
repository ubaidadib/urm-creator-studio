[← Back to the guide index](00-index.md)

# 07 · Troubleshooting

Most problems are quick to fix, and **the assistant fixes many of them for you**. At the start of
every session it checks your computer; when something is missing it explains the fix in plain words,
one step at a time, and **asks before installing anything**.

> **Your originals are safe.** The studio only ever works on copies of your files. A failed render,
> a crash or a wrong setting never changes your original photos, videos, logo or music. Every export
> goes into a new version folder, so earlier versions are safe too.

The easiest fix for almost anything: **describe the problem to the assistant in your own words.**

---

## Setup problems

| Symptom | What it means | Fix |
|---|---|---|
| Device check says **FFmpeg missing** (Mac) | The video engine isn't installed | If you have Homebrew: run `brew install ffmpeg` in Terminal. If you don't: install Homebrew from brew.sh first (you paste one line into Terminal and type your Mac password yourself), then `brew install ffmpeg`. The assistant can guide you. |
| **FFmpeg missing** (Windows) | Same | In PowerShell: `winget install --id Gyan.FFmpeg -e`, then close and reopen Claude Code. If winget isn't available, the assistant walks you through a manual download. |
| **FFmpeg missing** (Linux) | Same | `sudo apt install ffmpeg` (or your distribution's equivalent). |
| **Browser missing** / "Chrome or Edge was not found" | The studio needs a browser to draw text, especially Arabic | Install Google Chrome from google.com/chrome. Edge, Chromium and Brave also work. |
| **Fonts missing** | The bundled font files weren't copied | Re-install the full package (unzip everything, run the installer again). |
| **Python not found** (Mac) | Python isn't installed | Run `xcode-select --install` in Terminal (Apple's free developer tools), or install from python.org. Then run the installer again. |
| **Python not found** (Windows) | Same | `winget install Python.Python.3.12`, then run the installer again. |
| Installer says **"Studio files not found"** | The installer was moved away from the other files | Unzip the whole package and run the installer from inside the unzipped folder. |
| **Mac blocks the installer** | macOS doesn't recognise the developer | Right-click `Install-macOS.command` → **Open** → **Open**. |
| Claude Code doesn't know the studio | Claude Code was open during installation | Quit Claude Code completely and open it again. |
| **Speech-to-text not installed** | The optional whisper.cpp tool is missing | Optional. On a Mac: `brew install whisper-cpp`, plus a model file (~1.6 GB) placed in `URM-Creator-Studio/models/`. The assistant asks before downloading and shows the size. Or simply type your script instead. |

---

## While making a video

| Symptom | What it means | Fix |
|---|---|---|
| **Rendering is very slow** | Your computer is working hard | Make a quick preview first, shorten long clips, close other apps. Text is cached after the first render, so later renders are faster. |
| "**File not found**" | A file the plan uses is missing | Ask the assistant to check the project's media list and fix the reference. Did you rename or delete a file in the project folder? |
| Quality check: **text cut off** | Some text touches the edge of the frame | The assistant shortens the text, adds a line break, moves it, or uses a smaller size, then re-renders. |
| Arabic shows **boxes ☐ or separated letters** | The font doesn't properly support Arabic | Switch to a bundled Arabic font (Cairo, Tajawal, Noto Kufi, Noto Naskh, Amiri). |
| **Colours look washed out** (iPhone) | The clip was filmed in HDR | Export the clip as SDR, or turn off HDR video for future recordings (Settings › Camera › Formats › HDR Video). |
| **Video has no sound** | The clip has no audio, or its volume was set to zero | Ask the assistant to check the clip and the volume settings. |
| **Music too loud** | Music volume is too high under speech | Ask for quieter music; the assistant lowers it and keeps "ducking" on. |
| **Subtitles are poor** | Background noise or music confuses speech recognition | Provide cleaner audio or type the script. The assistant never fills gaps by guessing. |
| Problems with **Arabic folder or file names** on Windows | Some tools struggle with special characters | Usually supported; if a step fails, move the project to a folder without special characters. |
| "**Permission denied**" | The studio couldn't write to a folder | Check free disk space, and that the workspace isn't a read-only or cloud-only (not downloaded) folder. |
| **Out of disk space** | Projects and versions take space | Delete the `work` folders inside projects and old versions you no longer need. The assistant asks before deleting anything. |

---

## Serious checks (the assistant stops)

Two quality-check failures are treated as serious. The assistant stops and tells you instead of
delivering the video:

| Check | What it means | What happens |
|---|---|---|
| **Original file changed** | One of your source files was modified while the video was being made — usually another app (such as a cloud-sync service) touching it | The assistant stops and helps you find out what changed the file. |
| **Brand isolation** | Another brand's name, handle or files (or URM ENROLL's name) appeared in your video | The assistant corrects the project's brand and renders again. |

---

## Quick self-check

Before asking for help, these four questions solve most problems:

1. **Did you unzip the whole package** and run the installer from inside the unzipped folder?
2. **Did you restart Claude Code** after installing the studio or FFmpeg?
3. **Is there enough free disk space?** About 5 GB is recommended.
4. **Are your files fully downloaded?** Files in cloud folders (iCloud, OneDrive, Google Drive) sometimes
   exist only as placeholders until opened. Copy them into the `inbox` folder first.

---

## Getting more help

- Tell the assistant exactly what you see — for example, "the installer says FFmpeg missing".
  It translates technical errors into plain words and suggests one fix at a time.
- Ask it to **run the device check again** after you install something.
- Re-running the installer is always safe: your brands, projects and videos are kept.

---

[← Arabic typography](06-arabic-typography.md) · Next: [Examples →](08-examples.md)
