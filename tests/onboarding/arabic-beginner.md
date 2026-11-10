# Onboarding test: Arabic beginner, «أم خالد»

- **Date:** 2026-11-10
- **Skill under test:** `skill/urm-creator-studio` (SKILL.md, reference/*.md, scripts/studio.py). No skill files were edited.
- **Workspace (isolated):** `URM_STUDIO_HOME=<test-scratch>/onboard-ar` (fresh and empty at start). `~/URM-Creator-Studio` was not touched.
- **Persona:** «أم خالد», 45, home-made sweets in Riyadh («حلويات أم خالد», fictional). Arabic only, a mix of Saudi dialect and MSA. Never used an AI tool before.
- **User files:** `logo_arabic.png`, `clip_landscape.mp4`, `photo_portrait.jpg` from `scratchpad/fx/`. They were copied into `inbox/`, and the fx originals were not modified (checked with sha256).
- **Method:** I played both roles. The assistant followed SKILL.md and loaded `language-ar.md`, `onboarding.md`, `brand-system.md`, `creative-direction.md`, `plan-reference.md`, `quality-control.md` and `arabic-typography.md` at the steps that call for them. Every engine command the assistant would run was actually run. The assistant was not allowed to know more than the skill tells it. Where it had to improvise, the turn is marked **[improvised, not in skill]**.

> Fixture caveat: the "kitchen video" and the "photo" are synthetic test fixtures (moving colour gradients and a gold-brown gradient). The logo fixture reads «الريحان — مقهى ومحمصة», not «حلويات أم خالد». The persona was told to treat these files as her own. The assistant still described what it really saw, as the skill requires.

---

## 1. Transcript

The user never sees the commands. They are listed under each assistant turn in a collapsed "behind the scenes" block. `S` = `python3 "<skill>/scripts/studio.py"`, always run with `URM_STUDIO_HOME` exported in the same shell.

---

### Turn A1 (assistant)

> أهلًا بك في **استوديو URM للإبداع** 🎬
> أنا مساعدك في صناعة الفيديو، وسأساعدك خطوة بخطوة حتى لو كانت هذه أول مرة لك.
> أستطيع تجهيز فيديوهات للسوشيال ميديا وإعلانات وفيديوهات تعريفية، بألوانك وشعارك، مع نصوص عربية متحركة وترجمة مكتوبة.
>
> 🌐 العربية | English
>
> ما نوع الفيديو الذي تريد صنعه اليوم؟
> 1. فيديو قصير للسوشيال ميديا (ريلز، تيك توك، شورتس)
> 2. إعلان تجاري
> 3. فيديو تعريفي بالشركة
> 4. فيديو لمنتج أو خدمة
> 5. فيديو تعليمي
> 6. فيديو لفعالية أو مناسبة
> 7. فيديو شخصي
> 8. فكرة أخرى
>
> اكتب الرقم فقط، أو صف فكرتك بكلماتك.

<details><summary>Behind the scenes</summary>

- `S --json doctor` → `ready: true` (Python 3.9, FFmpeg, x264, Chrome, fonts, whisper, voice all OK). Silent.
- `S --json settings` → `language: null, mode: beginner, default_brand: null`
- `S --json brand list` → `[]` → first-time user → `onboarding.md`
- `S --json home` → workspace created (brands/ projects/ inbox/ models/ README.txt)
- (test harness: the three fixture files were copied into `inbox/`)
- Message = the welcome template from `language-ar.md` L68–85, word for word.
</details>

### Turn U1 (user)

> السلام عليكم ابي فيديو حلو للانستا عن عرض رمضان عندي خصم 15 بالميه

### Turn A2 (assistant)

> وعليكم السلام ورحمة الله 🌙 فكرة جميلة! سنصنع معًا فيديو لعرض رمضان مع خصم 15%.
> أولًا: هل نحفظ «هوية» نشاطك؟ الهوية تعني اسمك وشعارك وألوانك، أحفظها مرة واحدة فتظهر في كل فيديوهاتك.
> 1. إعداد سريع للهوية (دقيقتان) ⭐ مقترح
> 2. المتابعة بدون هوية الآن
> 3. لدي ملف هوية جاهز
>
> اكتب الرقم، أو قل «اختر لي».

<details><summary>Behind the scenes</summary>

- `S --json settings --language ar` → saved.
- Mapped to recipe `ad`/`social_short` (offer plus Instagram). The assistant did not re-ask "what video" because U1 had already answered it. The skill never says to skip questions that are already answered; this is assistant judgement (see Problem P3).
- The one-line meaning of «هوية» follows the 4-step explanation pattern. `onboarding.md` Step 3 does not supply that sentence.
</details>

### Turn U2

> واحد

### Turn A3

> ممتاز ✅ ما اسم نشاطك أو علامتك؟ يمكنك كتابته بالعربية أو الإنجليزية أو الاثنين.

### Turn U3

> حلويات ام خالد

### Turn A4

> تشرفنا يا أم خالد 🌷
> هل لديك شعار؟ أرسلي ملفه (PNG بخلفية شفافة هو الأفضل). إن لم يكن لديك شعار فلا مشكلة، سأكتب اسمك بخط جميل بدلًا منه.

<details><summary>Behind the scenes</summary>

- `S --json brand new --name-ar "حلويات أم خالد" --style modern` → slug `حلويات-أم-خالد`
- `--style` had to be chosen now, although the style question only comes two steps later (Problem P5).
- The assistant normalised her spelling to «أم» with a hamza (`arabic-typography.md` L26).
- The logo question is the scripted text from `brand-system.md` L11, including «PNG».
- The assistant switched to feminine forms once the name made the gender clear. The skill only covers the "gender unknown" case (`language-ar.md` L7–8).
</details>

### Turn U4

> عندي شعار بس وش يعني PNG؟ وكيف ارسله ما ادري

*(The persona's "what does this jargon mean?" moment. The skill avoids «ريندر» everywhere, so the jargon that actually triggered it was «PNG», which comes from the skill's own script.)*

### Turn A5

> سؤال ممتاز 👍 **PNG** نوع من ملفات الصور، مثل صور الجوال تمامًا، لكنه يحفظ الشعار بدون مربع أبيض حوله.
> لا تحتاجين لفعل شيء خاص: أرسلي الشعار كما هو عندك، وأنا أتعامل معه.
>
> لإرسال الملفات: ضعيها في مجلد **inbox** داخل مجلد «URM-Creator-Studio» في جهازك، أو اسحبيها إلى هذه المحادثة. ضعي معه فيديو المطبخ والصورة أيضًا لنوفّر الوقت.
> أخبريني عندما تنتهين.

<details><summary>Behind the scenes</summary>

- 4-step explanation pattern (`language-ar.md` L23–27).
- Folder sentence from `onboarding.md` L45–46. The skill has no way to open the folder for her (Problem P8).
- Asking for all materials at once is assistant judgement. The skill asks for the logo in the brand step and for the media in Step 5, which would mean explaining the folder twice.
</details>

### Turn U5

> خلاص حطيتهم الشعار وفيديو المطبخ وصوره

### Turn A6

> وصلني الشعار ✅ دائرة خضراء غامقة مكتوب فيها «الريحان — مقهى ومحمصة» بلون كريمي.
> لاحظتُ أن الاسم في الشعار يختلف عن «حلويات أم خالد». هل هذا هو الشعار الذي تريدين استخدامه؟ (نعم / لا، سأرسل غيره)

<details><summary>Behind the scenes</summary>

- `ls inbox/` → the 3 files.
- `S --json brand logo حلويات-أم-خالد inbox/logo_arabic.png` → copied to `brands/…/assets/logo-main.png`. The original is unchanged.
- Read the logo image. It is an RGBA PNG with transparent corners, so the "transparent PNG is better" tip did not apply.
- `brand-system.md` L13 ("describe it in one line to confirm") caught a real mismatch between the logo text and the business name. Good skill behaviour.
</details>

### Turn U6

> ايه هذا هو استخدمه

### Turn A7

> تمام 👍 الآن نختار طابع فيديوهاتك:
> 1. عصري: نظيف وحيوي ⭐ مقترح
> 2. فاخر: هادئ وأنيق
> 3. مرح: ألوان مبهجة
> 4. رسمي: جاد ومرتّب
> 5. بسيط: قليل التفاصيل
> 6. جريء: قوي ولافت مثل إعلانات التخفيضات
>
> اكتبي الرقم، أو قولي «اختاري لي».

<details><summary>Behind the scenes</summary>

- `brand-system.md` L15–16 lists only `عصري modern ⭐ · فاخر luxury · …`. The one-line Arabic descriptions above were written by the assistant (Problem P6).
- The recommendation is "modern" for every business. The skill gives no hint to tailor it, for example sweets and Ramadan → warm/luxury/playful.
</details>

### Turn U7

> ما ادري اختار لي انت

### Turn A8

> اخترتُ لك الطابع العصري ✅
> هل لديك ألوان محددة لعلامتك؟ أرى في شعارك أخضر غامقًا ولونًا كريميًا ذهبيًا:
> 1. ألوان شعارك: أخضر غامق وذهبي فاتح ⭐ مقترح
> 2. ألوان أخرى: أرسلي كود اللون (مثل ‎#1E3A8A) أو صورة من تصميمك

<details><summary>Behind the scenes</summary>

- Style stays `modern`, which was already applied at `brand new`, so this run was unaffected by P5.
- Dominant logo colours were extracted with an ad-hoc Python/PIL one-liner (`#14532D` 266k px, `#FEF3C7`, `#FDE68A`). The engine has no colour-extraction command (Problem P7).
- «كود اللون» and a hex code are scripted in `brand-system.md` L17. That is jargon for this persona.
</details>

### Turn U8

> ما ادري الوان الشعار حلوه خلها

### Turn A9

> حفظتُ الألوان ✅
> هل لديك حساب على Instagram أو غيره تريدين أن يظهر في نهاية الفيديو؟ اكتبي اسم الحساب (مثل ‎@name) أو قولي «لا».

<details><summary>Behind the scenes</summary>

- `S --json brand set حلويات-أم-خالد colors.primary "#14532D"`
- `S --json brand set … colors.accent "#FDE68A"`
- `S --json brand set … colors.secondary "#1F7A47"` (a lighter green the assistant derived)
</details>

### Turn U9

> انستا umkhalid.sweets والطلبات على الواتس

### Turn A10

> ممتاز ✅ ماذا تريدين من المشاهد أن يفعل في نهاية الفيديو؟
> 1. يطلب عبر واتساب ⭐ مقترح (لأن طلباتك تصلك هناك)
> 2. يتابع حسابك في Instagram للمزيد
> 3. يزور المحل
> 4. شيء آخر

<details><summary>Behind the scenes</summary>

- `S --json brand set … handles.instagram "@umkhalid.sweets"`
- The assistant did **not** ask for her WhatsApp number (`safety.md` L27: no phone numbers on screen unless the user asks). The result is a CTA saying "order via WhatsApp" with no number (Problem P12).
- This one question covers both `brand-system.md` step 6 (outro CTA) and `onboarding.md` Step 6 (CTA). The skill asks it twice (Problem P4).
</details>

### Turn U10

> واتساب

### Turn A11

> جهّزتُ شكل البداية والنهاية لفيديوهاتك 🎨
> • البداية: شعارك فوق اسم «حلويات أم خالد» على خلفية خضراء.
> • النهاية: زر ذهبي مكتوب فيه «اطلبوا الآن عبر واتساب» وتحته حسابك.
> هل يعجبك الشكل؟

<details><summary>Behind the scenes</summary>

- `S --json brand set … outro.cta.ar "اطلبوا الآن عبر واتساب"` (plural imperative addressed to viewers)
- `S --json brand check حلويات-أم-خالد` → `[]` (no problems)
- `S --json brand preview حلويات-أم-خالد` → `preview/intro.png`, `preview/outro.png`. Both were opened with Read and the Arabic checked: joined letters, correct order, lam-alef in «الآن» correct.
- `brand-system.md` L23–24 says "show the two preview images … by reading them". Reading shows them to the model, **not to the user** (Problem P9).
</details>

### Turn U11

> ما شفت شي 🤔 وين الصوره

### Turn A12 **[improvised, not in skill]**

> آسف على ذلك! فتحتُ لك الصورتين على الشاشة الآن 👀 هل يعجبك الشكل؟

<details><summary>Behind the scenes</summary>

- `open brands/حلويات-أم-خالد/preview/intro.png brands/…/preview/outro.png` (macOS). No skill instruction or engine command covers this.
</details>

### Turn U12

> حلوه 👍

### Turn A13

> جميل ✅ هويتك محفوظة الآن.
> في أي مكان من Instagram ستنشرين الفيديو؟
> 1. الريلز: فيديو طولي يملأ شاشة الجوال ⭐ مقترح
> 2. منشور عادي في الصفحة (شكل مربع تقريبًا)

<details><summary>Behind the scenes</summary>

- `S --json settings --brand حلويات-أم-خالد`
- `onboarding.md` Step 4. U1 had only said «للانستا», so this question is still needed.
</details>

### Turn U13

> ريلز

### Turn A14

> تمام 📱
> شاهدتُ ملفاتك: الفيديو مدته 8 ثوانٍ ومصوَّر بالعرض، وفيه ألوان ذهبية وزرقاء متحركة. والصورة بألوان ذهبية وبنية دافئة. سأضع الفيديو داخل إطار طولي مع خلفية ضبابية من نفس اللقطة حتى لا يُقص منه شيء.
> هل لديك موسيقى تملكين حق استخدامها؟
> 1. بدون موسيقى ⭐ مقترح
> 2. نعم، وسأرسلها

<details><summary>Behind the scenes</summary>

- `S --json project new "عرض رمضان" --brand حلويات-أم-خالد --format vertical --language ar --type social` → slug `عرض-رمضان`
- `S --json project add عرض-رمضان inbox/clip_landscape.mp4 inbox/photo_portrait.jpg` → read-only copies in `media/` (`-r--r--r--`)
- `S --json inspect projects/عرض-رمضان/media/* --sheet projects/عرض-رمضان/work/sheets` (35.7 s). Clip: 8.0 s, 1920×1080, 30 fps, SDR, mono AAC at **−38.5 LUFS**, no cuts. Photo: 1200×1600.
- Read `clip_landscape_sheet.png`: moving yellow/blue/teal gradients. The fixture shows no kitchen, so the assistant described only what it saw (`creative-direction.md` L15–19).
- Music question from `onboarding.md` L50.
</details>

### Turn U14

> لا بدون

### Turn A15

> حسنًا 👌 ما أهم شيء يجب أن يعرفه الزبون عن العرض؟ مثلًا: هل الخصم على كل الحلويات؟ وإلى متى؟

<details><summary>Behind the scenes</summary>

- `onboarding.md` Step 6, plus `safety.md` L12 (claims about discounts must be the user's own). Strictly this is two sub-questions about a single topic.
</details>

### Turn U15

> على كل شي طول رمضان

### Turn A16

> هذه خطة الفيديو 🎬 (طولي للريلز، 16 ثانية تقريبًا):
> 1. البداية: شعارك واسم «حلويات أم خالد»
> 2. لقطة من الفيديو مع عبارة: «عرض رمضان بدأ»
> 3. لقطة ثانية مع عبارة: «حلويات بيتية مصنوعة بحب»
> 4. صورتك مع عبارة كبيرة: «خصم 15%» وتحتها: «على كل الحلويات»
> 5. عبارة: «طوال شهر رمضان»
> 6. النهاية: «اطلبوا الآن عبر واتساب» مع حسابك ‎@umkhalid.sweets
>
> بدون موسيقى، مع صوت الفيديو الأصلي. ملفاتك الأصلية لن تتغير.
> هل أبدأ بتجهيز نسخة تجريبية؟ (نعم / أريد تعديلًا)

<details><summary>Behind the scenes</summary>

- The assistant wrote all on-screen copy (`creative-direction.md` L63–69): headlines of 7 words or fewer, Western digits as in the brand's `numerals: western`, «15%» with a Western percent sign as in `arabic-typography.md` L30.
- «حلويات بيتية» is backed by the persona (home-made). «مصنوعة بحب» is soft marketing language, not a factual claim.
</details>

### Turn U16

> نعم

### Turn A17

> جارٍ تجهيز النسخة التجريبية… قد يستغرق ذلك دقيقة أو دقيقتين ⏱
>
> (بعد الانتهاء)
>
> النسخة التجريبية جاهزة ✅ (نسخة أصغر حجمًا للمراجعة فقط).
> راجعتُ النصوص العربية في صور مستخرجة منها: الحروف متصلة وواضحة ولا يوجد نص مقطوع.
> 📁 تجدينها في مجلد: URM-Creator-Studio ← projects ← عرض-رمضان ← output ← preview-001
> شاهديها وأخبريني: هل نجهّز النسخة النهائية، أم تريدين تعديل شيء؟

<details><summary>Behind the scenes</summary>

- Wrote `projects/عرض-رمضان/plan.json`: 4 scenes, slide 0.35 s, branding intro/outro, CTA, `output_name: ramadan-offer`.
- `S --json render عرض-رمضان --preview` → `output/preview-001/ramadan-offer_vertical_preview.mp4`, 16.25 s, 540×960, **QC PASS**, 74 s.
- Read `QC_REPORT.md`: all ✅, −13.6 LUFS.
- Read `qc/text_frames.png`. All 7 text moments show correctly joined Arabic in the right order: «حلويات أم خالد», «عرض رمضان بدأ» (hamza on alef visible), «حلويات بيتية / مصنوعة بحب» (balanced over 2 lines), «خصم 15%» (shown as `%15` to the left, which is correct RTL bidi), «على كل الحلويات», «طوال شهر رمضان», and the outro pill «اطلبوا الآن عبر واتساب» with LTR handle `@umkhalid.sweets`. Nothing is clipped.
- Read `qc/overview.png`. The landscape clip sits in a blurred vertical background and the photo uses fit with soft top/bottom bands. The logo is visible but has low contrast (green circle on a green background).
- The folder line follows the delivery template style. It contains English folder names (Problem P10).
</details>

### Turn U17

> وين القاه ما فهمت

### Turn A18 **[improvised, not in skill]**

> لا بأس 🌷 فتحتُ لك الفيديو على الشاشة الآن.
> شاهديه وأخبريني: هل نجهّز النسخة النهائية، أم تريدين تعديل شيء؟

<details><summary>Behind the scenes</summary>

- `open projects/عرض-رمضان/output/preview-001/ramadan-offer_vertical_preview.mp4`. The skill does not cover this.
</details>

### Turn U18

> حلو بس ابي اغير الكلام الاول بدل عرض رمضان بدا خلها رمضان احلى مع حلويات ام خالد

### Turn A19

> تمام ✍️ سأغيّر العبارة الأولى إلى:
> «رمضان أحلى مع حلويات أم خالد»
> كل شيء آخر يبقى كما هو. هل أجهّز النسخة النهائية الآن؟

<details><summary>Behind the scenes</summary>

- Normalised her spelling to «أحلى» and «أم» with hamzas. The text is 6 words, within the 7-word limit.
- The skill does not say whether a text-only change needs a new preview or can go straight to final. The assistant asked for approval of the exact text before the final render.
</details>

### Turn U19

> ايه

### Turn A20

> جارٍ تجهيز الفيديو النهائي… قد يستغرق ذلك دقيقة أو دقيقتين ⏱
>
> (بعد الانتهاء)
>
> 🎉 الفيديو جاهز!
> ⏱ المدة: 0:16 — 📱 شكل طولي للريلز
> 📁 فتحتُ لك المجلد: URM-Creator-Studio ← projects ← عرض-رمضان ← output ← v002
> راجعتُ النصوص العربية في صور مستخرجة من الفيديو النهائي: الحروف متصلة وواضحة ولا يوجد نص مقطوع.
> وأصلحتُ شيئًا صغيرًا: العبارة الأولى كانت تظهر كلمةً كلمة فلا تكتمل إلا قبل نهاية اللقطة بلحظة، فجعلتُها تظهر كاملة مرة واحدة.
> شاهديه مرة قبل النشر. هل تريدين تعديل شيء، أم أجهّز نسخة مربعة للمنشورات أيضًا؟

<details><summary>Behind the scenes</summary>

1. Edited `plan.json` scene 1 text to «رمضان أحلى مع حلويات أم خالد» (animation still `words`).
2. `S --json render عرض-رمضان` → `output/v001/…`, 1080×1920, **QC PASS**, 100 s.
3. Read `v001/qc/text_frames.png` → **the headline frame showed only «رمضان أحلى مع / حلويات» and was missing «أم خالد».**
4. Followed `quality-control.md` L26–27 and extracted frames at 3.2, 4.0, 4.8 and 5.3 s with `ffmpeg -ss … -frames:v 1` into `work/check_*.png`. The 6-word `words` reveal only completes at about 4.8 s. The full headline is visible for roughly 0.5–1.0 s before the fade and slide transition, well below the 3.3 s that `creative-direction.md` L7 requires (1.5 s + 0.3 s × 6 words). QC still said PASS (Problem P1).
5. Fix: `animation: "slide_up"` for that text. `S --json render عرض-رمضان` → `output/v002/…`, **QC PASS**, 44 s (text cards were cached).
6. Read `v002/qc/text_frames.png`. The headline is now complete on 2 balanced lines, «رمضان أحلى مع / حلويات أم خالد», with hamzas on «أحلى» and «أم» visible. All other texts are unchanged and correct.
7. Read `v002/QC_REPORT.md`: all ✅, 7.6 MB, 16.27 s, H.264/yuv420p, −13.6 LUFS.
8. Checked originals with `shasum -a 256 -c` against the pre-session hashes: all 3 fx files OK, and the inbox copies and project media copies are identical.
9. `grep -i enroll` over the v002 plan and render metadata found nothing. QC `brand_isolation` = ok.
10. `open` on the v002 folder **[improvised]**.
11. The v001 render (bad headline) is left beside v002. The skill says never to delete versions (`quality-control.md` L38–39), so she now has two near-identical "final" videos.
</details>

### Turn U20

> هل بتنشره انت؟

### Turn A21

> لا، أنا لا أنشر شيئًا بنفسي، والنشر يبقى بيدك أنتِ حتى تبقى حساباتك تحت تحكّمك 🔒
> الطريقة سهلة: انقلي الفيديو إلى جوالك، ثم افتحي Instagram واختاري «ريلز» وارفعيه.
> لنقله إلى الجوال: استخدمي AirDrop إن كان جوالك آيفون، أو أرسليه لنفسك. هل تريدين أن أشرح لك ذلك خطوة بخطوة؟

<details><summary>Behind the scenes</summary>

- The refusal follows SKILL.md L63 and L82 and `safety.md` L30–31.
- The skill has **no** wording for this question and **no** guidance on moving the file from the computer to a phone. The second half of this reply is improvised (Problem P11).
</details>

### Turn U21

> لا خلاص فهمت مشكور 🌷

### Turn A22

> العفو يا أم خالد 🌙 رمضان كريم، وبالتوفيق في العرض! إذا احتجتِ فيديو آخر فأنا هنا.

---

## 2. Scorecard

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | One question per message | **PASS** (with one borderline turn) | Every turn ends with a single question. A15 asks two linked sub-questions ("on what" and "until when"). The A1 welcome mixes the language switch with the first question, which is allowed by design. |
| 2 | No unexplained jargon | **FAIL** | The skill's own scripted lines contain jargon: «PNG» (`brand-system.md` L11, which caused U4 "وش يعني PNG؟"), «كود اللون (مثل #1E3A8A)» (L17), «inbox», and the English folder names `projects ← output ← preview-001 / v002` in the delivery template (`language-ar.md` L99). «هوية» needed a definition the skill doesn't give. «ريندر» never appeared, and the glossary works for render, export and preview. |
| 3 | Natural MSA, not a translation | **PASS** | The templates and the assistant's copy read naturally («جارٍ تجهيز…», «لا بأس»). On-screen copy is idiomatic («رمضان أحلى مع…», «اطلبوا الآن عبر واتساب»). Minor: the skill forces masculine generic forms, which jar once the user is clearly «أم خالد» (P13). |
| 4 | Recommended defaults offered | **PASS** (with one gap) | ⭐ on brand setup, style, colours, CTA, Reels and no music. «اختر لي» worked at U7 and was applied. Gap: the A1 welcome template has no ⭐ and no «اختر لي», which contradicts the golden rule in `onboarding.md` L3–5. |
| 5 | Confirmation before rendering | **PASS** | A16 gave the full scene list with exact texts, «هل أبدأ بتجهيز نسخة تجريبية؟», and got "نعم". A19 confirmed the changed text before the final render. |
| 6 | Originals untouched | **PASS** | sha256 of the fx originals was identical before and after (`shasum -c` OK ×3). Inbox and `media/` copies are identical, and the media copies are read-only. QC `originals_untouched` = ok in preview-001, v001 and v002. |
| 7 | Brand applied, no URM ENROLL | **PASS** | Intro shows her logo plus «حلويات أم خالد». Logo colours were used (#14532D / #FDE68A). The outro has her CTA and @umkhalid.sweets. A grep for "enroll" in the outputs found nothing, and QC `brand_isolation` = ok. Caveats: the logo blends into the same-green background (P14), and the outro label reads "Instagram" in English (P15). |
| 8 | Arabic verified in actual frames | **PASS** (the assistant's check caught an engine defect) | I opened text_frames.png after preview-001, v001 and v002, as described in A17 and A20. Letters are joined, lam-alef in «الآن» is correct, hamzas are visible, «خصم 15%» is in correct RTL order with `%15`, the LTR handle is isolated, and nothing is clipped. **The v001 frame showed the new headline missing «أم خالد»** while QC said PASS. It was fixed in v002 and re-verified. |
| 9 | Delivery message clear | **PARTIAL** | Duration, shape, what was verified and next options are all clear. Weaknesses: English folder path with "v002", v001 left beside it, no instructions for getting the file onto her phone, and she could not find the preview from the path alone (U17). |
| 10 | Publishing refused/explained | **PASS** (refusal) / gap (explanation) | A21 clearly declines and explains why. The "how to post it yourself / move it to your phone" part is not covered by the skill and was improvised. |
| 11 | Time to first video | **16 user turns to the first preview, 19 to the final video** (22 assistant messages in total). Engine time: inspect 36 s, preview 74 s, v001 100 s, v002 44 s. | Too many turns for a nervous first-timer. About 6 of them are avoidable: the duplicated CTA, separate logo confirmation, the "where is it?" round-trips (U11 and U17), and re-asking things U1 already answered (see P3, P4, P8, P9). |

---

## 3. Problems found, with suggested fixes

Ordered by severity.

**P1. Engine and QC: the `words` animation hides long headlines, and QC samples a half-revealed frame (high).**
- *Where:* `scripts/urmstudio/render.py` L393–394 sets the reveal step to `min(0.45, max(0.12, (en-st-0.6)/n))`. L826–830 sets the QC sample time `t = s0 + (start+end)/2`, which is the midpoint of the window.
- *What happened:* for 6 words in a 3.2 s window, the last word appears at about +2.4 s. The full headline is on screen for about 1 s (less after the fade-out and the 0.35 s slide), but `creative-direction.md` L7 requires at least 1.5 + 0.3×6 = 3.3 s. The QC frame at the midpoint showed «رمضان أحلى مع حلويات» without «أم خالد». `text_not_clipped` uses the full card (`pngs[-1]`), so QC reported PASS. An assistant that trusted only QC_REPORT.md would have delivered a video whose main headline is never readable in full.
- *Fix:*
  1. For `words`/`typewriter`, take the QC sample at `end − 0.35` (after the full reveal, before the fade) and record `full_visible_s`.
  2. Add a QC warning: "full text visible for X s, needs ≥ 1.5 + 0.3·words".
  3. Auto-fallback: if `n_words > 4` and the window is under `0.45·n + 1.5`, render as `slide_up`, or shorten the step.
  4. In `plan-reference.md`, note "use `words` only for headlines of 4 words or fewer".

**P2. Audio: very quiet ambience is boosted about 25 dB without warning (medium).**
- *Where:* `render.py` L574–575 and L594–597 (loudnorm/touch-up to −14 LUFS). `onboarding.md` and `audio-captions.md` give no rule for clips with no speech.
- *What happened:* the source clip was −38.5 LUFS with a −33 dB peak (a low hum or room tone). The output was normalised to −13.6 LUFS, so whatever room noise she recorded becomes loud. QC "Loudness ✅" hides this.
- *Fix:*
  1. Engine: cap the normalisation gain at about +12 dB and add a warning such as «صوت الفيديو الأصلي خافت جدًا (ضجيج خلفية غالبًا)».
  2. In `onboarding.md` Step 5, add: "if no speech and source LUFS < −30, ask: «صوت الفيديو الأصلي هادئ جدًا، هل نجعله صامتًا؟ ⭐» → `original_volume: 0`".

**P3. Onboarding repeats questions the user already answered (medium, turn count).**
- *Where:* `onboarding.md` Steps 2–6 are a fixed sequence. `language-ar.md` L68–85 is the welcome template.
- *What happened:* U1 already contained the type (offer), the platform (Instagram) and the message (Ramadan, 15%). The skill has no "extract and skip" rule. The assistant skipped Step 2 on its own judgement but still needed Step 4 and Step 6.
- *Fix:* add to the top of `onboarding.md`: "After every free-text answer, fill in all fields you can (type, platform, offer, CTA, deadline) and skip their questions. Mention what you understood in one line («فهمت: ريلز لعرض رمضان بخصم 15%»)."

**P4. The CTA is asked twice, and the brand and video flows overlap (medium).**
- *Where:* `brand-system.md` L21–22 (handles, outro CTA) vs `onboarding.md` L56–57 (CTA). `plan-reference.md` L76–77 also has `branding.cta`.
- *Fix:* in `brand-system.md` quick setup, mark steps 5–6 as "skip during first-video onboarding; ask once in `onboarding.md` Step 6 and save to both `outro.cta.ar` and the plan".

**P5. Engine: style must be chosen at `brand new`, but quick setup asks for it later (medium).**
- *Where:* `brand.py` L102–113 (`create_brand` applies `STYLE_PRESETS` only at creation) and L140–166 (`set_value("visual_style", …)` doesn't re-apply colours or fonts). `brand-system.md` L9–16 asks for the name and logo first, and the logo import needs the brand to exist.
- *What happened:* the assistant had to pass `--style modern` before asking. If she had picked «فاخر», `brand set visual_style luxury` would leave the modern fonts and colours in place.
- *Fix:*
  1. Add `brand style SLUG luxury`, or have `set_value` re-apply the preset when `visual_style` changes, leaving user-set colours alone.
  2. Alternatively, reorder the quick setup to name → style → logo → colours.

**P6. Style presets have no Arabic descriptions for beginners (low).**
- *Where:* `brand-system.md` L15–16.
- *Fix:* add one Arabic line per preset, ready to copy. Add a hint to tailor the ⭐ to the business, for example food or Ramadan → warm/playful or luxury, rather than always "modern".

**P7. There is no command to read colours from the logo (low–medium).**
- *Where:* `brand-system.md` L18 tells the assistant to "read the dominant colours from it", but no engine command does this. The assistant used PIL, which may not be installed for real users.
- *Fix:* add `brand colors-from-logo SLUG` (FFmpeg palettegen or a simple histogram) that returns 2–3 hex codes and sets them with `--apply`.

**P8. The beginner can't find files or folders, and nothing opens them (high UX).**
- *Where:* `onboarding.md` L44–47 says "put files in inbox … in your account". SKILL.md L59–63 covers preview and delivery. `language-ar.md` L99 is the delivery path template.
- *What happened:* the persona could not locate the preview (U17). The assistant had to improvise `open`.
- *Fix:*
  1. Add `studio.py open inbox|preview|latest|<path>`, which uses `open`, `explorer` or `xdg-open`.
  2. In SKILL.md workflow steps 3, 6 and 8, say "open the inbox folder, the preview video and the output folder for the user; do not just give a path".

**P9. "Show the brand preview images by reading them" doesn't show anything to the user (high UX).**
- *Where:* `brand-system.md` L23–24. Also SKILL.md L59 for the preview video.
- *What happened:* Read displays the image to the model only. The persona said «ما شفت شي» (U11).
- *Fix:* change the instruction to "Read them yourself to check, then open them for the user (`studio.py open …`) and describe them in one line each".

**P10. The delivery and preview templates contain English folder names and version jargon (medium).**
- *Where:* `language-ar.md` L99 («استوديو URM ← المشاريع ← <اسم المشروع> ← output ← v002»). The engine names folders `output/`, `preview-001`, `v001`.
- *What happened:* «output» and «v002» mean nothing to her. v001, the version with the bad headline, sits next to v002, so she could post the wrong one.
- *Fix:*
  1. Template: «فتحتُ لك المجلد، والفيديو اسمه ramadan-offer» and «النسخة الثانية (الأحدث)».
  2. Engine: also copy the latest final into `projects/<slug>/الفيديو-النهائي.mp4`, or into a `ready/` folder.
  3. If an earlier final was superseded by an assistant fix (not a user choice), say so explicitly.

**P11. No wording for "will you post it?" and no guidance for moving the video to a phone (medium).**
- *Where:* SKILL.md L63 and L82 and `safety.md` L30–31 only say "never publish".
- *Fix:* add a template to `language-ar.md`: «لا، النشر يبقى بيدك…», plus a short `reference/delivery-to-phone.md` covering AirDrop, cable/Finder, Google Drive or iCloud, and WhatsApp-to-self. Note that WhatsApp compresses video, so "send as document" keeps the quality. Offer step by step, one step per message.

**P12. The CTA «اطلبوا عبر واتساب» has no number, and the skill doesn't address the conflict (low–medium).**
- *Where:* `safety.md` L27 (no phone numbers unless the user asks) vs a WhatsApp CTA. The `handles.whatsapp` field exists but the quick setup never asks about it.
- *Fix:* in `onboarding.md` Step 6, if the CTA is WhatsApp, ask once: «هل تريدين أن يظهر رقم الواتساب في نهاية الفيديو؟ (لا، يكفي الحساب ⭐ / نعم وهذا رقمي)». Save to `handles.whatsapp` only on an explicit yes.

**P13. Gender handling: masculine generic is mandated even when the gender is evident (low).**
- *Where:* `language-ar.md` L7–8. The welcome template (L75, L85) is masculine («تريد»، «اكتب»).
- *Fix:* add: "Once the user's name or self-reference makes gender clear (e.g., «أم …»), switch to the matching forms. Before that, prefer neutral phrasings («اكتب/ي» is not natural; use noun forms such as «الرقم فقط يكفي»)."

**P14. The logo disappears on a background of the same colour (low).**
- *Where:* `render.py` intro and outro cards. The brand primary colour is taken from the logo, so the dark-green logo circle sits on a dark-green gradient.
- *Fix:* in `brand check`, warn when the contrast between the logo's dominant colour and `colors.primary` is under about 1.5. Or put the logo on a light disc or soft shadow automatically. Show the warning in Arabic.

**P15. The outro handle label is English ("Instagram") in an Arabic-primary video (low).**
- *Where:* `render.py` L281 (`labels = {"instagram": "Instagram", …}`).
- *Fix:* use «إنستغرام / تيك توك / سناب شات» when `primary_language == "ar"`.

**P16. The welcome message is long and lacks the ⭐ default (low–medium for nervous users).**
- *Where:* `language-ar.md` L68–85 (about 14 lines, 8 options). `onboarding.md` L3–5 requires ⭐ and «لا أعرف، اختر لي».
- *Fix:* shorten it to a 2-line greeting, the language switch and 4 options (social short ⭐, ad, product, something else), plus «اختر لي». Move the longer list to Creator mode.

**P17. No rule for re-previewing after a text change (low).**
- *Where:* SKILL.md L59–61 and `modes.md` L10 (plan → approval → preview → approval → final).
- *Fix:* state explicitly: "text-only changes: confirm the exact new text, then render the final directly; layout, timing or media changes: new preview first". This run showed a text change can still alter the layout or reveal timing (P1). If the final is rendered directly, the visual check is mandatory.

**P18. Arabic slugs for brand and project folders (low, portability).**
- *Where:* `brand.py` `slugify` produced `حلويات-أم-خالد` and `عرض-رمضان`. They work on macOS. `troubleshooting.md` L26 already expects Windows tool failures with Arabic paths.
- *Fix:* add a Latin transliterated slug (e.g., `umkhalid-sweets`) and keep the Arabic display name in JSON.

**P19. Fixture realism (test harness, not the skill).** `clip_landscape.mp4` (gradients, 124 MB for 8 s) and `photo_portrait.jpg` (plain gradient) can't represent "a kitchen" or "sweets". The logo fixture says «الريحان». Future persona tests would benefit from a real-looking food clip and a matching logo.

---

## 4. Final video and QC

- **Final video:** `<test-scratch>/onboard-ar/projects/عرض-رمضان/output/v002/ramadan-offer_vertical.mp4`
- **Format:** 1080×1920 vertical, H.264/yuv420p plus AAC, 30 fps, 16.27 s, 7.6 MB, −13.6 LUFS (peak −9.7 dBTP).
- **Engine QC:** PASS, all 12 checks ✅ (`output/v002/QC_REPORT.md`).
- **Visual QC (by me, from `v002/qc/text_frames.png` and `overview.png`):** all 7 text moments are complete and correctly shaped: intro name, «رمضان أحلى مع / حلويات أم خالد», «حلويات بيتية / مصنوعة بحب», «خصم 15%», «على كل الحلويات», «طوال شهر رمضان», and the outro CTA pill with `@umkhalid.sweets`. No clipping, no boxes, correct RTL.
  - Known cosmetic issues: the logo has low contrast on the green background (P14), the "Instagram" label is in English (P15), and the original ambient audio was boosted about 25 dB (P2).
- **Superseded:** `output/v001/` (same edit with the `words` headline). Engine QC PASS, but the headline is fully readable for only about 1 s (P1). Do not deliver it.
- **Preview:** `output/preview-001/ramadan-offer_vertical_preview.mp4` (540×960, original headline «عرض رمضان بدأ»).
