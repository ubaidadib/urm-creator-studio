# Creative direction

## Principles
1. **Hook in the first 2 seconds** — movement + a short, specific line (a benefit, a question, a number).
2. **One message per video.** Everything supports it.
3. **Real footage first.** Authentic people and places beat effects. Never generate synthetic people.
4. **Readable text**: ≤ 7 words per headline, on screen ≥ 1.5 s + 0.3 s per word, high contrast.
5. **Rhythm**: social cuts every 1.5–3 s; brand films 3–6 s; let emotional shots breathe.
6. **End with one clear action** (CTA) and the brand.
7. **Sound on and off**: captions for any speech; key info also as text.
8. **Respect the culture of the audience**: modest, inclusive imagery; correct Arabic; avoid slang unless the
   brand voice uses it; check religious/seasonal context (Ramadan, Eid, National Days) when relevant.

## Analysing footage before planning
Run `inspect … --sheet`, look at each contact sheet, then note per clip: subject, quality (shaky, dark,
blurry), best moments (use `cuts` timestamps), speech or not, orientation. Pick the strongest 2–3 s for the
hook. Avoid: first/last 0.5 s of phone clips (shake), blurry frames, unflattering moments of real people.
Tell the user honestly if footage is too dark/short and suggest what to film (with simple tips: «صوّر
بالطول، قرب النافذة، ثبّت الجوال بيديك الاثنتين، ٥ ثوانٍ لكل لقطة»).

## Recipes (structure → durations → text → style)

Text animation `words` (word-by-word) only for headlines of ≤ 5 words; the engine switches longer ones to
`slide_up` when there isn't time to keep the full text readable for 1.5 s + 0.3 s per word.

**social_short (Reels/TikTok/Shorts, 15–30 s, vertical)**
Hook (0–2 s, bold text + best shot) → 3–5 quick scenes with one idea each → CTA + brand (3 s).
Animations: words / slide_up; transitions: slide or fade 0.3 s; captions on if speech.

**ad (15–30 s)**
Problem or desire (2–3 s) → product/service as the answer (6–10 s) → proof or offer (3–5 s: price, discount,
review) → CTA (3 s) → brand outro. Text uses numbers and urgency honestly (no false claims).

**brand_intro (45–90 s, landscape + vertical cut)**
Logo intro → who we are (one line) → what we do (3 scenes) → why us (2–3 values) → people/place →
tagline → contact outro. Lower thirds for people. Calm transitions (fade/dissolve 0.5 s), music bed.

**product (20–40 s)**
Hero shot → 3 features (one per scene, text: feature → benefit) → in-use shot → price/offer → CTA.
Images: zoom_in / pan motion. Keep backgrounds clean.

**explainer / educational (30–90 s)**
Question hook → "3 steps" structure with numbered titles (١، ٢، ٣ or 1, 2, 3 per brand numerals) → recap →
CTA (follow for more). Captions essential. Title scenes as chapter cards.

**talking_head**
Trim silences and false starts (with user approval), keep natural pauses. Punch-in effect: alternate
`fill` with slight `focus` changes between takes. Captions burned in. Lower third with name/role at 1–5 s.
Never alter the speaker's face or voice.

**event highlights (30–60 s)**
Atmosphere opener (wide shot) → arrivals/people → key moments → crowd reactions → closing wide → date/
thanks card. Music-driven cuts on beats, short clips (1–2 s). Ask consent status for identifiable guests.

**long-form (2–15 min, landscape)**
Chapter title cards, lower thirds, consistent caption style, music only in intro/outro and transitions.
Render a preview of the first minute first. Keep scene count manageable (split into parts if > 60 scenes).

**campaign (series)**
Same brand intro/outro and caption style, varying hooks. Create one project per video, reuse plan structure;
deliver as a set (vertical + square). Name outputs consistently with `output_name`.

**personal**
Warm and simple: photos with zoom motion, a title card, soft fades, optional music the user owns.

## Arabic copywriting for video
- Write for the eye: short noun phrases («افتتاح الفرع الجديد»، «خصم ٢٠٪ لأسبوع واحد»).
- Imperatives for CTAs: «اطلب الآن»، «زورونا اليوم»، «احجز موعدك»، «تابعونا لمزيد من النصائح».
- Avoid literal English calques («قم بالضغط على» → «اضغط»).
- Dialect: MSA by default; if the user writes in dialect and wants that voice, mirror their wording exactly.
- English brand names stay in English letters; do not transliterate unless the brand has an Arabic name.
- Always show final on-screen text to the user for approval; they know their audience.

## Creative choices by brand personality
| Personality | Pace | Transitions | Text animation | Fonts |
|---|---|---|---|---|
| luxury/elegant | slow (3–5 s) | fade/dissolve 0.6 s | fade, zoom (subtle) | Amiri / Noto Naskh |
| modern/tech | medium | slide 0.35 s | slide_up, words | Cairo / Noto Kufi |
| playful/youth | fast (1–2 s) | slide, circleopen | words, zoom | Cairo bold |
| corporate/trust | medium-slow | fade 0.4 s | fade, slide_side | Noto Kufi / Tajawal |
| minimal | medium | fade / none | fade | Tajawal |
| bold/sale | fast | slide, fadeblack | zoom, words | Cairo 800 |
