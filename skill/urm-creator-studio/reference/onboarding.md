# Onboarding flow (first-time and every new video)

Golden rules: **extract first** — after every free-text answer, fill every field it already answers (video
type, platform, offer, deadline, CTA, brand name) and skip those questions; confirm in one line
(«فهمت: ريلز لعرض رمضان بخصم 15٪ على إنستغرام ✅»). Then **one question per message**, numbered choices, the recommended choice first and marked
(«⭐ مقترح» / "⭐ recommended"), always accept free text, always offer «لا أعرف، اختر لي» / "Not sure —
choose for me" which applies the default shown below.

## Step 0 — language (only if not saved)
Greet in Arabic with the switch (template in `language-ar.md`). If the reply is English, switch and save:
`studio.py settings --language en`. If the user picks Arabic or writes Arabic: `--language ar`.

## Step 1 — device check (silent)
`studio.py --json doctor`. If `ready` is false: explain the missing item using its `fix` text, in the user's
language, one step at a time, and ask permission before running any install command. Re-run doctor after.
Optional items (speech-to-text, voice) are mentioned only when needed.

## Step 2 — what video?  (choices list in `language-ar.md` / `language-en.md`)
Map the answer to a recipe in `creative-direction.md`:

| # | Arabic label | Recipe key | Default shape | Default length |
|---|---|---|---|---|
| 1 | فيديو قصير للسوشيال ميديا | social_short | vertical | 15–30 s |
| 2 | إعلان تجاري | ad | vertical (+ square copy) | 15–30 s |
| 3 | فيديو تعريفي بالشركة | brand_intro | landscape (+ vertical cut) | 45–90 s |
| 4 | فيديو لمنتج أو خدمة | product | vertical | 20–40 s |
| 5 | فيديو تعليمي | explainer | vertical (short) / landscape (long) | 30–90 s |
| 6 | فيديو لفعالية أو مناسبة | event | vertical | 30–60 s |
| 7 | فيديو شخصي | personal | vertical | 15–60 s |
| 8 | فكرة أخرى | ask one follow-up question, then pick the closest recipe | | |

## Step 3 — brand
- If brands exist and one is default: «هل نستخدم هوية <الاسم>؟ (نعم / هوية أخرى / بدون هوية)».
- If none: offer two options (EN in brackets):
  1. «إعداد سريع لهويتك: الاسم والشعار والألوان (دقيقتان) ⭐ مقترح» ("Quick brand setup: name, logo, colours —
     2 minutes ⭐") → `brand-system.md` quick setup
  2. «المتابعة بدون هوية الآن» ("Continue without a brand for now") → neutral style, no logo, no intro/outro
  (Importing an existing brand.json is only offered to Creator/Pro users or when the user mentions a file.)

## Step 4 — where will it be posted? (sets shape)  «أين ستنشر الفيديو؟» / "Where will you post it?"
1. Instagram Reels / TikTok / YouTube Shorts / Snapchat → vertical ⭐
2. Instagram or Facebook post → portrait (4:5) or square
3. YouTube / website / presentation screen → landscape
4. «أكثر من مكان» → main shape + extra exports at the end

## Step 5 — materials
Explain simply where to put files (EN: "Put your photos, videos, logo and music in the **inbox** folder inside
the URM-Creator-Studio folder in your home folder, or drag them into this chat. Tell me when you're done."):
> «ضع الصور والفيديوهات والشعار والموسيقى في مجلد **inbox** داخل مجلد «URM-Creator-Studio» في حسابك،
> أو اسحبها إلى هذه المحادثة. أخبرني عندما تنتهي.»
Run `studio.py open inbox` so the folder appears on their screen (don't just give a path). If the user has no footage: offer a text-and-photo video
(title scenes + brand colours), never synthetic people.

Ask about music only if relevant: «هل لديك موسيقى تملك حق استخدامها؟ (نعم وسأرسلها / بدون موسيقى ⭐)» /
"Do you have music you're allowed to use? (yes, I'll send it / no music ⭐)".
Explain licensing in one line if they want music from the internet: «يجب أن تكون الموسيقى مسموحة
الاستخدام، مثل مكتبة الصوت المجانية في يوتيوب أو موسيقى اشتريتها».

## Step 6 — message & text
Ask for the main message in their words: «ما أهم رسالة تريد أن يفهمها المشاهد؟ (مثال: افتتاح فرع جديد،
خصم ٢٠٪)» / "What's the one thing viewers should take away? (e.g. new branch opening, 20% off)". Then ask for the call-to-action: «ماذا تريد من المشاهد أن يفعل في النهاية؟» / "What should viewers do at the
end?" with choices: زيارة المحل / الطلب عبر واتساب / المتابعة / التسجيل / الاتصال / أخرى — visit / order on
WhatsApp / follow / sign up / call / other.
You write the on-screen text yourself (short, punchy, natural Arabic) and show it for approval.

## Step 7 — confirm the plan (always before rendering)
Show a short numbered scene list with exact texts and durations, shape, music yes/no, captions yes/no.
Ask «هل أبدأ بتجهيز نسخة تجريبية؟» / "Shall I make a quick test version?". Then preview → feedback → final.

## Defaults when the user says "choose for me"
shape by platform (vertical), length 20 s, brand colours, fonts from brand, fade transitions (slide for
energetic), captions ON when there is speech, music OFF unless provided, intro ON (2 s) and outro ON (3 s)
when a brand exists, watermark OFF, numerals: Western in chat, brand setting in video.

## Things never to ask beginners
fps, codec, bitrate, resolution numbers, LUFS, file formats, crop coordinates, font weights.

## Keeping it short
Target: first test version within ~8 user replies. Combine steps when the user already gave the answer
(e.g. "Reel for Instagram about my Ramadan offer" answers type, platform and message at once). Never re-ask
something already answered.

## Gendered Arabic
Until the user's gender is clear, prefer phrasing that avoids gendered verbs («يكفي الرقم فقط»، «الخطوة التالية:
إرسال الشعار»). Once it is clear (a name like «أم خالد», self-reference «أنا صاحبة…»), use the matching forms
(«تريدين»، «أرسلي»). Never guess from a business type.

## Text-only changes after a preview
If the user only changes wording (same scenes, same timing): confirm the exact new text, render the final
directly, and **look at the QC frames** before delivering (text length can change layout and timing).
Any change to scenes, media, order or timing → new preview first.
