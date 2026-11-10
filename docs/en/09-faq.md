[← Back to the guide index](00-index.md)

# 09 · Frequently asked questions

---

### 1. How much does it cost?

URM Creator Studio itself is **free**. The extra tools it uses (Python, FFmpeg, the bundled fonts and
the optional speech-to-text) are free too. What you do need is access to **Claude Code**, through a
Claude subscription that includes it or an Anthropic API account. Check current plans at
**claude.com/pricing**.

### 2. Who is URM ENROLL, and why is this free?

URM ENROLL shares URM Creator Studio for free with its social-media followers. The studio is built so
that **your videos carry your brand only** — URM ENROLL's name or logo is never added to them, and the
quality check actually fails a video if it finds it there.

### 3. Do I need any AI or video-editing experience?

No. In the default Beginner mode the assistant asks one simple question at a time, avoids jargon, and
always shows you a plan and a test version before making the final video.

### 4. Is my content private?

The video work happens **on your computer**. The studio's engine does not upload your photos, videos or
music anywhere, and speech-to-text (if installed) also runs locally. Keep in mind that Claude Code itself
is an online AI assistant: what you type in the chat, and anything you share or ask it to look at
(for example the preview frames it checks), is processed by Claude as part of the conversation.

### 5. Will it post my videos to Instagram or TikTok?

**No, never.** The studio does not upload, post, schedule or send videos, and never logs into your
social media accounts. It tells you where the finished file is, and you publish it yourself.

### 6. Can it create AI people, avatars or a copy of my voice?

No. The studio works with **real footage** and does not generate synthetic people, change someone's face
or body, create lip-sync or face swaps, or clone voices. If you ask for something in this area, the
assistant explains the concerns and needs your explicit confirmation that you have the person's informed
consent and that the use is lawful and not misleading — and even then it will never impersonate a real
person. On a Mac it can, with your explicit approval for that video, create a plain computer-voice
narration using macOS's built-in voices; it tells you it's a computer voice so you can label it if your
platform requires.

### 7. Can I use any song I like?

Only music you **own or are licensed to use**: music bought with business rights, a composer's
permission, or a free library such as the YouTube Audio Library under its terms. Songs from streaming
apps aren't licensed for business videos. The assistant never downloads music for you.

### 8. Does it work offline?

Partly. The video engine, fonts and speech-to-text all run on your computer. But Claude Code — the
assistant you chat with — needs an internet connection to work. You also need internet to install
everything the first time.

### 9. Does it work on Windows?

It is designed to: there is a Windows installer (`Install-Windows-English.bat`), but it has **not yet been
tested on a real Windows machine**, so treat Windows as early/unverified and please report any problem. Microsoft Edge (already on most
Windows computers) is used to draw text. The only feature that is Mac-only is the optional built-in
computer voice.

### 10. How long does a video take?

A short social video usually takes a minute or two to put together; long videos and older computers take
longer. The quick preview is much faster than the final video, and later renders are faster because
text is cached.

### 11. Can I edit a video later?

Yes. Your projects stay in your workspace. Come back any time and say, for example, "open my Loop ad
project and change the price to $25". Every change creates a new version — earlier versions are kept.

### 12. Can I make videos for clients or several businesses?

Yes. You can keep as many brand profiles as you like. The assistant confirms which brand each project
uses and never mixes them. Remember that the client's logo, fonts and music must be properly licensed
for their use.

### 13. Can I make Arabic videos if I don't speak Arabic?

The studio draws Arabic correctly (connected letters, right-to-left order) and checks it in frames
taken from your video. But it can't know your audience as well as you do — have an Arabic speaker read
the final text before posting. See [Arabic typography](06-arabic-typography.md).

### 14. Will my original files be changed?

Never. The studio copies your files into the project and only works on the copies. It even checks after
every render that no original changed.

### 15. Which video shapes can I make?

Tall 9:16 (Reels, TikTok, Shorts), square 1:1, portrait 4:5 and wide 16:9 (YouTube). You can get the
same video in several shapes — just ask. See [Video guide](05-video-guide.md).

### 16. Does it include advanced motion-design tools like Remotion?

No. Remotion is **not included**. The studio has its own built-in animations (fades, slides, zooms,
word-by-word reveals, transitions, name banners, intros and outros). Everything is rendered locally on
your computer — there is no cloud rendering.

### 17. What are the licence and terms of use?

See the `LICENSE` and `USAGE-TERMS.md` files at the top of the package. The bundled fonts are under the
SIL Open Font License; their licence files are in the studio's `fonts` folder.

### 18. How do I update to a new version?

Unzip the new package and run its installer again. Your previous studio copy is kept as a backup
(`urm-creator-studio.backup-<date-time>` in the skills folder), and your brands, projects and videos are
untouched. Restart Claude Code afterwards.

### 19. How do I uninstall?

1. Quit Claude Code.
2. Delete the studio folder:
   - Mac/Linux: `~/.claude/skills/urm-creator-studio`
   - Windows: `%USERPROFILE%\.claude\skills\urm-creator-studio`
   Also delete any `urm-creator-studio.backup-…` folders next to it if you like.
3. Your **workspace folder** `URM-Creator-Studio` (brands, projects, videos) is **not** removed. Keep it
   to preserve your work, or delete it yourself if you no longer need it.

FFmpeg, Python and Chrome/Edge are separate programs; uninstall them the normal way if you want.

### 20. Where do I find my videos?

In your home folder: `URM-Creator-Studio/projects/<project name>/output/` — each version in its own
folder (`v001`, `v002`, …). The assistant tells you the exact folder each time.

---

[← Examples](08-examples.md) · [Back to the guide index](00-index.md)
