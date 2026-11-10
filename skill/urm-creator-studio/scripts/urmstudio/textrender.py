"""Text-to-image rendering through a headless Chromium browser.

Why a browser: FFmpeg's text filters are often missing (e.g. Homebrew builds
without libfreetype/libass) and, even when present, they do not always apply
full Arabic shaping and bidirectional ordering. Chromium uses HarfBuzz + ICU,
so Arabic letters join correctly, RTL/LTR runs are ordered by the Unicode
Bidirectional Algorithm, and fonts fall back properly.

Each card is a full-frame transparent PNG (same size as the video), so the
compositor overlays it at 0,0 and QC can measure the real text bounding box.
"""
import hashlib
import html
import os
import platform
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .common import (FONTS_DIR, SAFE_MARGINS, StudioError, AR_DIGITS,
                     has_arabic, text_direction)

# --------------------------------------------------------------------------
# Browser discovery
# --------------------------------------------------------------------------

_MAC = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]
_WIN = [
    r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
    r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
    r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
    r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
    r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
]
_LINUX = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
          "microsoft-edge", "brave-browser"]


def find_browser():
    env = os.environ.get("URM_BROWSER")
    if env and Path(env).exists():
        return env
    sysname = platform.system()
    if sysname == "Darwin":
        for p in _MAC:
            if Path(p).exists():
                return p
        home_apps = Path.home() / "Applications"
        for p in _MAC:
            alt = home_apps / Path(p).relative_to("/Applications")
            if alt.exists():
                return str(alt)
    elif sysname == "Windows":
        for p in _WIN:
            q = os.path.expandvars(p)
            if Path(q).exists():
                return q
    for name in _LINUX:
        w = shutil.which(name)
        if w:
            return w
    return None


# --------------------------------------------------------------------------
# Fonts
# --------------------------------------------------------------------------

# family name -> list of (file relative to fonts/, weight range or weight)
BUNDLED_FONTS = {
    "Cairo": [("cairo/Cairo-Variable.ttf", "200 1000")],
    "Tajawal": [("tajawal/Tajawal-Regular.ttf", "400"), ("tajawal/Tajawal-Medium.ttf", "500"),
                ("tajawal/Tajawal-Bold.ttf", "700"), ("tajawal/Tajawal-ExtraBold.ttf", "800")],
    "Noto Naskh Arabic": [("noto-naskh-arabic/NotoNaskhArabic-Variable.ttf", "400 700")],
    "Noto Kufi Arabic": [("noto-kufi-arabic/NotoKufiArabic-Variable.ttf", "100 900")],
    "Amiri": [("amiri/Amiri-Regular.ttf", "400"), ("amiri/Amiri-Bold.ttf", "700")],
    "Inter": [("inter/Inter-Variable.ttf", "100 900")],
}

SAFE_ARABIC_FALLBACK = ["'Noto Naskh Arabic'", "'Cairo'", "'SF Arabic'", "'Geeza Pro'",
                        "'Segoe UI'", "'Arial'", "sans-serif"]
SAFE_LATIN_FALLBACK = ["'Inter'", "'Helvetica Neue'", "'Segoe UI'", "'Arial'", "sans-serif"]


def font_face_css(custom_fonts=None) -> str:
    rules = []
    for fam, files in BUNDLED_FONTS.items():
        for rel, weight in files:
            p = (FONTS_DIR / rel)
            if p.exists():
                rules.append(
                    "@font-face{font-family:\"%s\";src:url(\"%s\");font-weight:%s;font-display:block}"
                    % (fam, p.as_uri(), weight))
    for cf in custom_fonts or []:
        p = Path(cf.get("file", ""))
        if p.exists():
            rules.append("@font-face{font-family:\"%s\";src:url(\"%s\");font-weight:%s;font-display:block}"
                         % (cf["family"].replace('"', ''), p.as_uri(), cf.get("weight", "100 900")))
    return "\n".join(rules)


def font_stack(primary_arabic, primary_latin, rtl: bool) -> str:
    """Latin font first for LTR text; Arabic font first for RTL text.

    Browsers pick per character, so a Latin-first stack still renders Arabic
    with the first family that has Arabic glyphs, and vice-versa.
    """
    a = "'%s'" % primary_arabic.replace("'", "") if primary_arabic else None
    l = "'%s'" % primary_latin.replace("'", "") if primary_latin else None
    order = ([a, l] if rtl else [l, a]) + (SAFE_ARABIC_FALLBACK if rtl else SAFE_LATIN_FALLBACK)
    seen, res = set(), []
    for f in order:
        if f and f not in seen:
            seen.add(f)
            res.append(f)
    return ",".join(res)


# --------------------------------------------------------------------------
# Bidi-safe text markup
# --------------------------------------------------------------------------

# Runs that must keep left-to-right order even inside Arabic sentences.
_LTR_ISLAND = re.compile(
    r"(https?://\S+|www\.\S+|[\w.+-]+@[\w-]+\.[\w.-]+|@[A-Za-z0-9_.]+|#[A-Za-z0-9_]+"
    r"|\+?\d[\d\s\-]{6,}\d)"
)


def to_html(text: str, protect=(), numerals="western", hide_after_word=None,
            highlight_word=None, highlight_color=None) -> str:
    """Escape text and isolate LTR islands (URLs, @handles, phone numbers,
    brand names) with <bdi dir=ltr> so punctuation and order stay correct.

    hide_after_word: index of last visible word (for word-by-word reveals);
    hidden words keep their space so the layout never jumps.
    """
    protect = tuple(p.replace(" ", "\u00a0") for p in protect if p)
    for p in protect:
        text = (text or "").replace(p.replace("\u00a0", " "), p)  # multi-word names stay one unit
    lines = (text or "").split("\n")
    out_lines = []
    word_i = 0
    for line in lines:
        tokens = re.split(r"([ \t\r\f\v]+)", line)
        parts = []
        for tok in tokens:
            if tok == "" or tok.isspace():
                parts.append(html.escape(tok))
                continue
            vis = hide_after_word is None or word_i <= hide_after_word
            hl = highlight_word is not None and word_i == highlight_word
            word_i += 1
            esc = _mark_islands(tok, protect, numerals)
            style = []
            if not vis:
                style.append("visibility:hidden")
            if hl and highlight_color:
                style.append("color:%s" % highlight_color)
            if style:
                esc = '<span style="%s">%s</span>' % (";".join(style), esc)
            parts.append(esc)
        out_lines.append("".join(parts))
    return "<br>".join(out_lines)


def _mark_islands(tok, protect, numerals):
    # Protected brand names (Latin) inside Arabic text
    for name in protect:
        if name and name in tok and not has_arabic(name):
            i = tok.index(name)
            return (_mark_islands(tok[:i], (), numerals) + '<bdi dir="ltr" style="white-space:nowrap">' + html.escape(name)
                    + "</bdi>" + _mark_islands(tok[i + len(name):], (), numerals))
    m = _LTR_ISLAND.search(tok)
    if m:
        return (_plain(tok[:m.start()], numerals) + '<bdi dir="ltr" style="white-space:nowrap">' + html.escape(m.group(0))
                + "</bdi>" + _mark_islands(tok[m.end():], protect, numerals))
    return _plain(tok, numerals)


def _plain(s, numerals):
    # Arabic-Indic digits only for Arabic words or bare numbers, never inside Latin words.
    if numerals == "arabic_indic" and (has_arabic(s) or re.fullmatch(r"[\d.,%:/\-]+", s or "")):
        s = s.translate(AR_DIGITS)
    return html.escape(s)


def count_words(text):
    return len([t for t in re.split(r"\s+", text or "") if t])


# --------------------------------------------------------------------------
# Card HTML
# --------------------------------------------------------------------------

ROLE_SIZE = {  # base font size in px for a 1080-wide frame
    "headline": 92, "title": 110, "subtitle": 58, "body": 46, "cta": 60,
    "caption": 52, "lower_title": 50, "lower_sub": 36, "brand": 84, "handle": 40,
    "watermark": 34,
}


def build_card_html(*, width, height, fmt, text, role="headline", position="center",
                    style=None, brand_style=None, hide_after_word=None,
                    highlight_word=None, background=None, logo=None, extra_html="", after_html="",
                    numerals="western", protect=()):
    """Return a complete HTML document for one transparent full-frame card."""
    style = style or {}
    bs = brand_style or {}
    lang_dir = text_direction(text) if text else "rtl"
    rtl = lang_dir == "rtl"
    scale = width / 1080.0
    if fmt == "landscape":
        scale = height / 1080.0 * 0.95
    size = style.get("size") or ROLE_SIZE.get(role, 60)
    size = round(size * scale)
    weight = style.get("weight") or (800 if role in ("headline", "title", "brand", "cta") else
                                     700 if role in ("caption", "lower_title") else 500)
    color = style.get("color") or bs.get("text_color", "#FFFFFF")
    accent = style.get("accent") or bs.get("accent", "#FFC93C")
    primary = bs.get("primary", "#1F2937")
    font_ar = style.get("font_ar") or (bs.get("font_ar_heading") if role in (
        "headline", "title", "brand", "cta", "lower_title") else bs.get("font_ar_body")) or "Cairo"
    font_lat = style.get("font_latin") or (bs.get("font_latin_heading") if role in (
        "headline", "title", "brand", "cta", "lower_title") else bs.get("font_latin_body")) or "Inter"
    stack = font_stack(font_ar, font_lat, rtl)
    top, right, bottom, left = SAFE_MARGINS.get(fmt, (0.08, 0.06, 0.1, 0.06))
    pad_t, pad_r, pad_b, pad_l = (round(top * height), round(right * width),
                                  round(bottom * height), round(left * width))
    if role != "caption" and position in ("lower", "bottom"):
        pad_b += int(style.get("reserve_bottom", 0))  # keep clear of burned-in captions
    # Arabic needs taller line boxes (ascenders, dots, diacritics)
    line_h = 1.55 if rtl or has_arabic(text) else 1.25
    align = style.get("align") or "center"
    justify = {"top": "flex-start", "center": "center", "bottom": "flex-end",
               "upper": "flex-start", "lower": "flex-end"}.get(position, "center")
    max_lines = style.get("max_lines") or (2 if role == "caption" else 4)
    min_size = round(size * 0.55)

    body_html = to_html(text, protect=protect, numerals=numerals if rtl else "western",
                        hide_after_word=hide_after_word, highlight_word=highlight_word,
                        highlight_color=accent)
    box_css = ""
    # two-layer shadow: soft glow + tight edge keeps white text readable on bright, busy photos
    shadow = "0 %dpx %dpx rgba(0,0,0,.6),0 0 %dpx rgba(0,0,0,.55)" % (
        max(2, round(3 * scale)), max(6, round(14 * scale)), max(2, round(3 * scale)))
    if role == "caption":
        cap_style = style.get("caption_style", bs.get("caption_style", "box"))
        if cap_style == "box":
            box_css = ("background:rgba(0,0,0,.62);border-radius:%dpx;padding:%dpx %dpx;"
                       % (round(18 * scale), round(10 * scale), round(26 * scale)))
            shadow = "none"
        elif cap_style == "brand":
            box_css = ("background:%s;border-radius:%dpx;padding:%dpx %dpx;"
                       % (primary, round(18 * scale), round(10 * scale), round(26 * scale)))
            shadow = "none"
        else:  # outline
            shadow = ("0 0 %dpx #000,0 0 %dpx #000,0 %dpx %dpx rgba(0,0,0,.8)"
                      % (round(3 * scale), round(6 * scale), round(3 * scale), round(10 * scale)))
    elif role == "cta":
        box_css = ("background:%s;color:%s;border-radius:%dpx;padding:%dpx %dpx;"
                   % (accent, bs.get("on_accent", "#111111"), round(60 * scale),
                      round(14 * scale), round(48 * scale)))
        shadow = "none"
        color = bs.get("on_accent", "#111111")
    elif style.get("box"):
        box_css = ("background:%s;border-radius:%dpx;padding:%dpx %dpx;"
                   % (style["box"], round(16 * scale), round(12 * scale), round(28 * scale)))

    bg_css = "transparent"
    if background:
        bg_css = background

    logo_html = ""
    if logo:
        logo_html = '<img class="logo" style="%s" src="%s">' % (logo.get("css", ""), Path(logo["file"]).as_uri())

    return f"""<!doctype html>
<html lang="{'ar' if rtl else 'en'}" dir="{lang_dir}"><head><meta charset="utf-8">
<style>
{font_face_css(bs.get('custom_fonts'))}
html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:{bg_css}}}
.frame{{box-sizing:border-box;width:{width}px;height:{height}px;padding:{pad_t}px {pad_r}px {pad_b}px {pad_l}px;
  display:flex;flex-direction:column;justify-content:{justify};align-items:center;gap:{round(28*scale)}px}}
.t{{font-family:{stack};font-weight:{weight};font-size:{size}px;line-height:{line_h};color:{color};
  text-align:{align};text-shadow:{shadow};letter-spacing:0;word-spacing:0;
  font-feature-settings:"kern" 1,"liga" 1,"calt" 1;font-kerning:normal;
  unicode-bidi:plaintext;direction:{lang_dir};overflow-wrap:break-word;max-width:100%;text-wrap:balance;
  {box_css}}}
.logo{{max-width:{round(width*0.42)}px;max-height:{round(height*0.18)}px;object-fit:contain}}
{style.get('css','')}
</style></head><body><div class="frame">{logo_html}{extra_html}
<div class="t" id="t" data-min="{min_size}" data-lines="{max_lines}">{body_html}</div>{after_html}</div>
<script>
(async function(){{
  try{{ await document.fonts.ready; }}catch(e){{}}
  var el=document.getElementById('t'); if(!el||!el.textContent.trim()) return;
  var min=+el.dataset.min, lines=+el.dataset.lines;
  function lh(){{return parseFloat(getComputedStyle(el).lineHeight)||parseFloat(getComputedStyle(el).fontSize)*1.5;}}
  var guard=0;
  while(guard++<60){{
    var fs=parseFloat(getComputedStyle(el).fontSize);
    var tooTall = el.scrollHeight > lh()*lines + 4 + (parseFloat(getComputedStyle(el).paddingTop)*2||0);
    var fr = el.parentElement, cs = getComputedStyle(fr);
    var avail = fr.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    var tooWide = el.scrollWidth > el.clientWidth + 1 || el.getBoundingClientRect().width > avail + 1;
    var frameOver = document.querySelector('.frame').scrollHeight > {height};
    if(!(tooTall||tooWide||frameOver) || fs<=min) break;
    el.style.fontSize=(fs-2)+'px';
  }}
}})();
</script></body></html>"""


def render_html_to_png(html_text, out_png, width, height, browser=None, timeout=90):
    browser = browser or find_browser()
    if not browser:
        raise StudioError("no_browser")
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="urm-card-") as td:
        src = Path(td) / "card.html"
        src.write_text(html_text, encoding="utf-8")
        cmd = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio",
               "--no-first-run", "--no-default-browser-check", "--disable-extensions",
               "--allow-file-access-from-files", "--force-device-scale-factor=1",
               "--default-background-color=00000000", "--virtual-time-budget=4000",
               "--user-data-dir=%s" % (Path(td) / "profile"),
               "--window-size=%d,%d" % (width, height), "--screenshot=%s" % out_png, src.as_uri()]
        if platform.system() == "Linux" and os.geteuid() == 0:
            cmd.insert(1, "--no-sandbox")
        try:
            subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise StudioError("command_failed", "browser timed out rendering text")
    if not out_png.exists() or out_png.stat().st_size == 0:
        raise StudioError("command_failed", "browser did not produce %s" % out_png.name)
    return out_png


class CardRenderer:
    """Renders many cards in parallel with a content-hash cache."""

    def __init__(self, cache_dir, browser=None, workers=4):
        self.cache = Path(cache_dir)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.browser = browser or find_browser()
        if not self.browser:
            raise StudioError("no_browser")
        self.workers = workers
        self.jobs = []

    def add(self, html_text, width, height):
        key = hashlib.sha1(("%dx%d\n" % (width, height) + html_text).encode("utf-8")).hexdigest()[:16]
        png = self.cache / ("card_%s.png" % key)
        (self.cache / ("card_%s.html" % key)).write_text(html_text, encoding="utf-8")
        if not png.exists():
            self.jobs.append((html_text, png, width, height))
        return png

    def run(self):
        """Render queued cards. Chromium takes several seconds to start, so up
        to 8 cards share one launch: they are stacked as iframes in one tall
        transparent page, captured once, then cut apart with FFmpeg."""
        jobs, self.jobs = self.jobs, []
        uniq = {}
        for j in jobs:
            uniq.setdefault(str(j[1]), j)
        jobs = list(uniq.values())
        if not jobs:
            return
        groups = {}
        for j in jobs:
            groups.setdefault((j[2], j[3]), []).append(j)
        batches = []
        for (w, h), js in groups.items():
            k = max(1, min(8, 15360 // h))
            for i in range(0, len(js), k):
                batches.append((w, h, js[i:i + k]))
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            list(ex.map(lambda b: self._batch(*b), batches))

    def _batch(self, w, h, js):
        if len(js) == 1:
            render_html_to_png(js[0][0], js[0][1], w, h, self.browser)
            return
        frames = "".join(
            '<iframe width="%d" height="%d" scrolling="no" srcdoc="%s"></iframe>' % (w, h, html.escape(j[0], quote=True))
            for j in js)
        page = ("<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;padding:0;"
                "background:transparent}iframe{display:block;border:0;margin:0;padding:0;width:%dpx;height:%dpx;"
                "background:transparent}</style></head><body>%s</body></html>" % (w, h, frames))
        sheet = self.cache / ("batch_%s.png" % hashlib.sha1(page.encode("utf-8")).hexdigest()[:12])
        render_html_to_png(page, sheet, w, h * len(js), self.browser, timeout=180)
        from .media import ffmpeg_bin  # local import avoids a cycle
        n = len(js)
        fc = "[0:v]split=%d%s;" % (n, "".join("[s%d]" % i for i in range(n)))
        fc += ";".join("[s%d]crop=%d:%d:0:%d[o%d]" % (i, w, h, i * h, i) for i in range(n))
        args = [ffmpeg_bin(), "-y", "-v", "error", "-i", str(sheet), "-filter_complex", fc]
        for i, j in enumerate(js):
            args += ["-map", "[o%d]" % i, "-frames:v", "1", str(j[1])]
        subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
        try:
            sheet.unlink()
        except OSError:
            pass
