# Creative-led production (Mode B): from an idea to a finished video

Use this when the user has **an idea but few or no assets**: no footage, no photos, no logo, no colours, no
music. You are the creative director, designer, editor and sound designer. The user should never have to
think about editing, prompting or file formats. A row of still images with zoom effects and a music bed is
**not** an acceptable result: the engine's QC fails it in creative mode.

## 0. Choose the production mode (after onboarding step 5)
| What the user has | Mode | Plan |
|---|---|---|
| Usable footage / photos of their own | **A — asset-led** (`production.mode: "asset"`) | `video` / `image` scenes as before; add motion scenes for the hook, benefits and CTA when they make it stronger |
| Only an idea, text, a product description or a brief | **B — creative-led** (`"creative"`) | `motion` scenes carry the video; images (if any) appear inside `showcase` compositions |
| Some assets, gaps elsewhere | **mixed** (`"mixed"`) | Their footage for authenticity, motion scenes for structure, story and CTA |

Never ask the user to provide a logo, brand guide, footage, music or a script before you can start.

## 1. Ask only what changes the result (one question per message, Beginner)
You usually already have the video type, audience and platform from onboarding. Then at most:
1. **Name** to show on the end card: «ما الاسم الذي يظهر في نهاية الفيديو؟ (أو بدون اسم)» / "What name should
   appear at the end? (or none)". No name → the CTA scene simply has no mark (`"mark": false`).
2. **Action + contact**: what should viewers do, and where (website, @handle, WhatsApp — only if they say so).
3. **Facts you will show**: any number, price, date, "certified", "accredited", "best" must come from the user.
   Ask once, listing them: «سأكتب هذه المعلومات في الفيديو، هل هي صحيحة؟ …». Without true numbers, do not
   use the `stats` template and write benefit statements that make no factual claim.
Everything else (look, music, pacing, transitions, wording) you decide, and show in the plan summary.

## 2. Concept (write it, one line) and story arc
Find one idea the whole video serves, e.g. *"Your world, in a new language: from first words to new
opportunities."* Then shape the arc. 30 s social ad default:

| Beat | Seconds | Purpose | Good templates |
|---|---|---|---|
| Hook | 3.5–4.5 | a question, a bold promise, a surprising line | `kinetic_title` |
| World / desire | 3.5–4 | show the audience's world or wish | `word_cloud`, `globe`, `showcase` |
| Proof / benefits | 4–5 | why trust this, 2–4 benefits | `features`, `stats` (true numbers only), `quote` (real quotes only) |
| Transformation | 4–5 | before → after, a path, progress | `journey`, `contrast` |
| Call to action | 4–5 | name, action, contact | `cta` |

15 s: hook → one benefit scene → CTA. 45–60 s: add a second world scene and a second proof scene. Use **at
least 3 different templates** for anything ≥ 15 s, and never two identical templates back to back.

## 3. Script and on-screen copy
- Write for the eye: headlines ≤ 7 words, subtitles ≤ 8 words, one idea per scene. Mark one key word per
  headline with `highlight` (a single word that appears in the text).
- Reading time sets the length: **scene duration ≥ 1.2 s + 1.5 s + 0.3 s × (words on screen)**. QC warns when
  a text is not visible long enough; shorten the text before lengthening the video.
- Arabic: same rules as `language-ar.md` (MSA by default, imperatives for CTAs, numerals per brand).
- Optional narration: write a voice-over script that matches the scenes (≈ 2.3 words/second English,
  ≈ 2 words/second Arabic). Synthetic voice only with consent (`audio-captions.md`).

## 4. Visual identity
- Brand saved → motion scenes take its colours, fonts and logo automatically (`look` is derived from the
  brand). Nothing to do.
- No brand → choose a **look** (`studio.py looks`) that fits the business; say in one line why («اخترتُ
  ألوانًا زرقاء وذهبية توحي بالثقة»). If the user named colours in words, pass them as overrides:
  `"look": {"preset": "academy", "palette": {"primary": "#0F766E"}}`.
- No logo → `"identity": {"name": "…"}` builds a **temporary monogram** from the initials. Tell the user it
  is a placeholder they can replace later with a real logo (`brand logo`), and never present it as a logo
  design they own.

| Look | Fits | Soundtrack mood |
|---|---|---|
| academy | education, training, consulting, trust | inspiring |
| fresh | health, apps, services, start-ups | corporate |
| warm | food, cafés, family, community, retail | playful |
| luxury | fashion, perfume, jewellery, hospitality, real estate | luxury |
| tech | software, AI, gaming, electronics | energetic |
| bold | sales, sport, events, launches | energetic |
| calm | wellness, beauty, clinics, non-profits (light background) | calm |
| playful | kids, youth, games, creators | playful |

## 5. Visual assets: the decision ladder
Work down the ladder; stop at the first rung that gives the scene what it needs.
1. **The user's own footage and photos.** Always best for authenticity. Ask once if they can film 3–5 short
   clips (with simple tips) — but do not block production on it.
2. **AI image or video generation — only if a generation tool is actually available in this session.**
   Look at your tool list (for example an image/video generation connector). Never assume one exists, never
   invent one. Before using it: tell the user which service it is, that it may use their credits/plan,
   and get a yes. Prompt for places, objects, textures, abstract scenes; **no synthetic people** unless the
   user explicitly asks and `safety.md` allows it. Save results into the project (`project add`) and record
   them: `asset register <project> media/<file> --origin ai-generated --provider "<service>" --license
   "<what its terms allow>" --prompt "<prompt>"`.
3. **Licensed stock — only through a stock provider tool available in this session** (or files the user
   licensed themselves). Never download from websites. Record: `--origin stock --provider … --license …
   --credit …`.
4. **Engine motion design — always available, offline, free.** The motion templates can carry a whole
   video. This is the default for Mode B, not a fallback.

Stills (from any rung) go inside a `showcase` scene (shaped frame, parallax push, floating chips, depth
shapes), or behind motion graphics — not as bare `image` scenes in a row. Moving footage (user, AI, stock)
uses ordinary `video` scenes with scene texts.

**Never** say or imply that generated or stock media was made by URM Creator Studio. In the delivery message
say plainly: graphics and music generated by the studio engine; images from <provider> (AI-generated) etc.
The render writes the same facts to `production.json`.

## 6. Music and sound
- User music they own/licensed → `audio.music` (as before).
- Otherwise `"audio": {"score": {"mood": "<mood>"}}`: the engine composes an **original soundtrack** for
  this edit (pads, bass, arpeggio, drums that enter after the hook, a hit on the brand/CTA reveal, whooshes
  on transitions, pops when elements land). It is generated locally and needs no licence. Moods:
  inspiring, corporate, energetic, calm, luxury, playful. `"sfx": false` keeps the music without effects.
- With a voice-over the score is lowered and ducked automatically.
- An AI music tool in the session is optional and follows the same consent + `asset register` rules.

## 7. Storyboard → plan
Show the user a numbered scene list (Beginner) or a table (Creator/Pro): beat · seconds · what we see ·
exact on-screen words. Wait for approval. Then write plan.json (`plan-reference.md`, section *Motion
scenes*). Leave transitions to the engine unless the user wants something specific; it alternates within
the look's transition family and hides every cut under a designed wipe.

## 8. Render, check, deliver
Tell the user how long it takes before you start (measured on an 8 GB Apple-silicon Mac, 30 s vertical video):
preview ≈ 1 minute, final ≈ 3 minutes; a 15 s landscape final ≈ 1.5 minutes; an unchanged re-render reuses the
cached motion clips (about half the time). On machines with 8 GB RAM or less the engine draws with 2 browsers at
once to stay within memory; `URM_MOTION_WORKERS` changes that. Ask the user to close heavy apps for a final.
1. `render <project> --preview` (half size). Look at `qc/text_frames.png` and `qc/overview.png` yourself.
   Fix layout/copy problems in the plan (not in the engine) and preview again.
2. Open the preview for the user. After approval: `render <project>`. Motion clips are cached, so a final
   after a text-card or audio change does not redraw unchanged scenes.
3. QC creative gates must be ✅: *the picture keeps moving*, *not a slideshow*, *complete creative
   structure*. Read `QC_REPORT.md` and look at the frames before you say anything about the result.
4. Deliver in plain words: the video (friendly copy in the project folder), its shape and length, the cover
   image (`cover.jpg`), the subtitle file of the on-screen words (`onscreen_text.srt`, or `captions.srt`
   with speech), and one sentence on what was generated and by whom. Offer one or two follow-ups (another
   format, a version with their own clips or logo).

## Self-check before showing the plan
- Would the first 2 seconds stop a scroll? Is there one clear idea?
- Does every scene move and show something different? ≥ 3 templates, no static holds?
- Are all claims true and approved? No invented statistics, testimonials or people?
- Is the CTA specific (what + where)?

## What is local, what needs a provider
| Element | Where it comes from | Cost / licence |
|---|---|---|
| Motion graphics, typography, transitions, monogram mark | the studio engine, on this computer (Chromium + FFmpeg) | free; original to the video. They are designed graphics, **not** AI-generated video — never describe them as such |
| Soundtrack and sound effects | the studio engine (synthesised on this computer) | free; original, no licence needed |
| The user's footage, photos, logo, voice, music | the user | the user's rights; originals are never changed |
| AI images / AI video / AI music | **only** a generation tool actually connected to this Claude session, with the user's yes | the provider's plan or credits and the provider's terms; recorded with `asset register --origin ai-generated` |
| Stock footage / photos | **only** a stock tool connected to this session, or files the user licensed | the provider's licence; recorded with `--origin stock --license … --credit …` |
| Synthetic narration | macOS system voice, only with consent (`audio-captions.md`) | free; label it as a computer voice |

If no provider is connected, say so in one plain sentence and continue with engine motion design — the video is
still complete. Never imply a subscription, integration or licence the user does not have.
