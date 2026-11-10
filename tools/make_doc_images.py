#!/usr/bin/env python3
"""Regenerate the illustrative images in docs/images/ (bilingual, rendered with the bundled fonts).

  python3 tools/make_doc_images.py [--reel-frames PATH.png] [--brand-preview DIR]
"""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skill" / "urm-creator-studio" / "scripts"))
from urmstudio.textrender import font_face_css, render_html_to_png  # noqa: E402

OUT = ROOT / "docs" / "images"
BASE = """<!doctype html><html><head><meta charset="utf-8"><style>%s
html,body{margin:0;background:#0f172a;color:#f8fafc;font-family:'Tajawal','Inter',sans-serif}
.ar{font-family:'Cairo';direction:rtl}.en{font-family:'Inter'}
%s</style></head><body>%s</body></html>"""


def page(css, body):
    return BASE % (font_face_css(), css, body)


def formats():
    css = """.wrap{display:flex;gap:56px;align-items:flex-end;justify-content:center;padding:60px 40px 40px}
.item{display:flex;flex-direction:column;align-items:center;gap:18px}
.box{border:6px solid #38bdf8;border-radius:22px;background:linear-gradient(160deg,#1e3a8a,#0ea5e9);
display:flex;align-items:center;justify-content:center;font:800 40px Inter;color:#fff}
.l1{font:700 34px Cairo;direction:rtl}.l2{font:500 24px Inter;color:#94a3b8;text-align:center}"""
    items = [("9:16", 216, 384, "طولي", "Vertical · Reels, TikTok, Shorts"),
             ("4:5", 288, 360, "عمودي", "Portrait · Instagram feed"),
             ("1:1", 300, 300, "مربع", "Square · posts"),
             ("16:9", 480, 270, "عرضي", "Landscape · YouTube, website")]
    body = '<div class="wrap">' + "".join(
        '<div class="item"><div class="box" style="width:%dpx;height:%dpx">%s</div><div class="l1">%s</div>'
        '<div class="l2">%s</div></div>' % (w, h, r, ar, en) for r, w, h, ar, en in items) + "</div>"
    render_html_to_png(page(css, body), OUT / "formats.png", 1600, 640)


def arabic_compare():
    word = "خصم ٢٠٪ على قهوتك المفضلة"
    broken = "‌".join(reversed(word))  # what naive tools do: letters isolated and order reversed
    css = """.g{display:grid;grid-template-columns:1fr 1fr;gap:40px;padding:50px}
.c{border-radius:24px;padding:40px;display:flex;flex-direction:column;gap:24px;align-items:center}
.ok{background:#064e3b}.bad{background:#7f1d1d}
.t{font:800 64px Cairo;line-height:1.6}.h{font:700 30px Cairo}.s{font:500 24px Inter;color:#e2e8f0}"""
    body = ('<div class="g"><div class="c ok"><div class="h ar">✅ صحيح — استوديو URM</div>'
            '<div class="t ar">%s</div><div class="s">Correct: joined letters, right-to-left</div></div>'
            '<div class="c bad"><div class="h ar">❌ خطأ شائع في أدوات أخرى</div>'
            '<div class="t ar">%s</div>'
            '<div class="s">Common bug elsewhere: letters split, order reversed</div></div></div>' % (word, broken))
    render_html_to_png(page(css, body), OUT / "arabic-correct-vs-wrong.png", 1600, 520)


def install_flow():
    steps = [("١", "نزّل الحزمة وفكّ ضغطها", "Download & unzip the package", "📦"),
             ("٢", "انقر مرتين على ملف التثبيت", "Double-click the installer", "🖱️"),
             ("٣", "افتح Claude Code", "Open Claude Code", "💬"),
             ("٤", "اكتب: أريد صنع فيديو", "Type: I want to make a video", "🎬")]
    css = """.row{display:flex;flex-direction:row-reverse;gap:28px;padding:50px;justify-content:center;align-items:stretch}
.s{width:330px;background:#1e293b;border:3px solid #334155;border-radius:26px;padding:30px 24px;display:flex;
flex-direction:column;align-items:center;gap:14px;text-align:center}
.n{width:70px;height:70px;border-radius:50%;background:#38bdf8;color:#0f172a;font:800 40px Cairo;display:flex;
align-items:center;justify-content:center}.i{font-size:64px}.a{font:700 30px Cairo;direction:rtl;line-height:1.5}
.e{font:500 22px Inter;color:#94a3b8}.arrow{align-self:center;font:700 50px Inter;color:#38bdf8}"""
    parts = []
    for k, (n, ar, en, ic) in enumerate(steps):
        parts.append('<div class="s"><div class="n">%s</div><div class="i">%s</div><div class="a">%s</div>'
                     '<div class="e">%s</div></div>' % (n, ic, ar, en))
        if k < len(steps) - 1:
            parts.append('<div class="arrow">←</div>')
    render_html_to_png(page(css, '<div class="row">%s</div>' % "".join(parts)), OUT / "install-flow.png", 1760, 480)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reel-frames")
    ap.add_argument("--brand-preview")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    formats()
    arabic_compare()
    install_flow()
    if a.reel_frames:
        shutil.copy2(a.reel_frames, OUT / "example-arabic-reel.png")
    if a.brand_preview:
        for n in ("intro", "outro"):
            shutil.copy2(Path(a.brand_preview) / ("%s.png" % n), OUT / ("brand-preview-%s.png" % n))
    print("images in", OUT)


if __name__ == "__main__":
    main()
