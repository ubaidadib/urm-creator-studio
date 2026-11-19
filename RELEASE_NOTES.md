# URM Creator Studio v1.1.0: Creative-Led Video Production

**🌐 [English](#english) · [العربية](#arabic)**

<a id="english"></a>

## English

URM Creator Studio is a free, beginner-friendly, **Arabic-first** video studio that runs as a skill inside
Claude Code. You describe the video you want, in Arabic or English, and it produces a ready-to-post MP4 on your
own computer. Made and distributed by URM ENROLL.

### What's new in 1.1.0
**Start from just an idea.** No logo, footage, photos or music? Describe the video you want, and the studio
makes a finished, animated video:

- **Story and words:** a short concept, an opening hook, the on-screen words and a clear call to action. You
  see and approve the scene list before anything is made.
- **Animated scenes:** 11 scene designs, including:
  - headlines, floating words and a globe;
  - benefit cards with icons, number counters and a progress path;
  - a before/after line and a quote;
  - a photo showcase, a call to action and a logo reveal.

  The background moves throughout, the camera moves gently, and designed transitions join the scenes. It is
  **not** a slideshow.
- **Correct Arabic:** letters join, the layout runs right to left, and Arabic and Latin text mix correctly in
  the same scene.
- **A look and a name mark:** 8 visual styles for businesses without a brand. If you have no logo, the studio
  makes a temporary mark from your name that you can replace later. If you have a brand, the animated scenes
  use your colours, fonts and logo.
- **Original music:** composed on your computer for each video, with sound effects timed to the animation. No
  licence is needed. Your own licensed music always takes priority.

**Three ways to make a video.** The studio chooses the way from what you have:

| Mode | What it is |
|---|---|
| **Your own material** (asset-led) | Works as in 1.0.x. |
| **Just an idea** (creative-led) | The studio designs every scene. |
| **Mixed** | Your clips and photos combined with designed scenes. Footage that doesn't fill the frame sits on a background in the video's own colours. |

**More finished files** come with every video:

- a cover image;
- a subtitle file of the on-screen words;
- `production.json`, which records how the video was made and where every element came from: your files,
  studio graphics and music, or an AI or stock service you chose to use. It contains no folder or account names.

**Stronger automatic checks** on every video:

- the picture keeps moving, and an idea-only video is not a slideshow;
- the file plays without errors, and the picture runs to the end;
- no black frames;
- narration is never cut off;
- no accidental silence.

**More reliable:** stopping a render cleans up after itself, and Macs with 8 GB of memory render at a safe pace.

### Locally made, not AI video
- **Made on your computer:** the animated scenes and the soundtrack are drawn and composed there by the studio's
  own engine.
- **Not AI-generated video:** no AI image, video or music service is included or needed.
- **Optional services:** if you choose to use an AI or stock service you have connected to Claude, your request
  goes to that company under its own terms and prices, and the studio records the provider and licence with the
  video.

### Requirements
- **Claude Code** with an eligible paid Claude plan (or an Anthropic API account) and internet access.
- **macOS 12 or later** (tested on an Apple-silicon Mac with 8 GB of memory).
- **Python 3.8+** and **FFmpeg**: the installer checks them and offers to install FFmpeg.
- **Google Chrome or Microsoft Edge**, used in the background to draw text and animated scenes.
- **Optional:** whisper.cpp for speech-to-text on your computer.

### Install
1. Download **`URM-Creator-Studio-v1.1.0.zip`** below (under **Assets**, not "Source code") and unzip it.
2. Mac: double-click `Install-macOS-English.command` (Arabic messages: `Install-macOS.command`). If macOS
   blocks it: right-click → **Open** → **Open**.

   Windows (not yet verified): `Install-Windows-English.bat`. Linux (not yet verified): `bash install.sh --en`.
3. Restart Claude Code and type: *Hi, I want to make a video*.

**Upgrading from 1.0.x:** install over your current version the usual way. The installer keeps a backup of the
previous version. It leaves your brands and projects unchanged, and only re-applies the language you choose for
the studio. Videos made with your own footage work as before.

### Verify your download
```bash
shasum -a 256 URM-Creator-Studio-v1.1.0.zip               # macOS / Linux
certutil -hashfile URM-Creator-Studio-v1.1.0.zip SHA256   # Windows
```
Compare the result with `URM-Creator-Studio-v1.1.0.zip.sha256`.

### Good to know
- **Render time:** an animated 30-second video takes about 3–4 minutes on a Mac with 8 GB of memory. A preview
  takes about 1–2 minutes.
- **Studio music:** it is synthesised, so it is simpler and more even than a professionally produced track.
- **Your words:** in idea-only videos the assistant writes the words for you. Read them before posting,
  especially the Arabic wording and any facts or prices.
- **Local page:** animated scenes need Chrome or Edge to open a temporary page on your own computer
  (`127.0.0.1`). Security software that blocks local connections stops them. See the troubleshooting guide.
- **Platforms:** tested on **macOS only**. The Windows and Linux installers have not been run on real machines
  yet.
- **Speech-to-text:** Arabic speech-to-text can make confident mistakes, so always review subtitles. It
  requires an optional extra install (a model of about 1.6 GB).
- **iPhone HDR:** footage may show slight colour shifts.
- **Built-in narration:** macOS only, and only with your explicit consent.
- **Beginner testing:** onboarding was tested in simulated sessions, not yet with real users.

### Privacy
- **On your computer:** the video engine uploads nothing.
- **Processed by Anthropic:** your chat with Claude, and any images the assistant opens to check your video.
- **Never automatic:** the studio never posts anything for you.

### License
MIT (code), SIL OFL 1.1 (bundled fonts). See `LICENSE`, `THIRD_PARTY_NOTICES.md` and `USAGE-TERMS.md`.

Earlier versions, including 1.0.1, remain available on the releases page. Full history: `CHANGELOG.md`.

---

<a id="arabic"></a>

<div dir="rtl" lang="ar">

## العربية

استوديو URM للإبداع استوديو فيديو مجاني وسهل للمبتدئين، **يتحدث العربية أولًا**، ويعمل داخل Claude Code. تصف
الفيديو الذي تريده بالعربية أو الإنجليزية، فتحصل على فيديو جاهز للنشر يُصنع على جهازك. من صنع URM ENROLL وتوزيعها.

### ما الجديد في 1.1.0

**ابدأ بفكرة فقط.** لا شعار ولا لقطات ولا صور ولا موسيقى؟ صِف الفيديو الذي تريده، فيصنع لك الاستوديو فيديو متحركًا كاملًا:

- **القصة والكلمات:** فكرة قصيرة، وبداية تشدّ الانتباه، والنصوص على الشاشة، ودعوة واضحة في النهاية. وترى قائمة
  المشاهد وتوافق عليها قبل أن يبدأ أي شيء.
- **مشاهد متحركة:** ١١ تصميمًا للمشاهد، منها العناوين، والكلمات العائمة، والكرة الأرضية، وبطاقات المزايا بأيقونات،
  وعدّادات الأرقام، ومسار التقدّم، والمقارنة بين قبل وبعد، والاقتباس، وعرض الصور، والدعوة الختامية، وظهور الشعار.
  الخلفية تتحرك طوال الوقت، والكاميرا تتحرك بهدوء، وانتقالات مصمَّمة تصل بين المشاهد. وهو **ليس** عرض شرائح.
- **عربية صحيحة:** حروف متصلة، واتجاه من اليمين إلى اليسار، وخلط سليم بين العربية والحروف اللاتينية في المشهد نفسه.
- **أسلوب وعلامة باسمك:** ٨ أساليب بصرية للمشاريع التي ليس لها هوية. وإن لم يكن لديك شعار، يصنع الاستوديو علامة
  مؤقتة من اسمك تستبدلها لاحقًا. وإن كانت لديك هوية، تستخدم المشاهد المتحركة ألوانك وخطوطك وشعارك.
- **موسيقى أصلية:** تُؤلَّف على جهازك لكل فيديو، مع مؤثرات صوتية متزامنة مع الحركة، ولا تحتاج إلى ترخيص.
  وموسيقاك المرخّصة لها الأولوية دائمًا.

**ثلاث طرق لصنع الفيديو** يختار الاستوديو بينها بحسب ما لديك:

| الطريقة | ما هي |
|---|---|
| **موادك الخاصة** | تعمل كما في 1.0.x. |
| **فكرة فقط** | يصمّم الاستوديو كل المشاهد. |
| **مزيج** | مقاطعك وصورك مع مشاهد مصمَّمة. واللقطات التي لا تملأ الإطار توضع على خلفية بألوان الفيديو نفسه. |

**ملفات إضافية مع كل فيديو:**

- صورة غلاف؛
- ملف ترجمة للنصوص الظاهرة على الشاشة؛
- الملف <code dir="ltr">production.json</code> الذي يسجّل كيف صُنع الفيديو ومن أين جاء كل عنصر فيه، دون أي أسماء
  مجلدات أو حسابات.

**فحوص تلقائية أقوى** لكل فيديو:

- الصورة تبقى متحركة، والفيديو المصنوع من فكرة ليس عرض شرائح؛
- الملف يعمل دون أخطاء، والصورة تستمر حتى النهاية؛
- لا إطارات سوداء؛
- التعليق الصوتي لا يُقطع أبدًا؛
- لا صمت غير مقصود.

**أكثر موثوقية:** إيقاف التصدير ينظّف ما بعده، وأجهزة الماك بذاكرة ٨ غيغابايت تعمل بوتيرة آمنة.

### يُصنع على جهازك، وليس فيديو بالذكاء الاصطناعي

- **على جهازك:** المشاهد المتحركة والموسيقى يرسمها ويؤلّفها محرّك الاستوديو نفسه.
- **ليس فيديو بالذكاء الاصطناعي:** لا تتضمن الحزمة أي خدمة ذكاء اصطناعي للصور أو الفيديو أو الموسيقى، ولا تحتاج إليها.
- **الخدمات الاختيارية:** إن اخترت استخدام خدمة ذكاء اصطناعي أو مكتبة وصلتها بـ Claude، يُرسَل طلبك إلى تلك الجهة
  وفق شروطها وأسعارها، ويسجّل الاستوديو اسم الجهة والترخيص مع الفيديو.

### المتطلبات

- برنامج **Claude Code** مع اشتراك مدفوع مناسب في Claude (أو حساب Anthropic API) واتصال بالإنترنت.
- **ماك بنظام 12 أو أحدث** (تمت تجربته على ماك بمعالج Apple وذاكرة ٨ غيغابايت).
- **بايثون 3.8 أو أحدث** وبرنامج **FFmpeg**.
- متصفح **Google Chrome أو Microsoft Edge**.
- **اختياريًا:** whisper.cpp.

### التثبيت

1. نزّل الملف <code dir="ltr">URM-Creator-Studio-v1.1.0.zip</code> من الأسفل (من قسم **Assets**، لا "Source code")، ثم فكّ ضغطه.
2. في ماك: انقر مرتين على <code dir="ltr">Install-macOS.command</code>. في ويندوز (لم يُجرَّب بعد): <code dir="ltr">Install-Windows.bat</code>.
3. أعد تشغيل Claude Code واكتب: «مرحبًا، أريد صنع فيديو».

**الترقية من 1.0.x:** ثبّت فوق الإصدار الحالي بالطريقة المعتادة. يحتفظ المثبّت بنسخة احتياطية من الإصدار السابق،
ولا يغيّر هوياتك ولا مشاريعك.

### حدود هذا الإصدار

- **مدة التصدير:** فيديو متحرك مدته ٣٠ ثانية يحتاج نحو ٣–٤ دقائق على ماك بذاكرة ٨ غيغابايت.
- **الموسيقى الأصلية:** مركّبة، فهي أبسط وأكثر ثباتًا من موسيقى منتجة في استوديو.
- **نصوصك:** في الفيديو المصنوع من فكرة يكتب المساعد النصوص، فاقرأها قبل النشر.
- **الصفحة المحلية:** تحتاج المشاهد المتحركة إلى صفحة محلية على جهازك (<code dir="ltr">127.0.0.1</code>)، وقد
  توقفها برامج الحماية.
- **أنظمة التشغيل:** جُرّب على **ماك فقط**.
- **تحويل الكلام العربي إلى نص:** قد يخطئ حتى عندما يبدو واثقًا، فراجع الترجمة دائمًا.
- **تجربة المبتدئين:** جُرّبت بجلسات محاكاة، لا مع مستخدمين حقيقيين بعد.

### الخصوصية

- **على جهازك:** محرّك الفيديو لا يرفع أي شيء.
- **تعالجها Anthropic:** محادثتك مع Claude والصور التي يفتحها المساعد لمراجعة الفيديو.
- **لا شيء تلقائي:** لا يُنشر أي شيء نيابةً عنك.

### الترخيص

البرنامج بترخيص MIT، والخطوط المرفقة بترخيص SIL OFL 1.1. راجع الملفين `LICENSE` و`USAGE-TERMS.ar.md`.

</div>
