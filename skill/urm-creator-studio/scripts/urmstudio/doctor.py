"""Device check, explained in plain Arabic or English."""
import platform
import sys
from pathlib import Path

from .captions import find_whisper
from .common import FONTS_DIR, run, say, studio_home, which
from .textrender import BUNDLED_FONTS, find_browser

INSTALL = {
    "ffmpeg": {
        "Darwin": ("افتح تطبيق «Terminal» والصق هذا السطر ثم اضغط Enter:\n    brew install ffmpeg\n"
                   "(إذا ظهرت رسالة أن brew غير موجود، ثبّت Homebrew أولًا من الموقع brew.sh)",
                   "Open the Terminal app, paste this line and press Enter:\n    brew install ffmpeg\n"
                   "(If it says brew is not found, install Homebrew first from brew.sh)"),
        "Windows": ("افتح «PowerShell» والصق:\n    winget install --id Gyan.FFmpeg -e\nثم أغلق النافذة وافتحها من جديد.",
                    "Open PowerShell and paste:\n    winget install --id Gyan.FFmpeg -e\nthen close and reopen the window."),
        "Linux": ("    sudo apt install ffmpeg", "    sudo apt install ffmpeg"),
    },
    "browser": {
        "Darwin": ("ثبّت Google Chrome من google.com/chrome (مجاني).", "Install Google Chrome from google.com/chrome (free)."),
        "Windows": ("متصفح Edge موجود عادةً في ويندوز. إن لم يُعثر عليه، ثبّت Google Chrome من google.com/chrome.",
                    "Edge normally ships with Windows. If not found, install Google Chrome from google.com/chrome."),
        "Linux": ("    sudo apt install chromium   أو ثبّت Google Chrome", "    sudo apt install chromium   or install Google Chrome"),
    },
    "whisper": {
        "Darwin": ("اختياري (لتحويل الكلام إلى ترجمة مكتوبة): brew install whisper-cpp ثم نزّل ملف النموذج ggml-large-v3-turbo.bin "
                   "إلى المجلد ~/URM-Creator-Studio/models/ (سأساعدك خطوة بخطوة).",
                   "Optional (turns speech into subtitles): brew install whisper-cpp, then download the model file "
                   "ggml-large-v3-turbo.bin into ~/URM-Creator-Studio/models/ (I can walk you through it)."),
        "Windows": ("اختياري: نزّل whisper.cpp لويندوز من صفحة الإصدارات في GitHub، ثم ملف النموذج.",
                    "Optional: download whisper.cpp for Windows from its GitHub releases page, plus a model file."),
        "Linux": ("اختياري: ابنِ whisper.cpp من المصدر ونزّل ملف النموذج.", "Optional: build whisper.cpp and download a model."),
    },
}


def check(lang="ar"):
    sysname = platform.system()
    items = []

    def add(key, ok, required, ar, en, fix=None):
        items.append({"key": key, "ok": ok, "required": required, "text": say(lang, ar, en), "fix": fix})

    py_ok = sys.version_info >= (3, 8)
    add("python", py_ok, True, "بايثون %d.%d" % sys.version_info[:2], "Python %d.%d" % sys.version_info[:2],
        None if py_ok else say(lang, "حدّث بايثون إلى 3.8 أو أحدث.", "Update Python to 3.8 or newer."))

    ff, fp = which("ffmpeg"), which("ffprobe")
    ver = ""
    if ff:
        try:
            ver = run([ff, "-hide_banner", "-version"], check=False).stdout.decode("utf-8", "replace").split("\n")[0]
        except Exception:
            pass
    add("ffmpeg", bool(ff and fp), True, "FFmpeg (محرّك الفيديو) %s" % ("موجود" if ff else "غير موجود"),
        "FFmpeg (video engine) %s" % ("found" if ff else "missing"),
        None if ff and fp else say(lang, *INSTALL["ffmpeg"].get(sysname, INSTALL["ffmpeg"]["Linux"])))
    if ff:
        enc = run([ff, "-hide_banner", "-encoders"], check=False).stdout.decode("utf-8", "replace")
        x264 = " libx264 " in enc
        add("x264", x264, False, "ترميز H.264 عالي الجودة %s" % ("متوفر" if x264 else "غير متوفر (سنستخدم بديلًا)"),
            "High-quality H.264 encoder %s" % ("available" if x264 else "missing (a fallback will be used)"))

    br = find_browser()
    add("browser", bool(br), True,
        "متصفح لرسم النصوص العربية: %s" % (Path(br).name if br else "غير موجود"),
        "Browser for drawing Arabic text: %s" % (Path(br).name if br else "missing"),
        None if br else say(lang, *INSTALL["browser"].get(sysname, INSTALL["browser"]["Linux"])))

    missing_fonts = [f for f, files in BUNDLED_FONTS.items() if not all((FONTS_DIR / r).exists() for r, _ in files)]
    add("fonts", not missing_fonts, True,
        "الخطوط العربية المرفقة %s" % ("كاملة" if not missing_fonts else "ناقصة: " + ", ".join(missing_fonts)),
        "Bundled Arabic fonts %s" % ("complete" if not missing_fonts else "missing: " + ", ".join(missing_fonts)),
        None if not missing_fonts else say(lang, "أعد تثبيت الحزمة كاملة.", "Reinstall the full package."))

    exe, model = find_whisper()
    add("whisper", bool(exe and model), False,
        "تحويل الكلام إلى نص (اختياري): %s" % ("جاهز" if exe and model else "غير مثبّت"),
        "Speech-to-text (optional): %s" % ("ready" if exe and model else "not installed"),
        None if exe and model else say(lang, *INSTALL["whisper"].get(sysname, INSTALL["whisper"]["Linux"])))

    voice = False
    if sysname == "Darwin" and which("say"):
        try:
            voice = ("%s_" % lang) in run(["say", "-v", "?"], check=False).stdout.decode("utf-8", "replace")
        except Exception:
            pass
    add("voice", voice, False, "صوت عربي مدمج للتعليق الصوتي (اختياري): %s" % ("متوفر" if voice else "غير متوفر"),
        "Built-in English voice for narration (optional): %s" % ("available" if voice else "not available"))

    home = studio_home()
    add("workspace", True, False, "مجلد عملك: %s" % home, "Your workspace folder: %s" % home)
    ready = all(i["ok"] for i in items if i["required"])
    return {"ready": ready, "items": items, "system": sysname, "browser": br, "whisper": [exe, model]}


def render_text(res, lang="ar"):
    lines = []
    lines.append(say(lang, "🔎 فحص الجهاز:", "🔎 Device check:"))
    for i in res["items"]:
        icon = "✅" if i["ok"] else ("❌" if i["required"] else "➖")
        lines.append("%s %s" % (icon, i["text"]))
        if not i["ok"] and i["fix"]:
            lines.append("   ↳ " + i["fix"].replace("\n", "\n     "))
    lines.append("")
    lines.append(say(lang, "✅ جهازك جاهز لصناعة الفيديو." if res["ready"] else
                     "⚠️ ينقص جهازك شيء ضروري. اتبع الخطوات أعلاه ثم أعد الفحص.",
                     "✅ Your computer is ready to make videos." if res["ready"] else
                     "⚠️ Something required is missing. Follow the steps above, then check again."))
    return "\n".join(lines)
