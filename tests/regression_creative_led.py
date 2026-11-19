#!/usr/bin/env python3
"""Regression tests for creative-led, mixed and asset-led productions (owner acceptance matrix C1–C7).

  python3 tests/regression_creative_led.py --fixtures DIR --out RESULTS_DIR [--only C1,C3] [--full]

DIR comes from tests/make_fixtures.py. Every scenario runs in a fresh, isolated workspace and renders real
videos. C1 and C2 (the acceptance briefs) always render at full size; the others render previews (half
size) unless --full is given. Results: RESULTS_DIR/creative_results.json and frames in
RESULTS_DIR/creative_frames/.

  C1   asset-free English acceptance brief: 30 s language-school promo, no logo/colours/footage/images/music
  C2   asset-free Arabic acceptance brief (RTL, joined letters, Latin CEFR levels inside Arabic layout)
  C2B  Arabic asset-free brief without even a business name; Arabic-Indic numerals
  C3   mixed: user footage + a user photo + an AI-registered photo (provider + licence), no brand, no music
  C4   existing brand: real logo + brand colours + the user's footage; motion scenes follow the brand
  C5   negative: a slideshow plan (stills + title cards) must FAIL in creative mode
  C5B  the same slideshow from the user's own assets stays deliverable (WARN): asset-led behaviour unchanged
  C6A  narration over an original score: voice heard to the end, music ducked, no dead air
  C6B  asset-led: user footage + user music + recorded narration
  C6C  narration longer than the video must be flagged (never silently cut off)
  C6D  mixed production with no music at all: an original score is composed automatically (no silence)
  C7   export integrity, landscape: hard cuts + dissolves, different scene lengths, a short final scene that
       must be in the picture, no black frames, clean decode
  C7B  motion clips are cached: an unchanged re-render reuses them
  C8   stopping a render leaves no helper browsers or temporary folders, and the next render works
  every scenario that writes production.json also checks it contains no absolute (private) paths
"""
import argparse
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skill" / "urm-creator-studio"


class R:
    def __init__(self, fx, out, ws_name):
        self.fx, self.out = Path(fx), Path(out)
        self.ws = self.out / ws_name
        shutil.rmtree(self.ws, ignore_errors=True)
        self.env = dict(os.environ, URM_STUDIO_HOME=str(self.ws))

    def st(self, *args, check=True, lang="en"):
        cmd = [sys.executable, str(SKILL / "scripts" / "studio.py"), "--lang", lang, "--json", *map(str, args)]
        cp = subprocess.run(cmd, capture_output=True, text=True, env=self.env)
        if check and cp.returncode != 0:
            raise RuntimeError("studio %s failed (%s): %s %s" % (args[:2], cp.returncode, cp.stdout[-1500:], cp.stderr[-1500:]))
        try:
            return (json.loads(cp.stdout) if cp.stdout.strip() else {}), cp.returncode
        except json.JSONDecodeError:
            return {"raw": cp.stdout[-2000:]}, cp.returncode

    def pdir(self, slug):
        return self.ws / "projects" / slug

    def plan(self, slug, plan):
        (self.pdir(slug) / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


ACCEPTANCE_PLAN = {
    "title": "Language School Promo", "brand": None, "format": "vertical", "language": "en", "fps": 30,
    "production": {"mode": "creative",
                   "concept": "Your world, in a new language: from first words to new opportunities"},
    "look": "academy", "identity": {"name": "Horizon Language Academy"},
    "scenes": [
        {"kind": "motion", "template": "kinetic_title", "duration": 4.2,
         "params": {"kicker": "Study abroad", "title": "Where will your next language take you?", "highlight": "next"}},
        {"kind": "motion", "template": "word_cloud", "duration": 3.8,
         "params": {"title": "Speak to the world", "highlight": "world", "subtitle": "Every conversation opens a door",
                    "words": ["Hello", "مرحبا", "Hola", "Bonjour", "Ciao", "Hallo", "Olá", "Привет", "Merhaba",
                              "Γεια σας", "Salut", "Hej"]}},
        {"kind": "motion", "template": "globe", "duration": 4.0,
         "params": {"title": "One classroom, the whole world", "subtitle": "Learn with students from everywhere"}},
        {"kind": "motion", "template": "features", "duration": 4.6,
         "params": {"title": "Learning you can trust", "highlight": "trust",
                    "items": [{"icon": "cap", "title": "Expert teachers", "text": "Qualified and supportive"},
                              {"icon": "users", "title": "Small classes", "text": "More time to speak"},
                              {"icon": "award", "title": "Recognised certificates", "text": "Proof of your progress"}]}},
        {"kind": "motion", "template": "journey", "duration": 4.4,
         "params": {"title": "From first words to fluency", "highlight": "fluency",
                    "steps": ["A1", "A2", "B1", "B2", "C1", "C2"]}},
        {"kind": "motion", "template": "contrast", "duration": 5.0,
         "params": {"from": "A new language", "to": "A world of opportunity", "highlight": "opportunity"}},
        {"kind": "motion", "template": "cta", "duration": 4.0,
         "params": {"title": "New courses start every month", "button": "Book your free trial",
                    "sub": "horizon-academy.example"}},
    ],
    "audio": {"score": {"mood": "inspiring"}, "normalize": True, "target_lufs": -14},
    "branding": {"intro": False, "outro": False},
}


def checks_of(res):
    return res.get("checks") or {}


def frame_sheet(res, out, label):
    src = res.get("inspect_frames")
    if src and Path(src).exists():
        dst = out / "creative_frames" / ("%s.png" % label)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return str(dst.relative_to(out))
    return None


PRIVATE_PATH = re.compile(r"(/Users/|/home/|/private/|/var/folders/|/tmp/|[A-Za-z]:\\\\)")


def manifest_private_paths(text):
    """production.json may travel with the video: it must not contain absolute paths (user/folder names)."""
    return PRIVATE_PATH.findall(text)


def common_creative_asserts(res, man, problems, need_motion=True):
    c = checks_of(res)
    if res.get("qc") == "FAIL":
        problems.append("QC FAIL: %s" % {k: v for k, v in c.items() if v == "fail"})
    for k in ("no_frozen_moments", "not_a_slideshow", "creative_structure", "text_not_clipped", "audio_track",
              "picture_complete", "decodes_cleanly", "no_black_frames"):
        if need_motion and c.get(k) not in ("ok",):
            problems.append("%s=%s" % (k, c.get(k)))
    if res.get("manifest") and Path(res["manifest"]).exists():
        leak = manifest_private_paths(Path(res["manifest"]).read_text(encoding="utf-8"))
        if leak:
            problems.append("production.json exposes private paths: %s" % leak[:3])
    for k in ("cover", "manifest"):
        if not res.get(k) or not Path(res[k]).exists():
            problems.append("missing deliverable: %s" % k)
    if man and not any(a.get("kind") == "music" and a.get("origin") == "engine" for a in man.get("assets", [])):
        problems.append("manifest does not record the engine-generated soundtrack")


def c1(fx, out, full=True):
    r = R(fx, out, "ws-c1")
    r.st("project", "new", "Language School Promo", "--format", "vertical", "--language", "en", "--type", "ad")
    r.plan("language-school-promo", ACCEPTANCE_PLAN)
    res, code = r.st("render", "language-school-promo", *([] if full else ["--preview"]), check=False)
    problems = []
    man = json.loads(Path(res["manifest"]).read_text()) if res.get("manifest") and Path(res["manifest"]).exists() else {}
    common_creative_asserts(res, man, problems)
    if man.get("production_mode") != "creative":
        problems.append("mode=%s" % man.get("production_mode"))
    if abs(res.get("duration", 0) - 30.0) > 0.5:
        problems.append("duration %.2f" % res.get("duration", 0))
    if full and man.get("size") != "1080x1920":
        problems.append("size %s" % man.get("size"))
    srt = Path(res["version_dir"]) / "onscreen_text.srt" if res.get("version_dir") else None
    if not srt or not srt.exists():
        problems.append("no on-screen text subtitle file")
    if any(a.get("origin") == "user" for a in man.get("assets", [])):
        problems.append("asset-free brief lists user assets")
    if not (man.get("identity") or {}).get("temporary"):
        problems.append("identity not marked temporary")
    return problems, res, "c1_acceptance"


def c2b(fx, out, full=False):
    r = R(fx, out, "ws-c2")
    r.st("project", "new", "Ramadan offer", "--format", "vertical", "--language", "ar", "--type", "ad", lang="ar")
    plan = {"title": "عرض", "format": "vertical", "language": "ar", "production": {"mode": "creative"},
            "look": {"preset": "warm"},
            "scenes": [
                {"kind": "motion", "template": "kinetic_title", "duration": 3.6,
                 "params": {"kicker": "عرض خاص", "title": "حلويات البيت في رمضان ٢٠٢٧", "highlight": "رمضان"}},
                {"kind": "motion", "template": "features", "duration": 4.4,
                 "params": {"title": "لماذا نحن؟", "items": [{"icon": "heart", "title": "مكونات طبيعية"},
                                                            {"icon": "clock", "title": "توصيل خلال ساعة"},
                                                            {"icon": "gift", "title": "تغليف هدايا مجاني"}]}},
                {"kind": "motion", "template": "stats", "duration": 3.8,
                 "params": {"title": "خصم الافتتاح", "items": [{"value": "20", "suffix": "%", "label": "على كل الطلبات"}]}},
                {"kind": "motion", "template": "cta", "duration": 3.6,
                 "params": {"title": "اطلب قبل الإفطار", "button": "اطلب عبر واتساب", "mark": False}},
            ],
            "audio": {"score": {"mood": "playful"}}, "branding": {"intro": False, "outro": False}}
    r.plan("ramadan-offer", plan)
    res, code = r.st("render", "ramadan-offer", *([] if full else ["--preview"]), check=False, lang="ar")
    problems = []
    man = json.loads(Path(res["manifest"]).read_text()) if res.get("manifest") else {}
    common_creative_asserts(res, man, problems)
    if (man.get("identity") or {}).get("name"):
        problems.append("an identity name appeared although none was given")
    return problems, res, "c2_arabic_no_name"


def c3(fx, out, full=False):
    r = R(fx, out, "ws-c3")
    r.st("project", "new", "Cafe launch", "--format", "vertical", "--language", "en", "--type", "ad")
    r.st("project", "add", "cafe-launch", Path(fx) / "photo_portrait.jpg", Path(fx) / "photo_landscape.jpg",
         Path(fx) / "clip_landscape.mp4")
    r.st("asset", "register", "cafe-launch", "media/photo_portrait.jpg", "--origin", "ai-generated",
         "--provider", "Example Image Model (test)", "--license", "commercial use per provider terms (test)",
         "--prompt", "warm café interior, morning light")
    # no brand, no look, no colours, no music: only footage, two photos and a name
    plan = {"title": "Cafe launch", "format": "vertical", "language": "en",
            "identity": {"name": "Bean There"},
            "scenes": [
                {"kind": "motion", "template": "kinetic_title", "duration": 3.4,
                 "params": {"title": "Your new morning ritual", "highlight": "morning"}},
                {"kind": "video", "src": "media/clip_landscape.mp4", "start": 0.5, "end": 3.5,
                 "texts": [{"text": "Freshly roasted", "role": "headline", "animation": "slide_up"}]},
                {"kind": "motion", "template": "showcase", "duration": 4.0,
                 "params": {"image": "media/photo_portrait.jpg", "title": "Made with care", "chips": ["Organic", "Local"]}},
                {"kind": "image", "src": "media/photo_landscape.jpg", "duration": 3.2, "motion": "zoom_in",
                 "texts": [{"text": "A corner to slow down", "role": "headline", "animation": "slide_up"}]},
                {"kind": "motion", "template": "cta", "duration": 3.6,
                 "params": {"title": "Opening Saturday", "button": "Visit us", "sub": "@beanthere.example"}},
            ],
            "transition": {"type": "fade", "duration": 0.4},
            "audio": {"score": {"mood": "playful"}}, "branding": {"intro": False, "outro": False}}
    r.plan("cafe-launch", plan)
    res, code = r.st("render", "cafe-launch", *([] if full else ["--preview"]), check=False)
    problems = []
    man = json.loads(Path(res["manifest"]).read_text()) if res.get("manifest") else {}
    common_creative_asserts(res, man, problems)
    if man.get("production_mode") != "mixed":
        problems.append("mode=%s (expected mixed)" % man.get("production_mode"))
    ai = [a for a in man.get("assets", []) if a.get("origin") == "ai-generated"]
    if not ai or not ai[0].get("provider") or not ai[0].get("license"):
        problems.append("AI-generated photo provenance missing in manifest")
    users = [str(a.get("file", "")) for a in man.get("assets", []) if a.get("origin") == "user"]
    if not any(u.endswith(".mp4") for u in users) or not any(u.endswith("photo_landscape.jpg") for u in users):
        problems.append("user clip/photo not recorded as user assets: %s" % users)
    exp = sum([3.4, 3.0, 4.0, 3.2, 3.6]) - 4 * 0.4
    if abs(res.get("duration", 0) - exp) > 0.6:
        problems.append("duration %.2f, expected ≈%.2f (a scene was lost?)" % (res.get("duration", 0), exp))
    # registering stock media without provider/licence must be refused
    _, code2 = r.st("asset", "register", "cafe-launch", "media/clip_landscape.mp4", "--origin", "stock", check=False)
    if code2 == 0:
        problems.append("stock asset accepted without provider/licence")
    return problems, res, "c3_mixed"


def c4(fx, out, full=False):
    r = R(fx, out, "ws-c4")
    r.st("brand", "new", "--name-en", "Northwind Tutors", "--style", "corporate")
    r.st("brand", "logo", "northwind-tutors", Path(fx) / "logo_english.png")
    r.st("brand", "set", "northwind-tutors", "colors.primary", "#0F4C81")
    r.st("brand", "set", "northwind-tutors", "colors.accent", "#F2A900")
    r.st("project", "new", "Tutors", "--brand", "northwind-tutors", "--format", "landscape", "--language", "en")
    r.st("project", "add", "tutors", Path(fx) / "clip_landscape.mp4")
    plan = {"title": "Tutors", "brand": "northwind-tutors", "format": "landscape", "language": "en",
            "scenes": [
                {"kind": "motion", "template": "logo_reveal", "duration": 3.8, "params": {"tagline": "Tutoring that fits your week"}},
                {"kind": "video", "src": "media/clip_landscape.mp4", "start": 1.0, "end": 4.6,
                 "texts": [{"text": "Real lessons, real progress", "role": "headline", "animation": "slide_up"}]},
                {"kind": "motion", "template": "features", "duration": 4.2,
                 "params": {"title": "How it works", "items": [{"icon": "calendar", "title": "Pick a time"},
                                                               {"icon": "laptop", "title": "Join online"},
                                                               {"icon": "chart", "title": "See progress"}]}},
                {"kind": "motion", "template": "cta", "duration": 3.6, "params": {"button": "Book a lesson"}},
            ],
            "transition": {"type": "fade", "duration": 0.4},
            "audio": {"score": {"mood": "corporate"}}, "branding": {"intro": False, "outro": False}}
    r.plan("tutors", plan)
    res, code = r.st("render", "tutors", *([] if full else ["--preview"]), check=False)
    problems = []
    man = json.loads(Path(res["manifest"]).read_text()) if res.get("manifest") else {}
    common_creative_asserts(res, man, problems)
    if man.get("look") != "brand":
        problems.append("motion look did not follow the brand (%s)" % man.get("look"))
    pal = man.get("palette") or {}
    if (pal.get("primary") or "").upper() != "#0F4C81" or (pal.get("accent") or "").upper() != "#F2A900":
        problems.append("brand colours not used: %s" % pal)
    if (man.get("identity") or {}).get("temporary"):
        problems.append("real logo not used (identity marked temporary)")
    if not any(a.get("origin") == "user" and str(a.get("file", "")).endswith(".mp4") for a in man.get("assets", [])):
        problems.append("brand footage not recorded as a user asset")
    return problems, res, "c4_brand_logo_colours_footage"


SLIDESHOW_SCENES = [
    {"kind": "title", "duration": 3.0, "texts": [{"text": "Welcome", "role": "title"}]},
    {"kind": "image", "src": "media/photo_landscape.jpg", "duration": 4.0, "motion": "zoom_in"},
    {"kind": "image", "src": "media/photo_portrait.jpg", "duration": 4.0, "motion": "zoom_out"},
    {"kind": "title", "duration": 3.0, "texts": [{"text": "Thank you", "role": "title"}]},
]


def c5(fx, out, full=False):
    r = R(fx, out, "ws-c5")
    r.st("project", "new", "Slides", "--format", "vertical", "--language", "en")
    r.st("project", "add", "slides", Path(fx) / "photo_landscape.jpg", Path(fx) / "photo_portrait.jpg")
    r.plan("slides", {"title": "Slides", "format": "vertical", "language": "en", "production": {"mode": "creative"},
                      "scenes": SLIDESHOW_SCENES, "audio": {}})
    res, code = r.st("render", "slides", "--preview", check=False)
    c = checks_of(res)
    problems = []
    if code != 3 or res.get("qc") != "FAIL":
        problems.append("slideshow in creative mode did not FAIL (qc=%s, exit=%s)" % (res.get("qc"), code))
    if c.get("not_a_slideshow") != "fail":
        problems.append("not_a_slideshow=%s" % c.get("not_a_slideshow"))
    if c.get("creative_structure") != "fail":
        problems.append("creative_structure=%s" % c.get("creative_structure"))
    return problems, res, "c5_slideshow_fails"


def c5b(fx, out, full=False):
    r = R(fx, out, "ws-c6")
    r.st("project", "new", "Family album", "--format", "vertical", "--language", "en", "--type", "personal")
    r.st("project", "add", "family-album", Path(fx) / "photo_landscape.jpg", Path(fx) / "photo_portrait.jpg",
         Path(fx) / "music_pad.wav")
    r.plan("family-album", {"title": "Album", "format": "vertical", "language": "en", "scenes": SLIDESHOW_SCENES,
                            "audio": {"music": {"src": "media/music_pad.wav", "volume": 0.4}}})
    res, code = r.st("render", "family-album", "--preview", check=False)
    c = checks_of(res)
    problems = []
    if res.get("qc") == "FAIL" or code != 0:
        problems.append("asset-led personal slideshow was blocked (qc=%s)" % res.get("qc"))
    if c.get("not_a_slideshow") not in ("warn",):
        problems.append("expected a slideshow WARN for asset-led, got %s" % c.get("not_a_slideshow"))
    if res.get("production_mode") != "asset":
        problems.append("mode=%s" % res.get("production_mode"))
    if "creative_structure" in c:
        problems.append("creative gate applied to an asset-led video")
    return problems, res, "c5b_asset_led_slideshow_warns"


def c7b(fx, out, full=False):
    r = R(fx, out, "ws-c7b")
    r.st("project", "new", "Cache", "--format", "square", "--language", "en")
    plan = {"title": "Cache", "format": "square", "language": "en", "look": "tech",
            "scenes": [{"kind": "motion", "template": "kinetic_title", "duration": 3.0, "params": {"title": "Ship faster"}},
                       {"kind": "motion", "template": "cta", "duration": 3.0, "params": {"button": "Try it", "mark": False}}],
            "audio": {"score": {"mood": "energetic"}}}
    r.plan("cache", plan)
    t0 = time.time()
    r.st("render", "cache", "--preview", check=False)
    first = time.time() - t0
    t0 = time.time()
    res, code = r.st("render", "cache", "--preview", check=False)
    second = time.time() - t0
    cached = list((r.pdir("cache") / "work" / "motion-cache").glob("motion_*.mp4"))
    problems = []
    if len(cached) != 2:
        problems.append("expected 2 cached motion clips, found %d" % len(cached))
    if not second < first:
        problems.append("re-render was not faster (%.0fs vs %.0fs)" % (second, first))
    res["timing"] = {"first": round(first, 1), "second": round(second, 1)}
    return problems, res, "c7b_cache"


ARABIC_PLAN = {
    "title": "إعلان مدرسة اللغات", "brand": None, "format": "vertical", "language": "ar", "fps": 30,
    "production": {"mode": "creative", "concept": "عالمك بلغة جديدة: من الكلمات الأولى إلى فرص جديدة"},
    "look": "academy", "identity": {"name": "أكاديمية الأفق للغات"},
    "scenes": [
        {"kind": "motion", "template": "kinetic_title", "duration": 4.2,
         "params": {"kicker": "الدراسة في الخارج", "title": "إلى أين ستأخذك لغتك القادمة؟", "highlight": "لغتك"}},
        {"kind": "motion", "template": "word_cloud", "duration": 3.8,
         "params": {"title": "تحدّث مع العالم", "highlight": "العالم", "subtitle": "كل محادثة تفتح بابًا جديدًا",
                    "words": ["مرحبا", "Hello", "Hola", "Bonjour", "Ciao", "Hallo", "Olá", "Привет", "Merhaba",
                              "Γεια σας", "Salut", "Hej"]}},
        {"kind": "motion", "template": "globe", "duration": 4.0,
         "params": {"title": "صفّ واحد والعالم كلّه", "subtitle": "تعلّم مع طلاب من كل مكان"}},
        {"kind": "motion", "template": "features", "duration": 4.6,
         "params": {"title": "تعليم تثق به", "highlight": "تثق",
                    "items": [{"icon": "cap", "title": "معلّمون خبراء", "text": "مؤهّلون وداعمون"},
                              {"icon": "users", "title": "مجموعات صغيرة", "text": "وقت أطول للتحدّث"},
                              {"icon": "award", "title": "شهادات معترف بها", "text": "دليل على تقدّمك"}]}},
        {"kind": "motion", "template": "journey", "duration": 4.4,
         "params": {"title": "من الكلمات الأولى إلى الطلاقة", "highlight": "الطلاقة",
                    "steps": ["A1", "A2", "B1", "B2", "C1", "C2"]}},
        {"kind": "motion", "template": "contrast", "duration": 5.0,
         "params": {"from": "لغة جديدة", "to": "عالم من الفرص", "highlight": "الفرص"}},
        {"kind": "motion", "template": "cta", "duration": 4.0,
         "params": {"title": "دورات جديدة تبدأ كل شهر", "button": "احجز درسك التجريبي المجاني",
                    "sub": "horizon-academy.example"}},
    ],
    "audio": {"score": {"mood": "inspiring"}, "normalize": True, "target_lufs": -14},
    "branding": {"intro": False, "outro": False},
}


def c2(fx, out, full=True):
    r = R(fx, out, "ws-c2")
    r.st("project", "new", "Language School Arabic", "--format", "vertical", "--language", "ar", "--type", "ad", lang="ar")
    r.plan("language-school-arabic", ARABIC_PLAN)
    res, code = r.st("render", "language-school-arabic", *([] if full else ["--preview"]), check=False, lang="ar")
    problems = []
    man = json.loads(Path(res["manifest"]).read_text()) if res.get("manifest") else {}
    common_creative_asserts(res, man, problems)
    if abs(res.get("duration", 0) - 30.0) > 0.5:
        problems.append("duration %.2f" % res.get("duration", 0))
    if full and man.get("size") != "1080x1920":
        problems.append("size %s" % man.get("size"))
    c = checks_of(res)
    if c.get("text_reading_time") != "ok":
        problems.append("text_reading_time=%s" % c.get("text_reading_time"))
    if not (man.get("identity") or {}).get("temporary"):
        problems.append("identity not marked temporary")
    return problems, res, "c2_arabic_acceptance"


def _motion_scenes(title):
    return [{"kind": "motion", "template": "kinetic_title", "duration": 3.4, "params": {"title": title}},
            {"kind": "motion", "template": "features", "duration": 4.0,
             "params": {"title": "Why us", "items": [{"icon": "heart", "title": "Made fresh"},
                                                     {"icon": "clock", "title": "Ready in minutes"}]}},
            {"kind": "motion", "template": "cta", "duration": 3.6, "params": {"button": "Order now", "mark": False}}]


def _audio_common(res, problems):
    c = checks_of(res)
    for k in ("audio_track", "decodes_cleanly", "picture_complete", "no_dead_air"):
        if c.get(k) != "ok":
            problems.append("%s=%s" % (k, c.get(k)))
    if c.get("loudness") not in ("ok",):
        problems.append("loudness=%s" % c.get("loudness"))


def c6a(fx, out, full=False):
    r = R(fx, out, "ws-c6a")
    r.st("project", "new", "Narrated", "--format", "vertical", "--language", "en")
    r.st("project", "add", "narrated", Path(fx) / "speech_en.mp4")
    r.plan("narrated", {"title": "Narrated", "format": "vertical", "language": "en", "production": {"mode": "creative"},
                        "look": "fresh", "scenes": _motion_scenes("Lunch, sorted"),
                        "audio": {"score": {"mood": "corporate"}, "voiceover": {"src": "media/speech_en.mp4", "start": 0.8}},
                        "branding": {"intro": False, "outro": False}})
    res, code = r.st("render", "narrated", "--preview", check=False)
    problems = []
    _audio_common(res, problems)
    c = checks_of(res)
    if c.get("voiceover_complete") != "ok":
        problems.append("voiceover_complete=%s" % c.get("voiceover_complete"))
    if res.get("qc") == "FAIL":
        problems.append("QC FAIL")
    # the score sits under the voice: louder while nobody speaks than while the voice is on
    v = res.get("video")
    if v:
        from_vo = _rms(v, 2.0, 3.0)
        after = _rms(v, 8.0, 2.0)
        if from_vo is None or after is None:
            problems.append("could not measure the mix")
        elif from_vo < after + 3.0:
            problems.append("voice does not stand out over the score (%.1f dB with voice vs %.1f dB score only)"
                            % (from_vo, after))
        res["mix_db"] = {"with_voice": from_vo, "score_only": after}
    return problems, res, "c6a_narration_over_score"


def _rms(video, start, dur):
    import re as _re
    cp = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(start), "-t", str(dur), "-i", str(video),
                         "-vn", "-af", "astats=metadata=0", "-f", "null", "-"], capture_output=True, text=True)
    m = _re.findall(r"RMS level dB: (-?[\d.]+|-inf)", cp.stderr)
    try:
        return float(m[-1])
    except (IndexError, ValueError):
        return None


def c6b(fx, out, full=False):
    r = R(fx, out, "ws-c6b")
    r.st("project", "new", "Shop clip", "--format", "vertical", "--language", "en")
    r.st("project", "add", "shop-clip", Path(fx) / "clip_vertical_silent.mp4", Path(fx) / "photo_portrait.jpg",
         Path(fx) / "music_pad.wav", Path(fx) / "speech_en.mp4")
    r.plan("shop-clip", {"title": "Shop", "format": "vertical", "language": "en",
                         "scenes": [{"kind": "video", "src": "media/clip_vertical_silent.mp4", "start": 0, "end": 5.0,
                                     "texts": [{"text": "New in store", "role": "headline"}]},
                                    {"kind": "image", "src": "media/photo_portrait.jpg", "duration": 3.0, "motion": "zoom_in",
                                     "texts": [{"text": "Open daily", "role": "headline"}]}],
                         "audio": {"music": {"src": "media/music_pad.wav", "volume": 0.35},
                                   "voiceover": {"src": "media/speech_en.mp4", "start": 0.5}},
                         "branding": {"intro": False, "outro": False}})
    res, code = r.st("render", "shop-clip", "--preview", check=False)
    problems = []
    _audio_common(res, problems)
    c = checks_of(res)
    if c.get("voiceover_complete") != "ok":
        problems.append("voiceover_complete=%s" % c.get("voiceover_complete"))
    if res.get("production_mode") != "asset":
        problems.append("mode=%s" % res.get("production_mode"))
    if res.get("qc") == "FAIL":
        problems.append("QC FAIL")
    return problems, res, "c6b_asset_music_voice"


def c6c(fx, out, full=False):
    r = R(fx, out, "ws-c6c")
    r.st("project", "new", "Too long", "--format", "vertical", "--language", "ar", lang="ar")
    r.st("project", "add", "too-long", Path(fx) / "speech_ar.mp4")
    r.plan("too-long", {"title": "Too long", "format": "vertical", "language": "ar", "production": {"mode": "creative"},
                        "scenes": [{"kind": "motion", "template": "kinetic_title", "duration": 3.6, "params": {"title": "عرض اليوم"}},
                                   {"kind": "motion", "template": "cta", "duration": 3.6, "params": {"button": "اطلب الآن", "mark": False}}],
                        "audio": {"voiceover": {"src": "media/speech_ar.mp4"}}, "branding": {"intro": False, "outro": False}})
    res, code = r.st("render", "too-long", "--preview", check=False, lang="ar")
    c = checks_of(res)
    problems = []
    if c.get("voiceover_complete") != "fail" or res.get("qc") != "FAIL":
        problems.append("a 16 s narration cut to 7 s was not flagged (voiceover_complete=%s, qc=%s)"
                        % (c.get("voiceover_complete"), res.get("qc")))
    return problems, res, "c6c_narration_too_long"


def c6d(fx, out, full=False):
    r = R(fx, out, "ws-c6d")
    r.st("project", "new", "No music", "--format", "vertical", "--language", "en")
    r.st("project", "add", "no-music", Path(fx) / "clip_vertical_silent.mp4")
    scenes = _motion_scenes("Fresh every morning")
    scenes.insert(1, {"kind": "video", "src": "media/clip_vertical_silent.mp4", "start": 0.5, "end": 4.0,
                      "texts": [{"text": "Baked here", "role": "headline"}]})
    r.plan("no-music", {"title": "No music", "format": "vertical", "language": "en", "scenes": scenes,
                        "branding": {"intro": False, "outro": False}})
    res, code = r.st("render", "no-music", "--preview", check=False)
    problems = []
    _audio_common(res, problems)
    man = json.loads(Path(res["manifest"]).read_text()) if res.get("manifest") else {}
    if not any(a.get("kind") == "music" and a.get("origin") == "engine" for a in man.get("assets", [])):
        problems.append("no soundtrack was composed for a production without music")
    if res.get("qc") == "FAIL":
        problems.append("QC FAIL")
    return problems, res, "c6d_missing_music"


def c7(fx, out, full=False):
    r = R(fx, out, "ws-c7")
    r.st("project", "new", "Integrity", "--format", "landscape", "--language", "en")
    r.st("project", "add", "integrity", Path(fx) / "clip_landscape.mp4")
    durs = [2.8, 4.6, 2.2, 4.4, 3.0]
    plan = {"title": "Integrity", "format": "landscape", "language": "en", "look": "luxury",
            "identity": {"name": "Maison Lune"},
            "scenes": [
                {"kind": "motion", "template": "kinetic_title", "duration": durs[0], "params": {"title": "Quiet luxury"}},
                {"kind": "motion", "template": "features", "duration": durs[1],
                 "params": {"title": "Crafted slowly", "items": [{"icon": "star", "title": "Hand finished"},
                                                                 {"icon": "leaf", "title": "Natural materials"}]}},
                {"kind": "video", "src": "media/clip_landscape.mp4", "start": 2.0, "end": 2.0 + durs[2]},
                {"kind": "motion", "template": "contrast", "duration": durs[3], "params": {"from": "Fast fashion", "to": "Made to last"}},
                {"kind": "motion", "template": "cta", "duration": durs[4], "params": {"button": "Visit the atelier"}},
            ],
            "transition": {"type": "fade", "duration": 0.5},
            "audio": {"score": {"mood": "luxury"}}, "branding": {"intro": False, "outro": False}}
    r.plan("integrity", plan)
    res, code = r.st("render", "integrity", *([] if full else ["--preview"]), check=False)
    problems = []
    man = json.loads(Path(res["manifest"]).read_text()) if res.get("manifest") else {}
    common_creative_asserts(res, man, problems)
    # cuts between motion scenes, dissolves into/out of footage: 2 dissolves of 0.5 s
    exp = sum(durs) - 2 * 0.5
    if abs(res.get("duration", 0) - exp) > 0.3:
        problems.append("duration %.2f, expected %.2f" % (res.get("duration", 0), exp))
    v = res.get("video")
    if v:
        # the short final scene must be in the picture: the last frame differs from the contrast scene
        meta = json.loads((Path(res["version_dir"]) / "render.json").read_text())
        last_start = meta["scene_starts"][-1]
        d = _frame_diff(v, last_start - 0.8, res["duration"] - 0.2)
        if d is None or d < 4.0:
            problems.append("final scene not visible at the end (frame difference %s)" % d)
    return problems, res, "c7_export_integrity_landscape"


def _frame_diff(video, t1, t2):
    import re as _re
    cp = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", "%.2f" % t1, "-i", str(video), "-ss", "%.2f" % t2,
                         "-i", str(video), "-filter_complex",
                         "[0:v]trim=end_frame=1,scale=320:-2,format=gray[a];[1:v]trim=end_frame=1,scale=320:-2,format=gray[b];"
                         "[a][b]blend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG",
                         "-f", "null", "-"], capture_output=True, text=True)
    m = _re.findall(r"YAVG=([\d.]+)", cp.stderr)
    return float(m[0]) if m else None


def _motion_procs():
    cp = subprocess.run(["pgrep", "-f", "urm-motion-"], capture_output=True, text=True)
    return [x for x in cp.stdout.split() if x.strip()]


def _motion_tmpdirs():
    import tempfile
    return sorted(Path(tempfile.gettempdir()).glob("urm-motion-*"))


def c8(fx, out, full=False):
    """Stopping a render (as a user closing the app or pressing stop would) leaves no helper browsers or
    temporary folders behind, and the next render of the same project still works."""
    r = R(fx, out, "ws-c8")
    r.st("project", "new", "Stop me", "--format", "vertical", "--language", "en")
    r.plan("stop-me", {"title": "Stop", "format": "vertical", "language": "en", "production": {"mode": "creative"},
                       "scenes": _motion_scenes("Stop and start again"), "branding": {"intro": False, "outro": False}})
    problems = []
    if _motion_procs() or _motion_tmpdirs():
        return ["helper browsers or temp folders already present before the test; run it alone"], {}, "c8_cancel"
    cmd = [sys.executable, str(SKILL / "scripts" / "studio.py"), "--lang", "en", "--json", "render", "stop-me", "--preview"]
    proc = subprocess.Popen(cmd, env=r.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < 120 and not _motion_procs() and proc.poll() is None:
        time.sleep(0.5)
    if not _motion_procs():
        problems.append("render never started its helper browsers (cannot test stopping)")
    time.sleep(2.0)
    proc.send_signal(signal.SIGTERM)
    try:
        code = proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        code = None
        problems.append("render did not stop within 30 s of SIGTERM")
    time.sleep(2.0)
    left_p, left_d = _motion_procs(), _motion_tmpdirs()
    if left_p:
        problems.append("%d helper browser process(es) left running" % len(left_p))
        subprocess.run(["pkill", "-f", "urm-motion-"])
    if left_d:
        problems.append("temporary folders left behind: %s" % [d.name for d in left_d])
    res, code2 = r.st("render", "stop-me", "--preview", check=False)
    if res.get("qc") != "PASS":
        problems.append("render after a stopped render did not pass (qc=%s)" % res.get("qc"))
    res["stop_exit_code"] = code
    return problems, res, "c8_cancel_and_cleanup"


SCENARIOS = {"C1": c1, "C2": c2, "C2B": c2b, "C3": c3, "C4": c4, "C5": c5, "C5B": c5b,
             "C6A": c6a, "C6B": c6b, "C6C": c6c, "C6D": c6d, "C7": c7, "C7B": c7b, "C8": c8}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only")
    ap.add_argument("--full", action="store_true", help="render C2B–C7 at full size too")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pick = [x.strip().upper() for x in a.only.split(",")] if a.only else list(SCENARIOS)
    results = []
    for sid in pick:
        t0 = time.time()
        try:
            problems, res, label = SCENARIOS[sid](a.fixtures, out, True if sid in ("C1", "C2") else a.full)
            ev = frame_sheet(res, out, label)
            status = "PASS" if not problems else "FAIL"
            results.append({"id": sid, "status": status, "problems": problems, "qc": res.get("qc"),
                            "checks": res.get("checks"), "video": res.get("video"), "frames": ev,
                            "seconds": round(time.time() - t0, 1), "timing": res.get("timing")})
        except Exception as e:
            results.append({"id": sid, "status": "ERROR", "problems": [str(e)[-1500:]], "seconds": round(time.time() - t0, 1)})
        r = results[-1]
        print("[%s] %s %s" % (r["status"], sid, "; ".join(r["problems"])[:600]), flush=True)
    (out / "creative_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    bad = [r for r in results if r["status"] != "PASS"]
    print("%d/%d passed" % (len(results) - len(bad), len(results)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
