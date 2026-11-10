# Engine commands and plan.json

All commands: `python3 "<skill>/scripts/studio.py" [--lang ar|en] [--json] <command> …`
Use `--json` when you need to parse results; plain output is already bilingual-friendly.

| Command | What it does |
|---|---|
| `doctor` | Checks Python, FFmpeg, browser, fonts, optional speech-to-text and voice. Exit 2 = not ready. |
| `home` | Creates/prints the workspace (`brands/`, `projects/`, `inbox/`). |
| `settings [--language ar\|en] [--mode beginner\|creator\|pro] [--brand SLUG]` | Saves preferences. |
| `brand new --name-ar … --name-en … --style modern` / `--from-file f.json` | Creates a brand. |
| `brand set SLUG key.path VALUE` | Edits one field (validates colours, fonts, numerals). |
| `brand logo SLUG FILE` · `brand font SLUG FILE "Family" --weight 700 --license-ok` | Copies assets in. |
| `brand check SLUG` · `brand preview SLUG` · `brand show SLUG` · `brand list` | Validate / preview. |
| `project new "Title" --brand SLUG --format vertical --language ar --type social` | New project. |
| `project add SLUG FILES_OR_FOLDERS…` | Copies media into `media/` (read-only copies). |
| `project show SLUG` · `project list` | Info, media list, latest version. |
| `inspect FILES… --sheet DIR` | Duration, size, orientation, fps, audio loudness, HDR, cut points; contact sheets. |
| `card "TEXT" --out f.png [--brand SLUG] [--role headline] [--format vertical] [--bg]` | Typography test. |
| `render PROJECT [--preview] [--format square]` | Builds `output/vNNN/` (previews: `output/preview-NNN/`) and runs QC. Exit 3 = QC fail. |
| `qc VERSION_DIR` | Re-runs QC. |
| `transcribe PROJECT\|FILE --language ar\|en\|auto` | Draft subtitles (local whisper.cpp). |
| `captions check FILE.srt` · `captions reflow FILE.srt --out new.srt` | Readability check / re-split. |
| `open inbox\|home\|latest --project SLUG\|PATH [--reveal]` | Opens a folder/file on the user's screen (Finder/Explorer). |
| `brand style SLUG luxury` · `brand colors SLUG [--apply]` | Re-apply a style preset · read logo colours (and apply them). |
| `voiceover TEXT.txt OUT.wav --language ar --approved` | System voice narration (macOS), only after consent. |

## Project folder
```
projects/<slug>/
  project.json      title, brand, format, language, type, mode
  plan.json         the edit (you write this)
  media/            read-only copies of the user's files
  captions/         .srt files (drafts from transcription + approved versions)
  work/             temporary files and text-card cache (safe to delete)
  output/preview-001/  quick half-size test versions (same contents as below)
  الفيديو-النهائي_<format>.mp4 / final-video_<format>.mp4   copy of the newest final (what the user opens)
  output/v001/      <slug>_<format>.mp4, thumbnail.jpg, captions.srt/.vtt, plan.used.json,
                    render.json, render.log, QC_REPORT.md, qc/ (frames, report.json)
```

## plan.json
Paths are relative to the project folder (absolute paths also work). Times are seconds.
The `//` comments below are explanations only — the real plan.json must be plain JSON without comments.
```json
{
  "title": "عرض الافتتاح",
  "brand": "al-rayhan-cafe",            // or null for unbranded
  "format": "vertical",                  // vertical 1080x1920 | square 1080x1080 | portrait 1080x1350 | landscape 1920x1080
  "language": "ar",                      // ar | en | bilingual  (sets text direction defaults)
  "fps": 30,
  "quality": "standard",                 // standard | high
  "transition": {"type": "fade", "duration": 0.35},   // fade | slide | dissolve | fadeblack | wipeleft | circleopen | none
  "scenes": [
    {"kind": "video", "src": "media/clip1.mp4", "start": 2.0, "end": 6.5,
     "framing": "auto",                  // auto | fill | fit_blur | fit_color
     "focus": "center",                  // center | left | right | top | bottom  (for fill)
     "speed": 1.0, "volume": 1.0,
     "texts": [{"text": "افتتاح الفرع الجديد", "role": "headline", "position": "upper",
                "animation": "words", "start": 0.3, "end": 4.0}]},
    {"kind": "image", "src": "media/photo.jpg", "duration": 3.5,
     "motion": "zoom_in",                // zoom_in | zoom_out | pan_left | pan_right | none
     "texts": [{"text": "خصم ٢٠٪", "role": "headline", "animation": "slide_up"}]},
    {"kind": "title", "duration": 3.0, "background": "gradient",   // gradient | solid | "#RRGGBB"
     "texts": [{"text": "الخميس ٢٠ نوفمبر", "role": "title", "animation": "zoom"}]}
  ],
  "overlays": [
    {"kind": "lower_third", "title": "سارة أحمد", "subtitle": "مديرة التسويق", "start": 1.0, "end": 5.0},
    {"kind": "text", "text": "عرض لفترة محدودة", "role": "subtitle", "position": "upper", "start": 6, "end": 9}
  ],
  "captions": {"src": "captions/ar.srt", "burn": true, "style": "box", "position": "bottom"},
  "audio": {
    "music": {"src": "media/music.mp3", "volume": 0.18},
    "duck": true,                        // lower music under speech
    "original_volume": 1.0,              // multiply all original clip audio
    "voiceover": {"src": "media/vo.wav", "start": 0.5, "volume": 1.0},
    "sfx": false,                        // soft whoosh on transitions
    "normalize": true, "target_lufs": -14
  },
  "branding": {"intro": true, "outro": true, "watermark": false,
               "cta": {"ar": "اطلب الآن عبر واتساب", "en": "Order on WhatsApp"}},
  "output_name": "opening-offer",        // optional file name
  "keep_work": false
}
```
Notes
- Overlay/caption times are relative to the **content** (after the brand intro); the engine adds the intro
  offset itself. Scene text times are relative to their scene.
- Text `role`: `title` (largest), `headline`, `subtitle`, `body`, `cta` (pill button), `caption`.
  `position`: `top`/`upper`, `center`, `lower`/`bottom`. `animation`: `fade`, `slide_up`, `slide_side`,
  `zoom`, `words` (word-by-word, correct RTL order), `none`. Optional `style`: `{size, weight, color,
  font_ar, font_latin, align, box, max_lines, css}` (Creator/Pro).
- Use `\n` in text for a deliberate line break. Text auto-shrinks to fit; keep headlines ≤ 7 words.
- Video scene `end` beyond the clip length is clipped automatically.
- `framing: auto` fills when shapes match and uses a blurred background when a wide clip goes into a tall
  video (and vice versa) so nothing important is cut off.
- Multi-format delivery: render again with `--format square` etc.; texts re-layout automatically.
