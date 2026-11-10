# Onboarding test: English beginner ("Maria", Calm Corner Yoga)

- Date: 2026-11-10, 13:53–14:00 CET
- Skill under test: `skill/urm-creator-studio` (SKILL.md + reference/*.md + scripts/studio.py)
- Workspace: `URM_STUDIO_HOME=<test-scratch>/onboard-en` (fresh, empty; `~/URM-Creator-Studio` was not touched)
- Inputs: `fx/speech_en.mp4` (5.9 s vertical talking clip) and `fx/photo_landscape.jpg`, copied into `inbox/`. No logo. The fixture SHA-1s were the same before and after the test.
- Method: one tester played both roles, the assistant following the skill strictly and the user persona. Every engine command was actually run.

> **Validity caveat:** the skill was edited while this test was running. `scripts/urmstudio/render.py` and `project.py` changed at 13:55:30, and `audio-captions.md`, `language-ar.md`, `plan-reference.md` and `quality-control.md` changed between 13:54 and 13:55. I read the references at about 13:53. The first preview was rendered at 13:55:58 by the older engine and went to `output/v001`. Later previews went to `output/preview-NNN`. Because of this the final landed in `v002` instead of `v001` (see Problem 1).

---

## 1. Transcript

Each turn shows what the user sees. Commands are listed under **Behind the scenes** and were not shown to the user.

**Behind the scenes (before A1):** `studio.py --json doctor` returned ready=true, with whisper and voice available (the item texts were Arabic only). `settings` showed no language and no brand. `brand list` returned `[]`, so this is a first-time user and the skill routes to `onboarding.md`.

**A1 (assistant), Arabic welcome template from `language-ar.md`, verbatim:**
> أهلًا بك في **استوديو URM للإبداع** 🎬
> أنا مساعدك في صناعة الفيديو، وسأساعدك خطوة بخطوة حتى لو كانت هذه أول مرة لك. …
>
> 🌐 العربية | English
>
> ما نوع الفيديو الذي تريد صنعه اليوم؟
> 1. فيديو قصير للسوشيال ميديا (ريلز، تيك توك، شورتس) … 8. فكرة أخرى
>
> اكتب الرقم فقط، أو صف فكرتك بكلماتك.

**U1 (Maria):** hi sorry i can't read this 😅 english? i want to make a reel for my yoga instagram, with subtitles of what i say

**Behind the scenes:** `studio.py --json settings --language en`

**A2:**
> No problem, we'll continue in English 🌐 (you can switch back any time: العربية | English).
> A short Instagram Reel with subtitles of what you say. Great! I'll make it tall, like a phone screen.
> First, your brand. This means your saved name, colours and Instagram handle, so every video looks like you. Which would you like?
> 1. Quick brand setup (about 2 minutes) ⭐ recommended
> 2. Continue without a brand for now
> 3. I already have a brand file
> 4. Not sure, choose for me

**U2:** 1 i guess. it's called Calm Corner Yoga. i don't have a logo though

**A3:**
> Lovely name ✅ Not having a logo is no problem. I'll write "Calm Corner Yoga" in a nice font at the start and end of your video instead. If you get a logo later, just send it and I'll add it.
> What style feels most like you?
> 1. Modern: clean and fresh ⭐ recommended
> 2. Luxury: elegant and calm
> 3. Playful: fun and colourful
> 4. Corporate: serious and trustworthy
> 5. Minimal: simple, lots of space
> 6. Bold: loud and eye-catching
> 7. Not sure, choose for me

**U3:** no idea honestly 😅 you choose

**Behind the scenes:** `brand new --name-en "Calm Corner Yoga" --style modern` created slug `calm-corner-yoga`. The default colours are blue #1E3A8A, sky #0EA5E9 and yellow #FACC15.

**A4:**
> Modern it is ✅
> Do you have specific colours for your business? You can send a colour code (like #1E3A8A) or a picture of your designs, or just say "choose for me".

**U4:** no idea about colours either lol. choose for me

**A5:**
> Done. I'll use the Modern colours 🎨
> Which social media accounts should appear at the end of your videos? Only the ones you use, for example Instagram @yourname.

**U5:** just instagram, @calmcorner.yoga

**A6:**
> Got it ✅ What would you like viewers to do at the end of the video?
> 1. Follow you for more ⭐ recommended
> 2. Book a class
> 3. Send you a message
> 4. Something else

**U6:** 1. follow for more yoga tips

**Behind the scenes:** `brand set calm-corner-yoga handles.instagram "@calmcorner.yoga"`, `brand set … outro.cta.en "Follow for more yoga tips"`, `brand check` (returned []), `brand preview`, `settings --brand calm-corner-yoga`. I read `preview/intro.png` and `preview/outro.png`.

**A7:**
> Here's how the start and end of your videos will look:
> • Start: "Calm Corner Yoga" in white letters on a blue background
> • End: your name, a yellow button saying "Follow for more yoga tips", and "Instagram @calmcorner.yoga" underneath
> Do you like the look?

**U7:** its fine! very blue haha but ok

*(Onboarding Step 4, "where will it be posted?", was skipped because she already said Instagram Reels.)*

**A8:**
> Great 📁 Now your materials. Please put your video and photos in the **inbox** folder inside the "URM-Creator-Studio" folder in your account, or drag them into this chat. Tell me when you're done.

**U8:** ok done. i put a video of me talking and a photo

**Behind the scenes:** `home`, `project new "Calm Corner Reel" --brand calm-corner-yoga --format vertical --language en --type social`, `project add calm-corner-reel <inbox>` (made read-only copies), `inspect media/* --sheet work/sheets`. I read both contact sheets. The video is a 5.9 s vertical clip with audio at −16.7 LUFS and no cuts, but the frames show only a dark blue-grey gradient. The photo shows a colourful pink and green fractal.

**A9:**
> I've got both ✅ Your video is about 6 seconds long, filmed tall, and the sound is clear.
> To be honest, in the picture I can only see a dark blue-grey background. I can't make out a person. The photo is a very colourful pink-and-green pattern.
> Is that the right video of you?

**U9:** yes thats me lol the light was bad. the photo is a poster from my studio

**A10:**
> Thanks! What's the one thing you want viewers to take away? For example "yoga can be easy for beginners" or "new class on Mondays".

**U10:** that yoga can be calm and easy, even for beginners

**A11:**
> Here's the plan for your Reel (tall, about 13 seconds):
> 1. Start (2 s): "Calm Corner Yoga" on your blue background
> 2. Your video (6 s): "New to yoga?" at the top, with subtitles of what you say at the bottom
> 3. Your studio photo (3 s), slowly zooming in: "Calm, easy yoga for beginners"
> 4. End (3 s): "Calm Corner Yoga", the button "Follow for more yoga tips", and Instagram @calmcorner.yoga
>
> No music. Subtitles: yes. I'll first turn your speech into written text and show it to you before anything is written into the video.
> Before I start:
> • I'll put together a quick test version (smaller, faster)
> • your original files stay unchanged
> Shall I start?

**U11:** wait is this going to post it for me?

**A12:**
> No. I never post anything for you. I make the video file and tell you where it is, and you upload it to Instagram yourself whenever you're ready.
> Shall I start the quick test version?

**U12:** ok yes go

**Behind the scenes:**
- Wrote `plan.json` with no captions: a video scene with the "New to yoga?" words animation, an image scene with zoom_in and slide_up text, brand intro and outro.
- `render calm-corner-reel --preview` produced `output/v001` (old engine) in 30.5 s with QC **WARN**. The warning was "Text clear of app buttons — intro @1.05s".
- Read `QC_REPORT.md`, `qc/text_frames.png` and `qc/overview.png`.
- What the frames showed: the intro wordmark runs almost edge to edge; "New to yoga?" sits at the top; the photo headline is readable but sits on a very busy background; the outro is correct.
- `transcribe calm-corner-reel --language en` took 10.8 s and returned 2 segments with 0 flagged. Lowest word confidence was 0.6 for segment 1 and 0.5 for segment 2.

**A13:**
> The quick test version is ready ⏱ about 13 seconds. I checked the text: nothing is cut off and it's readable. One small note: your name at the very start is quite wide and comes close to where Instagram puts its buttons on the right. It's still fully visible.
> You can watch it in: URM-Creator-Studio → projects → calm-corner-reel → output → v001.
>
> Next, the subtitles. I turned your speech into written text. Please check it, because the computer sometimes mishears words:
> 1. "Hi everyone, welcome back to the channel. Today I will show"
> 2. "you 3 simple tips to stay focused."
> Is every word right? If not, just tell me what to change.

**U13:** its "welcome back to the page" not channel. rest is right

**Behind the scenes:**
- `captions check transcript-draft.srt` returned [].
- Wrote `captions/en.srt` with the one-word correction (channel → page), keeping the timings. `captions check en.srt` returned [].
- Added `"captions": {"src": "captions/en.srt", "burn": true, "style": "box", "position": "bottom"}` to `plan.json`.
- `render --preview` produced `output/preview-001` (new engine) in 91.3 s with QC WARN (same intro warning).
- Read `text_frames.png`. Both cues are visible in a dark box at the bottom, the word "page" is correct, and nothing is clipped.

**A14:**
> Fixed ✅ It now says "welcome back to the page".
> The new test version with your subtitles written into the video is in: URM-Creator-Studio → projects → calm-corner-reel → output → preview-001.
> I checked the pictures from it: the subtitles appear at the bottom in white letters on a dark box. They're easy to read and nothing is cut off.
> Shall I make the final full-quality version?

**U14:** yes looks good!

**Behind the scenes:**
- `render calm-corner-reel` produced `output/v002` in 85.5 s: 1080×1920, H.264/AAC, 12.83 s, −13.7 LUFS, QC **WARN** (intro safe area only).
- Read `QC_REPORT.md`, `qc/text_frames.png` and `qc/overview.png`.
- The sidecar `captions.srt` and `captions.vtt` are offset +1.65 s for the intro, which is correct.
- The fixture hashes were unchanged.

**A15 (delivery):**
> 🎉 Your Reel is ready!
> ⏱ 0:13 · 📱 tall, for Instagram Reels
> 📁 You'll find it in: URM-Creator-Studio → projects → calm-corner-reel → output → v002 → calm-corner-reel_vertical.mp4
> What I checked: your subtitles are readable and match what you approved, no text is cut off, and the volume is right for social media. Your original files are unchanged. One small note: your name at the very start comes close to Instagram's button area, but it's fully visible.
> Please watch it once yourself before posting. I've also saved a caption file next to the video.
> Would you like a square version for your feed too, or should I change something?

**U15:** what's a caption file?

**A16:**
> A **caption file** is a small text file holding your subtitles and when each one appears, kept separate from the video. For example, YouTube lets you upload it so viewers can turn subtitles on or off.
> For Instagram Reels you don't need it: your subtitles are already written into the video. You can simply ignore that file.
> Anything you'd like to change, or shall we leave it here?

**U16:** no thats perfect thank you!!

---

## 2. Scorecard

| Criterion | Result | Evidence |
|---|---|---|
| Language switch handling | **PASS** | The Arabic welcome showed `🌐 العربية \| English`. Her English reply switched the assistant on the next message, `settings --language en` was saved, and the switch stayed visible in A2. Gap: the English wording for the onboarding brand, materials and message questions and the brand quick-setup questions does not exist in the skill (Arabic only), so the assistant had to translate them on the fly. |
| One question per message | **PASS** | Every assistant message ended with exactly one question. A13 bundled a QC note and a link to the preview with the transcript-review question, but it still asked only one question. |
| Jargon explained | **PARTIAL** | Brand, caption file and the test version were explained in plain words. However, the skill's own colour question (`brand-system.md` step 4) asks a beginner for a hex code "like #1E3A8A", and option 3 "I already have a brand file" means nothing to Maria. |
| Defaults offered | **PASS (with issue)** | "Not sure, choose for me" was offered and used twice. The "⭐ recommended" style is hard-coded to Modern, which gives corporate blue and yellow for a calm yoga brand. Maria said "very blue haha". |
| Transcript reviewed before burning (no invented words) | **PASS** | The whisper draft was shown cue by cue. Her correction (channel → page) was applied word-for-word and no other text was changed. The burned captions match the approved `en.srt`. |
| Confirmation before rendering | **PASS** | The preview started only after "ok yes go" and the final only after "yes looks good!". The second preview, with captions, ran without a new "shall I start?". It was covered by the approved plan ("subtitles: yes, I'll show you first"), which is acceptable. |
| No-logo brand handled gracefully | **PASS (engine warn)** | The reassurance was given and the wordmark appears in the intro and outro. However, the auto-generated intro wordmark itself triggers the only QC warning (`text_in_safe_area: intro @1.05s`), because the 16-character name spans almost the full width. |
| Captions verified in frames | **PASS** | `preview-001` and `v002` `text_frames.png` show both cues in a boxed white caption at the bottom, the word "page" is present, and nothing is clipped. Minor: the grid repeats frames and is not in time order. |
| Publishing correctly refused | **PASS** | A12 says clearly that nothing is posted for her and that she uploads it herself. |
| Delivery clarity | **PARTIAL** | Duration, shape, a friendly folder path, what was checked, the warning, the advice to watch once, and two follow-up options were all given. Problems: the final is in `v002` because of the mid-test engine change; the skill gives no way to actually open or play the file or folder for a beginner; and the delivery mentions a "caption file" without explaining it, which prompted U15. |
| User turns to first video | **12** to the first preview, **14** to the final (16 user messages in total). That is long for "a reel with subtitles". Brand setup alone took 6 turns (U2–U7). |

---

## 3. Problems in the skill instructions or engine

1. **The engine and references changed during the test, and old preview folders now take version numbers.**
   - Where: `scripts/urmstudio/render.py` and `project.py` (modified 13:55:30).
   - What went wrong: the first preview (old engine) was written to `output/v001`. After the change, previews go to `preview-NNN` and the first final became `v002`, which contradicts `quality-control.md` ("the first final is always v001").
   - Fix: when numbering finals, skip `vNNN` folders whose `render.json` has `"preview": true`. Freeze the skill while acceptance tests run.

2. **Transcription is missing from the main workflow, and the step order forces texts to be written before the speech is known.**
   - Where: SKILL.md §4 and `audio-captions.md` step 1.
   - What went wrong:
     - §4 never mentions transcription or caption review; it only appears in `audio-captions.md`.
     - Because "render once without captions first" comes after Plan, the on-screen text ("New to yoga?") was written before anyone knew she says "3 simple tips to stay focused". The hook and the speech don't match, and the promised tips never appear because the clip ends.
     - It also costs three renders (30 s + 91 s + 85 s).
   - Fix:
     - Add a step in §4 between Analyse and Plan for videos with speech: "transcribe the source clip (`transcribe <media file>`), review it, then plan texts that match it."
     - Re-check the on-screen texts against the approved transcript before the preview.
     - The engine already supports `transcribe FILE`. For a single talking clip, the timings only need to shift by the scene start.

3. **The English onboarding wording is missing.**
   - Where: `onboarding.md` Steps 3, 5 and 6, and `brand-system.md` quick setup steps 1–4.
   - What went wrong: these give only Arabic phrasing. `language-en.md` has only the welcome, before-action, delivery and failure templates.
   - Fix: add English versions of the brand-choice, materials, message/CTA and brand-setup questions to `language-en.md`.

4. **The style recommendation ignores the type of business.**
   - Where: `brand-system.md` step 3 ("عصري modern ⭐") and the `onboarding.md` defaults.
   - What went wrong: a yoga or wellness business gets blue and yellow.
   - Fix: recommend a preset from the business type or personality (wellness/spa → minimal or luxury; food → playful; B2B → corporate), or add a soft, calm preset.

5. **The colour question uses jargon.**
   - Where: `brand-system.md` step 4 (asks for "#1E3A8A").
   - Fix: "Do you have colours you always use? Send a picture of your sign, menu or posts, or say 'choose for me'." Keep hex codes for Creator and Pro modes.

6. **The no-logo wordmark violates the engine's own safe area.**
   - Where: engine intro card (`render.py` / `textrender.py`).
   - What went wrong: every render returned WARN `text_in_safe_area intro @1.05s`, and the user can't fix it.
   - Fix: fit the intro wordmark inside the vertical safe box (with the right-side margin for Reels/TikTok buttons), wrap long names onto two lines, or reduce the font size.

7. **Caption cues are split mid-sentence.**
   - Where: the whisper output, plus `captions check` / `reflow` in `captions.py`.
   - What went wrong: "…Today I will show / you 3 simple tips…". `captions check` returned [], so the problem went unnoticed.
   - Fix: re-split at sentence or clause punctuation after transcription, and have `captions check` warn when a cue ends mid-clause (no punctuation while the next cue starts lowercase).

8. **The QC report has no caption line.**
   - Where: `qc.py` and `QC_REPORT.md`.
   - What went wrong: `quality-control.md` lists a "caption readability" check, but the report has no caption row when captions are burned in and fine.
   - Fix: always add a ✅/⚠️ caption row when `captions.burn` is true.

9. **`text_frames.png` is hard to read.**
   - Where: QC frame grid.
   - What went wrong: the six cells include two duplicates (the hook plus cue 1 appears twice) and are not in time order.
   - Fix: deduplicate, sort by timestamp, and label each cell with its time.

10. **The skill never says how the beginner watches the preview or final.**
    - Where: SKILL.md §4 steps 6 and 8, and `language-en.md` Delivery.
    - What went wrong: Beginner mode requires "preview → approval", but nothing tells the assistant how to let a non-technical user see the file. She doesn't know Finder paths, and the folder name differs when `URM_STUDIO_HOME` is set.
    - Fix: tell the assistant to offer to open the video for her (macOS `open <file>`, Windows `start ""`, Linux `xdg-open`) after asking. Make `home` return a friendly path that matches what the user actually sees.

11. **There is no readability check for text on busy images.**
    - Where: QC and the image-scene text style.
    - What went wrong: "Calm, easy yoga for beginners" is white text with only a shadow over a saturated pink and green pattern. It was readable but weak, and QC has no contrast check.
    - Fix: add an automatic scrim or box behind text on image and video scenes when the background is busy, plus a QC contrast warning.

12. **Delivery mentions the sidecar caption file without explaining it.**
    - Where: the `language-en.md` Delivery template and glossary ("SRT file" is only in the Arabic glossary).
    - Fix: add "caption file (SRT)" to the English glossary. In delivery say "You don't need the extra caption file for Instagram" up front.

13. **There is no guidance when the material is shorter than the recipe.**
    - Where: `creative-direction.md` social_short (15–30 s).
    - What went wrong: the material gave about 13 s total, and the skill doesn't say whether to tell the user, extend the photo time, or accept it.
    - Fix: add one line saying a shorter video is fine and the user should be told, or suggest filming one more clip.

14. **Doctor and QC texts are Arabic-first or bilingual even after the user chose English.**
    - Where: the `doctor` item texts and the `QC_REPORT.md` labels.
    - Why it matters: this is harmless because the assistant translates them, but a user who opens `QC_REPORT.md` sees Arabic first.
    - Fix: respect the `settings.language` setting, or the `--lang` flag, in the report text.

15. **Brand onboarding takes too many turns.**
    - Where: `onboarding.md` Step 3 together with the `brand-system.md` 7-step quick setup.
    - What went wrong: brand setup took 6 of 12 turns before a first video.
    - Fix: in Beginner mode, after "no idea" on style, apply the default colours without a separate colour question. Collect the handle and the CTA in one question ("What's your Instagram, and what should people do at the end?"), or postpone the brand preview until the video preview.

---

## 4. Final video and QC

- Final video: `<test-scratch>/onboard-en/projects/calm-corner-reel/output/v002/calm-corner-reel_vertical.mp4`
- Format: 1080×1920, H.264/AAC, 12.83 s, −13.7 LUFS, peak −1.5 dBTP. Sidecar `captions.srt` and `captions.vtt` are offset +1.65 s for the intro.
- QC: **WARN**. Every check passes except `text_in_safe_area: intro @1.05s`, which is the auto wordmark (Problem 6). Originals untouched ✅, brand isolation ✅.
- What I saw in `qc/text_frames.png`:
  - The intro wordmark "Calm Corner Yoga" spans nearly the full width.
  - "New to yoga?" appears at the top over the clip.
  - The boxed captions read "Hi everyone, welcome back to / the page. Today I will show" and "you 3 simple tips to stay focused.", so the correction is present.
  - The photo headline is readable over a busy background.
  - The outro shows the name, the yellow CTA pill and "Instagram @calmcorner.yoga".
  - No clipping and no overlaps.
- Other outputs: preview without captions `output/v001` (old engine) and preview with captions `output/preview-001`.
