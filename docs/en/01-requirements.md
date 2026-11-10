[← Back to the guide index](00-index.md)

# 01 · Requirements

Before you install URM Creator Studio, check that your computer has (or can get) the items below.
Don't worry if some are missing — the installer checks your computer and tells you what to add, and the
assistant can walk you through each step later.

---

## At a glance

| Item | Needed? | What it is for | Notes |
|---|---|---|---|
| **Computer** | Required | Runs everything locally | macOS 12 or newer (tested). Windows 10/11 and Linux: designed for, **not yet tested on real machines** |
| **Claude Code** | Required | The assistant you chat with | Needs a Claude subscription that includes Claude Code, or an Anthropic API account |
| **Python 3.8+** | Required | Runs the studio's video engine | Free. Often already installed on Mac and Linux |
| **FFmpeg** | Required | Cuts, joins and exports the video ("the video engine") | Free. The installer offers to install it |
| **Google Chrome or Microsoft Edge** | Required | Draws on-screen text, especially Arabic letters, correctly | Free. Edge normally comes with Windows |
| **whisper.cpp** | Optional | Turns speech into written subtitles, on your computer | Free. Best Arabic model is about 1.6 GB |
| **Free disk space** | Recommended: ~5 GB | Software, fonts, your projects and exports | Video files are large; more space is better |
| **Internet** | For installation only | Downloading Claude Code and the free tools | Video editing itself happens on your computer |

---

## The computer

- **Mac:** macOS 12 (Monterey) or newer. Both Apple Silicon and Intel Macs work.
- **Windows:** Windows 10 or Windows 11. The installer and engine were written for Windows but have **not yet been
  tested on a real Windows machine**; please report problems.
- **Linux:** not yet tested. There is no double-click installer; technical users can run `install.sh` from a terminal.

A recent computer makes rendering faster, but any machine that can play HD video comfortably will work.
Long videos simply take longer to put together.

---

## Claude Code

Claude Code is the AI assistant that runs the studio. You talk to it in plain words; it does the
technical work for you.

To use Claude Code you need **one** of these:

- a **Claude subscription that includes Claude Code**, or
- an **Anthropic API account** (pay-as-you-go).

Plans and prices change, so check the current options at **claude.com/pricing** before you sign up.
URM Creator Studio itself is free — see the [FAQ](09-faq.md).

How to install Claude Code is explained in [Installation](02-installation.md).

---

## Python 3.8 or newer

Python is a free programming language. The studio's engine is written in it. You will never need to
write Python yourself.

- **Mac:** if it is missing, the installer tells you to run `xcode-select --install` (Apple's free
  developer tools, which include Python).
- **Windows:** if it is missing, the installer offers to install it for you using `winget`
  (Windows' built-in app installer). It asks first.
- **Linux:** install `python3` with your system's package manager.

---

## FFmpeg (the video engine)

FFmpeg is a free, widely used program that does the actual cutting, joining and exporting.

- **Mac:** the installer offers to install it with Homebrew (a free tool installer for Mac) if
  Homebrew is already on your Mac. If not, the assistant can guide you through installing Homebrew
  first from brew.sh.
- **Windows:** the installer offers to install it with `winget`.
- **Linux:** for example `sudo apt install ffmpeg` on Ubuntu/Debian.

The installer always **asks before installing** FFmpeg.

---

## Google Chrome or Microsoft Edge

The studio uses your browser quietly in the background to draw every piece of on-screen text. This is
what keeps Arabic letters connected and in the correct right-to-left order (see
[Arabic typography](06-arabic-typography.md)). You don't need to open the browser yourself.

The studio looks for Google Chrome, Microsoft Edge, Chromium or Brave. On Windows, Edge is usually
already installed. On a Mac, install Google Chrome from google.com/chrome if you have neither.

---

## Optional: whisper.cpp (speech-to-text)

If your video has people talking, the studio can write draft subtitles automatically with
**whisper.cpp**, a free speech-recognition program that runs **entirely on your computer** — nothing
is uploaded.

- It is optional. Without it, you can type or paste what is said, and the assistant times the subtitles
  with you.
- The recommended model file (`ggml-large-v3-turbo.bin`) is about **1.6 GB**. The assistant asks before
  downloading anything and explains the size first.

---

## Optional: built-in voice (Mac only)

On a Mac, the studio can create a computer-voice narration using the voices built into macOS — but
only when you explicitly ask for it for that video. This is not available on Windows or Linux.
Your own recorded voice is always the recommended option.

---

## Disk space

Plan for about **5 GB free**:

- the free tools (FFmpeg, and optionally whisper.cpp and its model),
- the bundled fonts,
- your projects — each project keeps copies of your media plus every version you export.

You can free space later by deleting old versions or a project's `work` folder (the assistant asks
before deleting anything).

---

## Internet

You need internet only to **install** Claude Code and the free tools. The video editing itself happens on
your computer. Note that Claude Code, the assistant you chat with, needs an internet connection to
talk to Claude while you work — see the [FAQ](09-faq.md) about offline use.

---

Next: [Installation →](02-installation.md)
