[← Back to the guide index](00-index.md)

# 08 · Examples

Four complete walkthroughs, from the first message to the finished video. All names and businesses are
fictional. You can copy any of the briefs below straight into the chat and change the details — more
ready-made briefs are in `examples/briefs/briefs-en.md`.

---

## Example 1 — English creator tip video (Sami Makes)

**Who:** Sami posts productivity tips on TikTok and YouTube Shorts. His brand, **Sami Makes**, is the
example profile `examples/brands/english-creator.json`: English, playful style, deep purple and orange
colours, Inter for English text, outline-style captions, handles `@samimakes` (TikTok),
`@sami.makes` (Instagram) and `@SamiMakes` (YouTube), call-to-action "Follow for more tips".

**The brief:**

> I post productivity tips on TikTok and YouTube Shorts. Make a 30-second vertical video from my talking
> clip: "3 simple tips to stay focused". Add captions and my handle at the end.

**How it goes:**

1. Sami drops `focus-tips.mov` into `URM-Creator-Studio/inbox`.
2. The assistant confirms the brand ("Shall we use Sami Makes?") and the shape (tall, for TikTok/Shorts).
3. It looks at the clip and reports: one talking take, about 45 seconds, good light, a false start at the beginning.
4. **Plan** (shown as a numbered list):
   1. Hook, 0–2 s: "3 tips to stay focused" — word-by-word reveal over Sami's best moment.
   2. Tip 1 with title "1. One tab only".
   3. Tip 2 with title "2. 25-minute timer".
   4. Tip 3 with title "3. Phone in another room".
   5. Outro: "Follow for more tips" + handles.
5. Sami approves. The assistant trims the false start (after asking) and makes a quick test version.
6. **Captions:** with speech-to-text installed, draft captions are created on Sami's computer. One unclear
   line is marked `[?]`; Sami corrects it. Without speech-to-text, Sami would paste his script instead.
7. Final render: a 0:30 tall video with captions written in, plus `captions.srt` for YouTube.
8. Sami asks for a wide version for his YouTube channel — a new version folder is created.

---

## Example 2 — Product ad (Loop water bottle)

**Who:** a small shop launching a reusable bottle called "Loop". They set up a quick brand profile in the
**Bold** style with their logo.

**The brief:**

> We're launching a reusable water bottle called "Loop". I want a 20-second ad with three features
> (keeps cold 24h, leak-proof, recycled steel), the price $29 and "Order now — link in bio".

**How it goes:**

1. Materials: six product photos and two short clips of the bottle in use.
2. The assistant asks where it will be posted → Instagram Reels and the feed → tall first, square copy later.
3. **Plan:**
   1. Desire, 0–2.5 s: "Cold water. All day." over the hero shot.
   2. Feature: "Keeps cold 24h" (photo with slow zoom).
   3. Feature: "Leak-proof" (clip of the bottle in a bag).
   4. Feature: "Recycled steel" (close-up photo).
   5. Offer: "$29" — large, with a zoom animation.
   6. Call-to-action: "Order now — link in bio".
   7. Brand outro with logo.
4. The assistant checks the claims with the owner: "Is 24 hours accurate for your bottle?" Ad claims must
   be true — it never invents them.
5. Music: the owner has a track bought with a business licence. It's added under the video at a low volume.
6. Preview → "make the price bigger" → new preview → final.
7. Then: "Now a square version for the feed, please." The texts are re-laid out for the square shape.

---

## Example 3 — Bilingual studio post (Dar Al-Sana)

**Who:** **Dar Al-Sana Studio** («دار السَّنا»), a fictional bilingual design studio —
`examples/brands/bilingual-studio.json`. Both Arabic and English names, navy and sky-blue colours, Cairo
and Tajawal for Arabic, Inter for English, brand-coloured captions, Western digits, a small corner logo,
website `daralsana.example`, tagline «تصميم يحكي قصتك» / "Design that tells your story".

**The brief:**

> Our studio is bilingual (Arabic/English). Make a square post video with the Arabic headline first and
> the English line under it: «تصميم يحكي قصتك» / "Design that tells your story".

**How it goes:**

1. Materials: five photos of finished design projects.
2. The assistant confirms: square shape, video language "bilingual", Arabic first.
3. **Plan:**
   1. Intro with the logo.
   2. Title card on the brand gradient: «تصميم يحكي قصتك» with "Design that tells your story" underneath.
   3. Three project photos with gentle pans, short labels in both languages.
   4. Outro: «تواصل معنا لمشروعك القادم» / "Let's talk about your next project" + website.
4. In the rendered frames the Arabic line is right-to-left and connected; the English line is
   left-to-right; the web address stays in one piece. The assistant checks these pictures before
   reporting back.
5. The owner, who doesn't read Arabic fluently, asks an Arabic-speaking colleague to read the text once
   before posting — good practice (see [Arabic typography](06-arabic-typography.md)).

---

## Example 4 — English interview with Arabic subtitles

**Who:** a coach who recorded a 3-minute interview in English and has many Arabic-speaking followers.

**The brief:**

> I recorded an interview in English. Please add Arabic subtitles so my Arabic-speaking audience can follow.

**How it goes:**

1. The assistant asks about the shape (wide for YouTube) and whether to add a name banner for the guest.
2. It puts the video together once without subtitles, so the timing is final.
3. **Transcription:** the English speech is turned into draft subtitles on the coach's computer. Flagged
   lines are reviewed with the coach — names and numbers especially.
4. **Translation:** the assistant translates the approved English subtitles into natural Modern Standard
   Arabic, keeping the original timing and names. It's labelled as a translation, and the coach approves it.
5. **Delivery options** the assistant offers:
   - Arabic subtitles written into the video, plus the English subtitles as a separate `.srt` file, or
   - two versions of the video: one with Arabic subtitles, one with English.
6. The rendered frames are inspected: Arabic subtitles connected, at most two lines, punctuation on the
   correct side, clear of the YouTube controls.
7. The subtitle files are ready to upload to YouTube as extra subtitle tracks.

The coach's face and voice are never altered — the studio only adds subtitles, banners and trims.

---

[← Troubleshooting](07-troubleshooting.md) · Next: [FAQ →](09-faq.md)
