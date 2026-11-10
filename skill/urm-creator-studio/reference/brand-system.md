# Brand system

Brands live in the user's workspace, never in the skill folder:
`~/URM-Creator-Studio/brands/<slug>/brand.json` + `assets/` (copied logo, fonts). Override the workspace
with the env var `URM_STUDIO_HOME`. The user can edit brand.json by hand, but normally you edit it for them
with `brand set`. Nothing in the code is brand-specific.

## Quick setup (Beginner: one question per message)
1. **Name** — «ما اسم نشاطك أو علامتك؟ يمكنك كتابته بالعربية أو الإنجليزية أو الاثنين.» /
   "What's the name of your business or brand? Arabic, English or both is fine."
   Arabic and English names are stored separately (`--name-ar`, `--name-en`). Bilingual brands get both.
2. **Logo** — «هل لديك شعار؟ أرسل صورته هنا. إن لم يكن لديك شعار فلا مشكلة، سأكتب اسمك بخط جميل بدلًا منه.» /
   "Do you have a logo? Send a picture of it here. No logo? No problem — I'll write your name in a beautiful
   font instead." (Don't mention file formats. If the logo has a white box around it, say «الشعار سيظهر
   داخل مربع أبيض؛ إن كانت لديك نسخة بدون خلفية فأرسلها، وإلا سأستخدم هذه» once.) → `brand logo <slug> <file>` (the file is copied).
   Look at the logo (Read the image) and describe it in one line to confirm it's the right file.
   Order of commands: `brand new` (with the style if already known) → `brand logo` → `brand style SLUG <style>`
   when the style is chosen later (re-applies its colours and fonts) → `brand colors SLUG --apply` to take the
   colours from the logo when the user says "use my logo colours" or "choose for me".
   A logo with a solid white/black box background: tell the user a transparent PNG looks better; still usable.
3. **Style** — offer 6 presets with one-line descriptions; the preset sets colours + fonts. Put the one that
   fits the business first as ⭐ (don't always recommend modern):
   cafés/restaurants/perfume/jewellery → luxury · yoga/wellness/clinics/beauty → minimal · kids/sweets/events
   → playful · finance/law/consulting/education → corporate · retail sales/sports → bold · tech/agencies →
   modern. Arabic: عصري · فاخر · مرح · رسمي · بسيط · جريء — English: modern · luxury · playful · corporate ·
   minimal · bold.
4. **Colours** — never ask beginners for colour codes. Ask: «هل لعلامتك ألوان معيّنة؟ صفها بكلماتك (مثل:
   أخضر وذهبي)، أو أرسل صورة الشعار أو المحل، أو قل "اختر لي".» / "Does your brand have colours? Describe
   them (e.g. green and gold), send a photo of your logo or shop, or say 'choose for me'." Turn words or the
   picture's dominant colours into hex codes yourself, and show them as a preview (`brand preview`) rather
   than as codes. Set with `brand set <slug> colors.primary "#RRGGBB"` (secondary, accent, text, on_accent).
   Creator/Pro users may give codes directly.
   Steps 3 and 4 can be one message when the user says "choose for me" early: pick style + colours and show
   the preview for approval.
5. **Handles** — «ما اسم حسابك على إنستغرام أو تيك توك؟» Only those they use (`handles.instagram @name`).
   Shown in the outro. A WhatsApp number appears on screen only if the user explicitly says yes to
   «هل تريد أن يظهر رقم الواتساب في نهاية الفيديو؟ (لا، يكفي الحساب ⭐ / نعم وهذا رقمي)».
6. **Call to action** — do NOT ask here during a first video: it is asked once in onboarding Step 6 and saved
   to both the plan and `outro.cta.<lang>`.
7. Run `brand check <slug>` and `brand preview <slug>`. Read the two images yourself to check them, then
   **open them for the user** (`studio.py open "<brands>/<slug>/preview/intro.png"`) — reading an image only
   shows it to you, not to them. Describe each in one line and ask «هل يعجبك الشكل؟».

Creator/Pro extras: fonts per role, personality words, tagline, intro/outro durations, watermark on/off,
position, opacity, caption style (`captions.style` box|outline|brand), numerals
(`numerals` western|arabic_indic), primary language (`primary_language` ar|en|bilingual).

## brand.json fields
```json
{
  "name": {"ar": "مقهى الريحان", "en": "Al Rayhan Cafe"},
  "primary_language": "ar",
  "logo": {"file": "assets/logo-main.png", "has_logo": true},
  "colors": {"primary": "#111111", "secondary": "#3A2E1F", "accent": "#C9A227", "text": "#FFFFFF", "on_accent": "#111111"},
  "fonts": {"arabic_heading": "Amiri", "arabic_body": "Noto Naskh Arabic", "latin_heading": "Inter",
            "latin_body": "Inter", "custom": []},
  "personality": ["warm", "authentic"], "visual_style": "luxury",
  "handles": {"instagram": "@alrayhan.cafe", "tiktok": "", "website": ""},
  "tagline": {"ar": "قهوة مختصة تُحمَّص يوميًا", "en": ""},
  "intro": {"enabled": true, "duration": 2.0},
  "outro": {"enabled": true, "duration": 3.0, "show_handles": true, "cta": {"ar": "زورونا اليوم", "en": "Visit us today"}},
  "watermark": {"enabled": false, "position": "top_corner", "opacity": 0.85},
  "captions": {"style": "box"},
  "numerals": "western"
}
```

## Bundled fonts (SIL Open Font License — free for commercial video)
| Font | Character | Good for |
|---|---|---|
| Cairo | modern, geometric, wide weight range, includes Latin | modern, playful, bold |
| Tajawal | clean, friendly, very readable at small sizes | body text, captions |
| Noto Kufi Arabic | structured Kufi, corporate | corporate, tech |
| Noto Naskh Arabic | classic book Naskh, highly readable | luxury body, long captions |
| Amiri | elegant classical Naskh | luxury, cultural, formal |
| Inter | neutral Latin | English text |

Custom fonts: only after the user confirms they have the licence to use it in videos.
`brand font <slug> <file> "<Family Name>" --weight 700 --license-ok` (copied into the brand). Then set
`fonts.arabic_heading` to the family. Check Arabic coverage by rendering a test card
(`card "أبجد هوز حطي كلمن ٠١٢٣" --brand <slug> --out test.png --bg`) and looking at it. If letters show as
boxes or disconnected, the font has no proper Arabic support — tell the user and keep a bundled font.

## Special cases
- **No logo**: intro shows the name as a typographic wordmark (both names for bilingual brands); outro
  shows the name. Offer later: «إذا صمّمت شعارًا لاحقًا أرسله وسأضيفه.»
- **No brand configured**: neutral dark style, no intro, no outro (unless the plan sets `branding.cta`),
  no watermark, no names. Never fill in URM ENROLL or any example brand.
- **Several brands** (agency users): always confirm which brand a project uses; the project stores it.
  Changing a project's brand: edit `brand` in plan.json and project.json, re-render.
- **Updating**: `brand set` changes apply to future renders; old versions are untouched.
- **Isolation**: a render only reads its own brand folder. QC fails if another brand's name, handle or
  asset path appears in the rendered text cards, or if "URM ENROLL" appears in a non-URM brand's video.

## Example profiles
`examples/brands/*.json` (fictional businesses) can be copied with
`brand new --from-file <file>` to show users what a finished profile looks like. Never use them for the
user's real videos without saying so.
