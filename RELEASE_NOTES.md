# URM Creator Studio v1.0.0: First Public Release

**🌐 [English](#english) · [العربية](#arabic)**

<a id="english"></a>

## English

URM Creator Studio is a free, beginner-friendly, **Arabic-first** video studio that runs as a skill inside
Claude Code. You describe the video you want, in Arabic or English, and it produces a ready-to-post video
with your own branding. Made and distributed by URM ENROLL.

### Highlights
- **Conversational onboarding**: one simple question at a time; Beginner, Creator and Pro modes; Arabic by
  default with a one-click switch to English.
- **Correct Arabic**: connected letters, right-to-left layout, mixed Arabic/English, Arabic-Indic or Western
  numerals, Arabic captions, titles and lower thirds. Verified in exported frames.
- **Your brand**: logo or typographic wordmark, colours (described in words or read from your logo), six style
  presets, bundled Arabic fonts, handles, intro/outro, watermark. Your videos never carry URM ENROLL branding.
- **Video tools**: clips and photos with motion, title cards, animated text, transitions, lower thirds,
  burned-in captions plus SRT/VTT files, music with automatic ducking, loudness to −14 LUFS, and
  vertical/portrait/square/landscape exports.
- **Optional local speech-to-text** (whisper.cpp) with mandatory human review.
- **Safety**: originals never modified, versioned exports, automatic quality checks, nothing published for you.

### Requirements
Claude Code with an eligible paid Claude plan (or Anthropic API account) and internet access; Python 3.8+;
FFmpeg; Google Chrome or Microsoft Edge. Optional: whisper.cpp.

### Install
1. Download `URM-Creator-Studio-v1.0.0.zip` below and unzip it.
2. Mac: double-click `Install-macOS-English.command`. Windows (unverified): `Install-Windows-English.bat`.
   Linux (unverified): `bash install.sh --en`.
3. Open Claude Code and type: *Hi, I want to make a video*.

### Known limitations
- Tested on **macOS only**. Windows and Linux installers have not been run on real machines yet.
- Arabic speech-to-text can make confident mistakes, so always review subtitles.
- iPhone HDR footage may show colour shifts (no full HDR tone-mapping).
- Built-in narration: macOS only, with explicit consent.
- Speech-to-text requires an optional extra install (about 1.6 GB model).
- Beginner onboarding was tested in simulated sessions, not yet with real users.

### Privacy
The video engine runs locally and uploads nothing. Your chat with Claude, and images the assistant opens to
check your video, are processed by Anthropic.

### License
MIT (code), SIL OFL 1.1 (bundled fonts). See `LICENSE` and `USAGE-TERMS.md`.

### Verify your download
```bash
shasum -a 256 URM-Creator-Studio-v1.0.0.zip   # macOS / Linux
certutil -hashfile URM-Creator-Studio-v1.0.0.zip SHA256   # Windows
```
Compare with `URM-Creator-Studio-v1.0.0.zip.sha256`.

---

<a id="arabic"></a>

<div dir="rtl" lang="ar">

## العربية

استوديو URM للإبداع استوديو فيديو مجاني وسهل للمبتدئين، **يتحدث العربية أولًا**، ويعمل داخل Claude Code. تصف
الفيديو الذي تريده بالعربية أو الإنجليزية، فتحصل على فيديو جاهز للنشر بهويتك أنت. من صنع URM ENROLL وتوزيعها.

### أبرز المزايا

- **محادثة سهلة**: سؤال بسيط واحد في كل مرة، وثلاثة أوضاع (المبتدئ والمبدع والمحترف)، والعربية هي اللغة الافتراضية
  مع إمكانية التحويل إلى الإنجليزية.
- **عربية صحيحة**: حروف متصلة، واتجاه من اليمين إلى اليسار، وخلط سليم بين العربية والإنجليزية، وأرقام عربية أو غربية،
  وترجمة وعناوين وأشرطة أسماء عربية، وكلها تُراجَع في صور من الفيديو النهائي.
- **هويتك أنت**: الشعار أو اسمك مكتوبًا بخط جميل، والألوان (تصفها بكلماتك أو تُؤخذ من شعارك)، وستة أساليب جاهزة،
  وخطوط عربية مرفقة، وحساباتك، والمقدمة والخاتمة. فيديوهاتك لا تحمل هوية URM ENROLL أبدًا.
- **أدوات الفيديو**: مقاطع وصور متحركة، وبطاقات عناوين، ونصوص متحركة، وانتقالات، وترجمة مكتوبة داخل الفيديو مع ملفات
  ترجمة منفصلة، وموسيقى تنخفض عند الكلام، ومستوى صوت مناسب للمنصات، وأشكال طولية وعمودية ومربعة وعرضية.
- **تحويل الكلام إلى نص على جهازك** (اختياري)، مع مراجعة إلزامية منك.
- **الأمان**: ملفاتك الأصلية لا تتغير، وكل نسخة تُحفظ منفصلة، وفحوص جودة تلقائية، ولا يُنشر أي شيء نيابةً عنك.

### المتطلبات

برنامج Claude Code مع اشتراك مدفوع مناسب في Claude (أو حساب Anthropic API) واتصال بالإنترنت، وبايثون 3.8 أو أحدث،
وبرنامج FFmpeg، ومتصفح Google Chrome أو Microsoft Edge. واختياريًا: whisper.cpp.

### التثبيت

1. نزّل الملف `URM-Creator-Studio-v1.0.0.zip` من الأسفل، ثم فكّ ضغطه.
2. في ماك: انقر مرتين على `Install-macOS.command`. في ويندوز (لم يُجرَّب بعد): `Install-Windows.bat`.
3. افتح Claude Code واكتب: «مرحبًا، أريد صنع فيديو».

### حدود هذا الإصدار

- جُرّب على **ماك فقط**، ولم يُجرَّب مثبّتا ويندوز ولينكس بعد على أجهزة حقيقية.
- تحويل الكلام العربي إلى نص قد يخطئ حتى عندما يبدو واثقًا، لذا راجع الترجمة دائمًا.
- مقاطع iPhone المصوّرة بتقنية HDR قد تتغير ألوانها قليلًا.
- التعليق الصوتي المدمج يعمل على ماك فقط، وبموافقتك الصريحة.
- تحويل الكلام إلى نص يحتاج تثبيتًا إضافيًا اختياريًا (ملف نموذج حجمه نحو 1.6 غيغابايت).
- جُرّبت تجربة المبتدئين بجلسات محاكاة، ولم تُجرَّب بعد مع مستخدمين حقيقيين.

### الخصوصية

محرّك الفيديو يعمل على جهازك ولا يرفع أي شيء. أما محادثتك مع Claude والصور التي يفتحها المساعد لمراجعة الفيديو
فتعالجها شركة Anthropic.

### الترخيص

البرنامج بترخيص MIT، والخطوط المرفقة بترخيص SIL OFL 1.1. راجع الملفين `LICENSE` و`USAGE-TERMS.ar.md`.

</div>
