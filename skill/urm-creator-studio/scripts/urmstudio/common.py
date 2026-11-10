"""Shared helpers: paths, settings, bilingual messages, subprocess wrappers.

Standard library only. Works on Python 3.8+ (macOS, Windows, Linux).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent  # .../urm-creator-studio
FONTS_DIR = SKILL_DIR / "fonts"
TEMPLATES_DIR = SKILL_DIR / "templates"
VERSION = "1.0.0"

FORMATS = {
    # name: (width, height, plain-language label ar, en)
    "vertical": (1080, 1920, "طولي ٩:١٦ (ريلز، تيك توك، شورتس)", "Vertical 9:16 (Reels, TikTok, Shorts)"),
    "square": (1080, 1080, "مربع ١:١ (منشور إنستغرام وفيسبوك)", "Square 1:1 (Instagram/Facebook post)"),
    "portrait": (1080, 1350, "عمودي ٤:٥ (منشور إنستغرام)", "Portrait 4:5 (Instagram feed)"),
    "landscape": (1920, 1080, "عرضي ١٦:٩ (يوتيوب، شاشات، عروض)", "Landscape 16:9 (YouTube, screens)"),
}

# Areas covered by platform buttons/captions, as fractions of the frame.
# (top, right, bottom, left)
SAFE_MARGINS = {
    "vertical": (0.11, 0.12, 0.20, 0.06),
    "square": (0.06, 0.06, 0.08, 0.06),
    "portrait": (0.07, 0.06, 0.10, 0.06),
    "landscape": (0.07, 0.05, 0.09, 0.05),
}


def studio_home() -> Path:
    """User workspace (brands, projects). Never inside the skill folder."""
    env = os.environ.get("URM_STUDIO_HOME")
    p = Path(env).expanduser() if env else Path.home() / "URM-Creator-Studio"
    return p


def ensure_home() -> Path:
    h = studio_home()
    for sub in ("brands", "projects", "inbox", "models"):
        (h / sub).mkdir(parents=True, exist_ok=True)
    s = h / "settings.json"
    if not s.exists():
        write_json(s, {"language": None, "mode": "beginner", "default_brand": None})
    readme = h / "README.txt"
    if not readme.exists():
        readme.write_text(
            "URM Creator Studio workspace / مساحة عمل استوديو URM\n\n"
            "brands/   = your brand profiles / ملفات هويتك التجارية\n"
            "projects/ = your video projects; finished videos are in projects/<name>/output/ /"
            " مشاريعك، والفيديوهات الجاهزة في output\n"
            "inbox/    = drop your photos, videos, logos and music here / ضع ملفاتك هنا\n"
            "models/   = optional speech-to-text model file / ملف نموذج تحويل الكلام إلى نص (اختياري)\n",
            encoding="utf-8",
        )
    return h


def load_settings() -> dict:
    s = studio_home() / "settings.json"
    if s.exists():
        try:
            return read_json(s)
        except Exception:
            pass
    return {"language": None, "mode": "beginner", "default_brand": None}


def save_settings(d: dict):
    ensure_home()
    write_json(studio_home() / "settings.json", d)


def ui_lang(explicit=None) -> str:
    if explicit in ("ar", "en"):
        return explicit
    env = os.environ.get("URM_STUDIO_LANG")
    if env in ("ar", "en"):
        return env
    s = load_settings().get("language")
    return s if s in ("ar", "en") else "ar"  # Arabic-first default


def say(lang: str, ar: str, en: str) -> str:
    return ar if lang == "ar" else en


def read_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, p)


def slugify(text: str, fallback="item") -> str:
    """ASCII slug when possible; keeps Arabic letters otherwise (valid on all OSes)."""
    t = unicodedata.normalize("NFKC", text or "").strip().lower()
    t = re.sub(r"[\s_]+", "-", t)
    t = re.sub(r"[^\w\-؀-ۿ]", "", t)
    t = re.sub(r"-{2,}", "-", t).strip("-")
    return t[:48] or fallback


def which(name):
    return shutil.which(name)


def run(cmd, check=True, capture=True, timeout=None, cwd=None):
    """Run a command list. Returns CompletedProcess. Never uses a shell."""
    try:
        cp = subprocess.run(
            [str(c) for c in cmd],
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            timeout=timeout,
            cwd=cwd,
        )
    except FileNotFoundError as e:
        raise StudioError("missing_tool", str(cmd[0])) from e
    if check and cp.returncode != 0:
        err = (cp.stderr or b"").decode("utf-8", "replace")[-3000:]
        raise StudioError("command_failed", f"{Path(str(cmd[0])).name}: {err}")
    return cp


class StudioError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


ERROR_TEXT = {
    "missing_tool": (
        "أداة لازمة غير مثبّتة على جهازك: {d}. شغّل فحص الجهاز (doctor) لمعرفة طريقة التثبيت.",
        "A required tool is not installed: {d}. Run the device check (doctor) for install steps.",
    ),
    "command_failed": (
        "حدث خطأ أثناء المعالجة. التفاصيل التقنية محفوظة في سجل العمل.",
        "Something went wrong while processing. Technical details are in the render log.",
    ),
    "no_browser": (
        "لم أجد متصفح Chrome أو Edge. نحتاجه لرسم النصوص العربية بشكل صحيح. ثبّت Google Chrome ثم أعد المحاولة.",
        "Chrome or Edge was not found. It is needed to draw Arabic text correctly. Install Google Chrome and try again.",
    ),
    "not_found": ("لم أجد هذا الملف أو المجلد: {d}", "File or folder not found: {d}"),
    "bad_plan": ("خطة الفيديو فيها مشكلة: {d}", "The video plan has a problem: {d}"),
    "bad_brand": ("ملف الهوية فيه مشكلة: {d}", "The brand profile has a problem: {d}"),
    "unsafe_output": (
        "رفضتُ الكتابة فوق ملف أصلي: {d}. ملفاتك الأصلية لا تُعدَّل أبدًا.",
        "Refused to write over an original file: {d}. Your originals are never modified.",
    ),
}


def explain_error(e: "StudioError", lang: str) -> str:
    ar, en = ERROR_TEXT.get(e.code, ("خطأ: {d}", "Error: {d}"))
    return (ar if lang == "ar" else en).format(d=e.detail)


def out(msg: str):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
WEST_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")
LATIN_RE = re.compile(r"[A-Za-z]")


def text_direction(text: str) -> str:
    """Direction from the first strong character (Unicode bidi rule P2)."""
    for ch in text or "":
        if ARABIC_RE.match(ch):
            return "rtl"
        if LATIN_RE.match(ch):
            return "ltr"
    return "ltr"


def has_arabic(text: str) -> bool:
    return bool(ARABIC_RE.search(text or ""))


def fmt_time(sec: float) -> str:
    sec = max(0.0, float(sec))
    m, s = divmod(int(round(sec)), 60)
    return f"{m}:{s:02d}"
