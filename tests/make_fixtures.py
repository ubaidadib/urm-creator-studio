#!/usr/bin/env python3
"""Generate synthetic, licence-free test media (no real people, no private footage).

  python3 tests/make_fixtures.py OUT_DIR

Creates: landscape & vertical clips, two photos, a music bed made from sine
tones, Arabic and English speech clips (macOS system voices, labelled
synthetic), and three fictional logos.
"""
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skill" / "urm-creator-studio" / "scripts"))
from urmstudio.textrender import render_html_to_png, font_face_css  # noqa: E402


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *map(str, args)], check=True)


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    # moving abstract footage
    ff("-f", "lavfi", "-i", "gradients=s=1920x1080:c0=0x0f766e:c1=0xf59e0b:c2=0x1e3a8a:n=3:speed=0.015:d=8:r=30",
       "-f", "lavfi", "-i", "sine=f=220:d=8:sample_rate=48000", "-filter_complex",
       "[0:v]noise=alls=4:allf=t,format=yuv420p[v];[1:a]volume=0.15[a]", "-map", "[v]", "-map", "[a]",
       "-c:v", "libx264", "-crf", "26", "-c:a", "aac", "-shortest", out / "clip_landscape.mp4")
    ff("-f", "lavfi", "-i", "gradients=s=1080x1920:c0=0x7c3aed:c1=0xec4899:c2=0x0ea5e9:n=3:speed=0.02:d=6:r=30",
       "-vf", "noise=alls=4:allf=t,format=yuv420p", "-c:v", "libx264", "-crf", "26", "-an",
       out / "clip_vertical_silent.mp4")
    # photos
    ff("-f", "lavfi", "-i", "mandelbrot=s=1600x1200:end_scale=0.3", "-frames:v", "1", out / "photo_landscape.jpg")
    ff("-f", "lavfi", "-i", "gradients=s=1200x1600:c0=0xfde68a:c1=0x92400e:n=2:x0=0:y0=0:x1=1200:y1=1600",
       "-frames:v", "1", out / "photo_portrait.jpg")
    # music bed: simple A-minor pad from sine tones (our own, licence-free)
    ff("-f", "lavfi", "-i", "sine=f=220:d=30", "-f", "lavfi", "-i", "sine=f=261.63:d=30", "-f", "lavfi",
       "-i", "sine=f=329.63:d=30", "-filter_complex",
       "[0][1][2]amix=inputs=3,volume=0.6,tremolo=f=0.5:d=0.4,afade=t=in:d=2,aformat=channel_layouts=stereo",
       "-ar", "48000", out / "music_pad.wav")
    # synthetic speech (macOS voices) – used to test transcription and ducking
    if platform.system() == "Darwin" and shutil.which("say"):
        ar = ("مرحبًا بكم في مقهى الريحان. نقدّم لكم قهوة مختصة محمّصة يوميًا، "
              "وحلويات طازجة كل صباح. زورونا اليوم واستمتعوا بخصم خاص.")
        en = "Hi everyone, welcome back to the channel. Today I will show you three simple tips to stay focused."
        for lang, voice, text in (("ar", "Majed", ar), ("en", "Samantha", en)):
            aiff = out / ("speech_%s.aiff" % lang)
            subprocess.run(["say", "-v", voice, "-o", str(aiff), text], check=True)
            ff("-f", "lavfi", "-i", "gradients=s=1080x1920:c0=0x334155:c1=0x0f172a:speed=0.01:r=30",
               "-i", aiff, "-map", "0:v", "-map", "1:a", "-shortest", "-c:v", "libx264", "-crf", "22",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", out / ("speech_%s.mp4" % lang))
            aiff.unlink()
    # fictional logos (transparent PNG)
    css = font_face_css()
    logos = {
        "logo_arabic.png": ('<div style="width:600px;height:600px;border-radius:50%;background:#14532d;'
                            'display:flex;align-items:center;justify-content:center;flex-direction:column">'
                            '<div style="font:700 150px Amiri;color:#fef3c7;line-height:1.2">الريحان</div>'
                            '<div style="font:500 44px Tajawal;color:#fde68a">مقهى ومحمصة</div></div>', 600, 600),
        "logo_english.png": ('<div style="width:900px;height:300px;display:flex;align-items:center;'
                             'justify-content:center;font:900 150px Inter;color:#f97316;letter-spacing:-4px">'
                             'sami<span style="color:#fff">makes</span></div>', 900, 300),
        "logo_bilingual.png": ('<div style="width:900px;height:420px;display:flex;flex-direction:column;'
                               'align-items:center;justify-content:center;gap:0">'
                               '<div style="font:800 140px Cairo;color:#e0f2fe;line-height:1.3">دار السَّنا</div>'
                               '<div style="font:600 64px Inter;color:#38bdf8;letter-spacing:6px">DAR AL-SANA</div></div>',
                               900, 420),
    }
    for name, (body, w, h) in logos.items():
        page = ("<!doctype html><html><head><meta charset='utf-8'><style>%s html,body{margin:0;background:transparent}"
                "</style></head><body>%s</body></html>" % (css, body))
        render_html_to_png(page, out / name, w, h)
    print("fixtures ready in", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fixtures")
