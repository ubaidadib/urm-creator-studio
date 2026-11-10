# Arabic typography & right-to-left video

## How the engine renders Arabic (why it is correct)
Every piece of on-screen text is laid out by a headless Chromium browser (HarfBuzz shaping + ICU bidi) into
a transparent PNG the size of the video frame, then composited by FFmpeg. This gives: connected letter
forms (initial/medial/final/isolated), lam-alef ligatures (لا، لأ، لإ، لآ), the Allah ligature, harakat
and shadda placement, correct right-to-left order, and correct mixed Arabic/English ordering.
**Never** use FFmpeg drawtext/subtitles filters for Arabic, never reverse strings, never "fix" order by hand.

## Rules applied automatically
- Base direction comes from the first strong letter of each text (`unicode-bidi: plaintext`).
- URLs, e-mails, @handles, #hashtags, phone numbers and the brand's Latin name are isolated as LTR islands
  (`<bdi dir="ltr">`) and never broken across lines → «تابعونا على @brand_x» stays intact.
- `letter-spacing: 0` for Arabic (spacing breaks the joins). No uppercase transforms. No kashida justification.
- Line-height 1.55 for Arabic (dots, hamza, harakat need room); 1.25 for Latin-only text.
- Lines are balanced (`text-wrap: balance`) and text auto-shrinks to fit inside the safe area; it is never
  truncated. Minimum size is 55 % of the role size — if text still does not fit, shorten it.
- Arabic font first in the font stack for RTL text, Latin font first for LTR text; browsers fall back per
  character, so mixed text uses the right font for each script.
- Numerals: `western` (0123) or `arabic_indic` (٠١٢٣) per brand. With `arabic_indic`, digits inside Arabic
  words and bare numbers are converted; digits inside Latin words (iPhone 15) are not.
- Lower thirds align to the right edge for Arabic, left for English. Slide transitions move in the reading
  direction (RTL videos slide the other way). Word-by-word reveals appear right-to-left with stable layout.

## Things you must do as the author
- Write natural Arabic; check spelling, hamzas (أ/إ/ا/آ), taa marbuta (ة/ه), alef maqsura (ى/ي).
- Pick ONE numeral system per text (QC warns when ٢٠ and 8 are mixed). Follow the brand setting.
- Punctuation: Arabic comma «،», semicolon «؛», question mark «؟». The exclamation mark is shared «!».
  A sentence-final mark sits at the left end in RTL — that is correct, do not move it.
- Percent: «٢٠٪» with Arabic digits, «20%» with Western digits. Inside an Arabic sentence the sign is
  displayed on the left of the number («%20» / «٪٢٠» visually) — that is the correct Unicode result (rule W2)
  and the usual look on Arabic news sites, not a bug. If a brand insists on the Western look «20%», write
  the number with left-to-right marks: `\u200e20%\u200e`.
- Mixed sentences: keep English words inside the sentence, not at the very start/end when possible, so the
  sentence direction is unambiguous. If a line must start with an English word but is Arabic overall,
  start it with an Arabic word or split the line.
- Diacritics (tashkeel): use only where meaning is ambiguous or for poetry/Quranic text (check with user).
  Partial tashkeel like «تُحمَّص» is fine.
- Quranic verses, hadith or religious phrases: ask the user to provide/approve exact text; render in Amiri
  or Noto Naskh; never animate word-by-word; never place over music without asking.

## Caption specifics
- Max ~42 characters per line, 2 lines, ≥ 0.8 s per cue, ≤ 17 characters per second.
- Box style (semi-transparent black) is the most readable over busy footage; outline style for clean shots.
- Sidecar files: `captions.srt` and `.vtt` include right-to-left marks (U+200F) around Arabic lines so
  players keep punctuation on the correct side. Upload these to YouTube/Facebook as subtitle files.

## Verification (mandatory before claiming Arabic is correct)
1. After each render, open `output/vNNN/qc/text_frames.png` with the Read tool.
2. Check every Arabic text in the image:
   - letters are joined (no isolated forms in the middle of words, no boxes ☐ or question marks)
   - words read right-to-left in the intended order; numbers and English words in the right place
   - nothing cut at the edges; dots and harakat visible and not clipped by the line above/below
   - text is clear of the top/bottom app areas and not covering faces or other text
3. If anything is wrong, fix the plan (shorter text, other position, other font) and re-render. Only then
   tell the user «راجعتُ النصوص العربية في صور مستخرجة من الفيديو النهائي…».
4. For a new custom font, render a test card first:
   `card "أبجد هوز حطي كلمن سعفص قرشت ثخذ ضظغ — لا لأ ﷲ ٠١٢٣٤٥٦٧٨٩ ABC 123" --brand <slug> --bg --out test.png`.
