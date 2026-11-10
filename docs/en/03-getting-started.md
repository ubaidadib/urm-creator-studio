[← Back to the guide index](00-index.md)

# 03 · Getting started

This guide walks you through your first video: how to start, what the assistant will ask, where to
put your files, and where the finished video appears.

---

## Start a conversation

Open Claude Code and type either of these:

```
Hi, I want to make a video
```

```
/urm-creator-studio
```

Plain words are enough. Anything about making, editing, captioning or branding a video also starts the
studio — for example "Can you add subtitles to my interview?".

At the start of every session the assistant quietly checks your computer. If something is missing,
it stops and helps you fix it first, step by step, asking before installing anything.

---

## Choosing your language

The studio is Arabic-first. The first time, the assistant may greet you in Arabic with this switch:

> 🌐 العربية | English

Just reply in English (or type "English") and it will switch and remember your choice. You can change
language any time — simply write in the other language or ask: "Please answer in Arabic."

Your chat language and your video language are separate. You can chat in English and make a video
with Arabic text, or the other way round.

---

## One question at a time

In the default mode the assistant asks **one simple question per message**, with numbered choices.
The recommended option is listed first and marked ⭐. You can:

- type just the **number**,
- answer in your own words, or
- say **"Not sure — choose for me"** and it will pick sensible defaults.

A typical first conversation goes like this:

1. **What video?** (social media short, ad, company intro, product, educational, event, personal, other)
2. **Which brand?** Set one up quickly, continue without a brand, or use a saved one.
3. **Where will it be posted?** This decides the shape (tall, square or wide).
4. **Your materials:** photos, clips, logo, music you have the right to use.
5. **Your main message and call-to-action** ("What should viewers do at the end?").
6. **The plan:** a short numbered list of scenes with the exact on-screen texts. You approve or ask for changes.
7. **Preview → final.**

---

## Modes: Beginner, Creator, Pro

You can switch mode any time by saying so ("switch to creator mode", "pro mode", "make it simpler").

| Mode | Best for | What changes |
|---|---|---|
| **Beginner** (default) | First-timers | One question per message, numbered choices, no jargon. Always: plan → approval → preview → approval → final. |
| **Creator** | People who want more say | Choose style, caption look, text animations, transitions, music volume and sound effects. The plan is shown as a table. Up to 3 related questions per message. |
| **Pro** | Experienced editors | Full control: direct edits to the project's plan file, frame-accurate trims, speed changes, smoothness (fps), quality, framing, loudness target, custom styles and fonts. |

---

## Where to put your files

You have two options:

**Option A — the inbox folder (recommended for many or large files).**
In your home folder there is a folder called **`URM-Creator-Studio`**. Inside it is **`inbox`**.
Copy your photos, videos, logo and music there, then tell the assistant "I've added my files".

- Mac: open Finder → **Go** menu → **Home** → `URM-Creator-Studio` → `inbox`
- Windows: open File Explorer → your user folder (e.g. `C:\Users\YourName`) → `URM-Creator-Studio` → `inbox`

**Option B — drag into the chat.** Drag files straight into the Claude Code window.

Supported files include common video (MP4, MOV, M4V, MKV, WEBM, AVI…), photos (JPG, PNG, WEBP, HEIC…)
and audio (MP3, WAV, M4A, AAC…).

The assistant **copies** your files into the project. Your originals are never changed, moved or renamed.

Next, it looks at your footage (it makes small overview images of each clip) and tells you in a
sentence or two what it saw — and honestly says if a clip is too dark, shaky or short.

---

## Preview first, then the final video

1. After you approve the plan, the assistant makes a **quick test version (preview)** — smaller and
   faster to produce.
2. It checks the result itself, including pictures taken from the video to make sure text is readable,
   not cut off and (for Arabic) correctly joined.
3. You watch it and say what to change. Repeat as often as you like.
4. When you're happy, it makes the **final video** in full quality and checks it again.

Putting a video together usually takes a minute or two for a short social video; longer videos and
slower computers take longer.

---

## Where your finished video is

Every project has its own folder inside the workspace:

The easiest way: inside each project folder there's a file called `final-video_<shape>.mp4` (or
`الفيديو-النهائي_…` for Arabic projects). It is always the newest final version, and the assistant opens the
folder on your screen for you.

```
URM-Creator-Studio/
  inbox/                 ← drop your files here
  brands/                ← your saved brand profiles
  projects/
    <project name>/
      media/             ← copies of your files
      output/
        preview-001/     ← quick test versions (smaller, faster)
        v001/            ← first final version
        v002/            ← next version, and so on
```

Inside each version folder you'll find:

- **the video** (an `.mp4` file that plays everywhere),
- `thumbnail.jpg` — a still picture you can use as a cover,
- `captions.srt` / `captions.vtt` — subtitle files, if the video has captions,
- `QC_REPORT.md` and a `qc` folder — the automatic quality check.

The assistant tells you the folder in plain words when the video is ready. Older versions are always
kept, so "the previous one was better" is never a problem.

---

## A short sample conversation

> **You:** Hi, I want to make a video
>
> **Assistant:** Welcome to URM Creator Studio 🎬 … 🌐 العربية | English … What would you like to make today?
> 1. Short social media video (Reels, TikTok, Shorts) …
>
> **You:** 1
>
> **Assistant:** Great choice. Shall we set up your brand first? 1. Quick brand setup (2 minutes) ⭐ recommended
> 2. Continue without a brand for now 3. I have a brand file ready
>
> **You:** 2
>
> **Assistant:** Where will you post it? 1. Instagram Reels / TikTok / YouTube Shorts ⭐ …
>
> **You:** TikTok
>
> **Assistant:** Please put your clips in the **inbox** folder inside **URM-Creator-Studio** in your home folder, or drag them here. Tell me when you're done.
>
> **You:** Done, 4 clips.
>
> **Assistant:** I looked at your 4 clips: a kitchen, hands kneading dough, a finished loaf and a smiling customer. Here's my plan: … Shall I make a quick test version?
>
> **You:** Yes
>
> **Assistant:** ✅ The test version is ready (0:20, tall for TikTok). I checked the texts: clear and nothing cut off. Anything to change?

---

## Good to know

- The assistant **never publishes** anything. You upload the video yourself.
- You can come back days later: say "open my bakery project" and continue.
- Want the same video as a square post too? Just ask — see [Video guide](05-video-guide.md).

---

[← Installation](02-installation.md) · Next: [Brand guide →](04-brand-guide.md)
