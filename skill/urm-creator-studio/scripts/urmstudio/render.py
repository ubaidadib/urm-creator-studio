"""Plan -> finished video. All work happens inside the project folder;
source media is only ever read.

Pipeline
  1. text cards (headlines, lower thirds, captions, intro/outro) -> transparent PNGs via Chromium
  1b. motion-design scenes (creative-led production) -> frame-by-frame canvas renders via Chromium (motion.py)
  1c. original soundtrack + sound design when the plan asks for a score and has no music file
  2. one normalised segment per scene (framing, motion, speed, scene text animation)
  3. join segments (cut or transition)
  4. final pass: lower thirds, captions, watermark, music + ducking, loudness
  5. quality control report (see qc.py)
"""
import datetime
import hashlib
import html
import json
import math
import os
import shutil
import time
from pathlib import Path

from . import brand as brandmod
from . import looks as looksmod
from .captions import parse as parse_captions, write_srt, write_vtt, check as check_captions
from .common import (FORMATS, SAFE_MARGINS, StudioError, VERSION, read_json, run, studio_home,
                     text_direction, write_json, has_arabic)
from .media import ffmpeg_bin, kind_of, probe
from .motion import MotionStudio, render_score, validate_motion_scene
from .textrender import (CardRenderer, build_card_html, count_words, font_face_css, font_stack,
                         to_html)

ENC_FINAL = {"standard": ("20", "medium"), "high": ("17", "slow"), "preview": ("28", "ultrafast")}
XFADE_OK = {"fade", "dissolve", "slideleft", "slideright", "slideup", "slidedown", "smoothleft",
            "smoothright", "circleopen", "wipeleft", "wiperight", "fadeblack", "fadewhite", "zoomin"}


# --------------------------------------------------------------------------
# Plan loading & validation
# --------------------------------------------------------------------------

def load_plan(project_dir):
    p = Path(project_dir) / "plan.json"
    if not p.exists():
        raise StudioError("not_found", str(p))
    try:
        plan = read_json(p)
    except json.JSONDecodeError as e:
        raise StudioError("bad_plan", "plan.json is not valid JSON (%s)" % e)
    return plan


def resolve_src(project_dir, src):
    if not src:
        return None
    p = Path(os.path.expanduser(str(src)))
    if not p.is_absolute():
        p = Path(project_dir) / p
    return p


def validate_plan(plan, project_dir):
    errs = []
    fmt = plan.get("format", "vertical")
    if fmt not in FORMATS:
        errs.append("format must be one of %s" % ", ".join(FORMATS))
    scenes = plan.get("scenes") or []
    if not scenes:
        errs.append("the plan has no scenes")
    for i, sc in enumerate(scenes, 1):
        k = sc.get("kind")
        if k not in ("video", "image", "title", "motion"):
            errs.append("scene %d: kind must be video, image, title or motion" % i)
            continue
        if k == "motion":
            errs += validate_motion_scene(i, sc, project_dir)
        if k in ("video", "image"):
            src = resolve_src(project_dir, sc.get("src"))
            if not src or not src.exists():
                errs.append("scene %d: file not found: %s" % (i, sc.get("src")))
        if k == "video":
            s, e = float(sc.get("start", 0)), sc.get("end")
            if e is not None and float(e) <= s:
                errs.append("scene %d: end must be after start" % i)
        for t in sc.get("texts", []):
            if not str(t.get("text", "")).strip():
                errs.append("scene %d: a text item is empty" % i)
    cap = plan.get("captions") or {}
    if cap.get("src"):
        cp = resolve_src(project_dir, cap["src"])
        if not cp.exists():
            errs.append("captions file not found: %s" % cap["src"])
    au = plan.get("audio") or {}
    for key in ("music", "voiceover"):
        v = au.get(key)
        src = v.get("src") if isinstance(v, dict) else v
        if src and not resolve_src(project_dir, src).exists():
            errs.append("%s file not found: %s" % (key, src))
    if errs:
        raise StudioError("bad_plan", " | ".join(errs))


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def next_version_dir(project_dir, preview=False):
    """Finals: output/v001, v002… Previews: output/preview-001… (they never use up a version number)."""
    out = Path(project_dir) / "output"
    out.mkdir(parents=True, exist_ok=True)
    prefix, pattern = ("preview-", "preview-[0-9][0-9][0-9]") if preview else ("v", "v[0-9][0-9][0-9]")
    n = 1
    for d in out.glob(pattern):
        n = max(n, int(d.name[len(prefix):]) + 1)
    v = out / ("%s%03d" % (prefix, n))
    v.mkdir()
    return v


def fingerprint(paths):
    res = {}
    for p in paths:
        p = Path(p)
        if p.exists():
            st = p.stat()
            h = hashlib.sha1()
            with open(p, "rb") as f:
                h.update(f.read(1 << 20))  # first MiB is enough to catch rewrites
            res[str(p)] = [st.st_size, int(st.st_mtime), h.hexdigest()]
    return res


def _atempo_chain(speed):
    parts, s = [], speed
    while s > 2.0:
        parts.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        parts.append("atempo=0.5")
        s /= 0.5
    parts.append("atempo=%.4f" % s)
    return ",".join(parts)


def _ease_y(start, dur=0.45, dist=70):
    # cubic ease-out offset that reaches 0 after `dur` seconds
    return "if(lt(t,%.3f),%d,if(lt(t,%.3f),%d*pow(1-(t-%.3f)/%.3f,3),0))" % (
        start, dist, start + dur, dist, start, dur)


def _ease_x(start, dur, dist):
    return "if(lt(t,%.3f),%d,if(lt(t,%.3f),%d*pow(1-(t-%.3f)/%.3f,3),0))" % (
        start, dist, start + dur, dist, start, dur)


class Ctx:
    pass


# --------------------------------------------------------------------------
# Scene expansion (intro/outro from brand)
# --------------------------------------------------------------------------

def expand_scenes(plan, brand, lang):
    scenes = [dict(s) for s in plan.get("scenes", [])]
    br = plan.get("branding") or {}
    has_brand = brand is not None
    intro_on = br.get("intro", has_brand and brand.get("intro", {}).get("enabled", True))
    outro_on = br.get("outro", has_brand and brand.get("outro", {}).get("enabled", True))
    out = []
    if intro_on and has_brand:
        out.append({"kind": "title", "_role": "intro",
                    "duration": float(br.get("intro_duration", brand.get("intro", {}).get("duration", 2.0)))})
    out += scenes
    cta_plan = br.get("cta")
    if outro_on and (has_brand or cta_plan):
        out.append({"kind": "title", "_role": "outro", "cta": cta_plan,
                    "duration": float(br.get("outro_duration",
                                             (brand or {}).get("outro", {}).get("duration", 3.0)))})
    return out


def scene_duration(sc, info=None):
    k = sc["kind"]
    if k == "video":
        start = float(sc.get("start", 0))
        end = sc.get("end")
        full = info["duration"] if info else 0
        end = float(end) if end is not None else full
        end = min(end, full) if full else end
        return max(0.2, (end - start) / float(sc.get("speed", 1) or 1))
    if k == "motion":
        return round(float(sc.get("duration", 3.0)) * 30) / 30.0  # whole frames
    return float(sc.get("duration", 3.0))


# --------------------------------------------------------------------------
# Card builders
# --------------------------------------------------------------------------

def background_html(W, H, bs, kind="gradient"):
    p, s = bs["primary"], bs["secondary"]
    if kind == "solid":
        bg = p
    else:
        bg = ("radial-gradient(120%% 80%% at 50%% 30%%, %s 0%%, %s 55%%, %s 100%%)" % (s, p, _darken(p)))
    return ("<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;width:%dpx;"
            "height:%dpx;overflow:hidden;background:%s}</style></head><body></body></html>" % (W, H, bg))


def _darken(hexc, f=0.55):
    hexc = hexc.lstrip("#")
    r, g, b = (int(hexc[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f))


def lower_third_html(W, H, fmt, title, subtitle, bs, protect=(), reserve=0):
    rtl = text_direction(title or subtitle) == "rtl"
    scale = W / 1080.0 if fmt != "landscape" else H / 1080.0 * 0.95
    top, right, bottom, left = SAFE_MARGINS[fmt]
    side_pad = round((right if rtl else left) * W)
    stack_h = font_stack(bs["font_ar_heading"], bs["font_latin_heading"], rtl)
    stack_b = font_stack(bs["font_ar_body"], bs["font_latin_body"], rtl)
    lh = 1.5 if rtl else 1.2
    bar_side = "right" if rtl else "left"
    numerals = bs.get("numerals", "western") if rtl else "western"
    return f"""<!doctype html><html dir="{'rtl' if rtl else 'ltr'}" lang="{'ar' if rtl else 'en'}"><head><meta charset="utf-8"><style>
{font_face_css(bs.get('custom_fonts'))}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:transparent}}
.wrap{{position:absolute;bottom:{round(bottom*H + 40*scale + reserve)}px;{bar_side}:{side_pad}px;max-width:{round(W*0.78)}px;
  display:flex;flex-direction:column;align-items:flex-start;gap:{round(6*scale)}px}}
.ti{{font-family:{stack_h};font-weight:800;font-size:{round(50*scale)}px;line-height:{lh};color:#fff;
  background:{bs['primary']};padding:{round(8*scale)}px {round(24*scale)}px;border-{bar_side}:{round(10*scale)}px solid {bs['accent']};
  border-radius:{round(8*scale)}px;letter-spacing:0;unicode-bidi:plaintext}}
.su{{font-family:{stack_b};font-weight:500;font-size:{round(36*scale)}px;line-height:{lh};color:#111;
  background:rgba(255,255,255,.93);padding:{round(6*scale)}px {round(22*scale)}px;border-radius:{round(8*scale)}px;
  letter-spacing:0;unicode-bidi:plaintext}}
</style></head><body><div class="wrap">
{'<div class="ti">%s</div>' % to_html(title, protect, numerals) if title else ''}
{'<div class="su">%s</div>' % to_html(subtitle, protect, numerals) if subtitle else ''}
</div></body></html>"""


def intro_card(W, H, fmt, brand, bs, lang):
    name = brandmod.display_name(brand, lang)
    logo = brandmod.logo_file(brand)
    tagline = (brand.get("tagline") or {}).get(lang) or ""
    if logo:
        after = ""
        if tagline:
            after = '<div class="t2" style="font-family:%s;font-size:%dpx;color:%s;opacity:.92;line-height:1.5;unicode-bidi:plaintext">%s</div>' % (
                font_stack(bs["font_ar_body"], bs["font_latin_body"], has_arabic(tagline)),
                round(40 * W / 1080), bs["text_color"], to_html(tagline, brandmod.protected_terms(brand)))
        return build_card_html(width=W, height=H, fmt=fmt, text=name, role="brand", position="center",
                               brand_style=bs, logo={"file": str(logo)}, after_html=after,
                               protect=brandmod.protected_terms(brand), numerals=bs.get("numerals"))
    # no logo: typographic wordmark (both names for bilingual brands)
    n = brand.get("name", {})
    text = name
    sub = ""
    if n.get("ar") and n.get("en"):
        text = n["ar"] if lang == "ar" else n["en"]
        sub = n["en"] if lang == "ar" else n["ar"]
    after = ""
    if sub or tagline:
        after = '<div style="font-family:%s;font-weight:600;font-size:%dpx;color:%s;opacity:.9;line-height:1.5;unicode-bidi:plaintext;text-align:center">%s</div>' % (
            font_stack(bs["font_ar_body"], bs["font_latin_body"], has_arabic(sub or tagline)),
            round(44 * W / 1080), bs["text_color"],
            "<br>".join(to_html(x, brandmod.protected_terms(brand)) for x in (sub, tagline) if x))
    return build_card_html(width=W, height=H, fmt=fmt, text=text, role="title", position="center",
                           brand_style=bs, after_html=after, protect=brandmod.protected_terms(brand),
                           numerals=bs.get("numerals"))


def outro_card(W, H, fmt, brand, bs, lang, cta_override=None):
    cta = cta_override
    if isinstance(cta, dict):
        cta = cta.get(lang) or cta.get("ar") or cta.get("en")
    if not cta and brand:
        c = (brand.get("outro") or {}).get("cta") or {}
        cta = c.get(lang) or c.get("ar" if lang == "ar" else "en") or ""
    if not cta:
        cta = "تابعونا" if lang == "ar" else "Follow us"
    logo = brandmod.logo_file(brand) if brand else None
    handles_html = ""
    if brand and (brand.get("outro") or {}).get("show_handles", True):
        hs = [(k, v) for k, v in (brand.get("handles") or {}).items() if v]
        if hs:
            labels = {"instagram": "Instagram", "tiktok": "TikTok", "youtube": "YouTube", "snapchat": "Snapchat",
                      "x": "X", "facebook": "Facebook", "linkedin": "LinkedIn", "website": "", "whatsapp": "WhatsApp"}
            if lang == "ar":
                labels.update({"instagram": "إنستغرام", "tiktok": "تيك توك", "youtube": "يوتيوب",
                               "snapchat": "سناب شات", "facebook": "فيسبوك", "linkedin": "لينكدإن",
                               "whatsapp": "واتساب"})
            rows = "".join(
                '<div dir="%s" style="unicode-bidi:isolate">%s<bdi dir="ltr"><b>%s</b></bdi></div>' % (
                    "rtl" if lang == "ar" else "ltr",
                    (html.escape(labels.get(k, k)) + " &nbsp;") if labels.get(k, k) else "", html.escape(v))
                for k, v in hs[:4])
            handles_html = ('<div style="font-family:%s;font-size:%dpx;color:%s;line-height:1.6;text-align:center;opacity:.95">%s</div>'
                            % (font_stack(bs["font_ar_body"], bs["font_latin_body"], False), round(38 * W / 1080),
                               bs["text_color"], rows))
    name_html = ""
    if brand and not logo:
        nm = brandmod.display_name(brand, lang)
        name_html = ('<div style="font-family:%s;font-weight:800;font-size:%dpx;color:%s;line-height:1.5;unicode-bidi:plaintext">%s</div>'
                     % (font_stack(bs["font_ar_heading"], bs["font_latin_heading"], has_arabic(nm)),
                        round(76 * W / 1080), bs["text_color"], to_html(nm, brandmod.protected_terms(brand))))
    return build_card_html(width=W, height=H, fmt=fmt, text=cta, role="cta", position="center",
                           brand_style=bs, logo={"file": str(logo), "css": "max-height:%dpx" % round(H * 0.14)} if logo else None,
                           extra_html=name_html, after_html=handles_html,
                           protect=brandmod.protected_terms(brand), numerals=bs.get("numerals"))


# --------------------------------------------------------------------------
# Segment building
# --------------------------------------------------------------------------

def framing_filter(mode, W, H, src_w, src_h, focus="center", tint=None):
    if mode == "auto":
        if src_w and src_h:
            r_src, r_dst = src_w / src_h, W / H
            mode = "fit_blur" if max(r_src, r_dst) / min(r_src, r_dst) > 1.3 else "fill"
        else:
            mode = "fill"
    if mode == "fit_blur":
        # blurred, darkened copy fills the frame; the full picture sits on top
        return ("split=2[fbA][fbB];[fbA]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,"
                "boxblur=luma_radius=10:luma_power=2,scale=%d:%d,eq=brightness=-0.08%s[fbBG];"
                "[fbB]scale=%d:%d:force_original_aspect_ratio=decrease[fbFG];"
                "[fbBG][fbFG]overlay=(W-w)/2:(H-h)/2"
                % (W // 4, H // 4, W // 4, H // 4, W, H,
                   # creative/mixed: the blurred surround takes the look's stage colour, so footage sits
                   # inside the same visual world as the motion scenes
                   (",drawbox=x=0:y=0:w=iw:h=ih:color=0x%s@0.62:t=fill" % tint.lstrip("#")) if tint else "",
                   W, H))
    if mode == "fit_color":
        return ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=black"
                % (W, H, W, H))
    cx = {"left": "0", "right": "iw-ow", "center": "(iw-ow)/2"}.get(focus, "(iw-ow)/2")
    cy = {"top": "0", "bottom": "ih-oh"}.get(focus, "(ih-oh)/2")
    return "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d:%s:%s" % (W, H, W, H, cx, cy)


def hdr_filter(info):
    if not info or not info.get("hdr"):
        return ""
    # Without zscale we cannot tone-map properly; convert primaries and warn in QC.
    return "colorspace=all=bt709:iall=bt2020:fast=1,"


def build_segment(ctx, idx, sc, out_path):
    W, H, fps = ctx.W, ctx.H, ctx.fps
    dur = sc["_dur"]
    args = [ffmpeg_bin(), "-y", "-v", "error", "-nostdin"]
    fc = []
    kind = sc["kind"]
    has_audio = False
    if kind in ("video", "motion"):
        src = sc["_src"]
        info = sc["_info"]
        motion = kind == "motion"  # a rendered motion-design clip: exact size, silent, untrimmed
        start = 0.0 if motion else float(sc.get("start", 0))
        speed = 1.0 if motion else float(sc.get("speed", 1) or 1)
        args += ["-ss", "%.3f" % start, "-t", "%.3f" % (dur * speed + 0.05), "-i", str(src)]
        vf = hdr_filter(info) + framing_filter("fill" if motion else sc.get("framing", "auto"), W, H, info.get("width"),
                                               info.get("height"), sc.get("focus", "center"), getattr(ctx, "tint", None))
        if speed != 1:
            vf = "setpts=PTS/%.4f," % speed + vf
        fc.append("[0:v]%s,fps=%s,setsar=1,format=yuv420p[base0]" % (vf, fps))
        vol = 0.0 if motion else float(sc.get("volume", 1.0))
        if info.get("has_audio") and vol > 0:
            has_audio = True
            a = "[0:a]aresample=48000,aformat=channel_layouts=stereo,volume=%.3f" % vol
            if speed != 1:
                a += "," + _atempo_chain(speed)
            a += ",apad,atrim=0:%.3f,afade=t=in:d=0.04,afade=t=out:st=%.3f:d=0.06[aout]" % (dur, max(0, dur - 0.06))
            fc.append(a)
    elif kind == "image":
        src = sc["_src"]
        info = sc["_info"]
        motion = sc.get("motion", "zoom_in")
        frames = max(1, int(round(dur * fps)))
        if motion == "none":
            args += ["-loop", "1", "-t", "%.3f" % dur, "-i", str(src)]
            fc.append("[0:v]%s,fps=%s,setsar=1,format=yuv420p[base0]" % (
                framing_filter(sc.get("framing", "auto"), W, H, info.get("width"), info.get("height"),
                               sc.get("focus", "center"), getattr(ctx, "tint", None)), fps))
        else:
            args += ["-i", str(src)]
            W2, H2 = int(W * 1.5) // 2 * 2, int(H * 1.5) // 2 * 2
            pre = framing_filter(sc.get("framing", "auto"), W2, H2, info.get("width"), info.get("height"),
                                 sc.get("focus", "center"), getattr(ctx, "tint", None))
            z = {"zoom_in": "1+0.10*on/%d" % frames, "zoom_out": "1.10-0.10*on/%d" % frames}.get(motion, "1.10")
            x = "iw/2-(iw/zoom/2)"
            if motion == "pan_left":
                x = "(iw-iw/zoom)*(1-on/%d)" % frames
            elif motion == "pan_right":
                x = "(iw-iw/zoom)*on/%d" % frames
            fc.append("[0:v]%s,zoompan=z='%s':x='%s':y='ih/2-(ih/zoom/2)':d=%d:s=%dx%d:fps=%s,setsar=1,"
                      "format=yuv420p,trim=duration=%.3f[base0]" % (pre, z, x, frames, W, H, fps, dur))
    else:  # title / intro / outro
        args += ["-loop", "1", "-t", "%.3f" % dur, "-i", str(sc["_bg"])]
        fc.append("[0:v]scale=%d:%d,fps=%s,setsar=1,format=yuv420p[base0]" % (W, H, fps))

    # scene text overlays
    cur = "base0"
    n_in = 1
    for j, ov in enumerate(sc.get("_overlays", [])):
        st, en, anim = ov["start"], ov["end"], ov.get("animation", "fade")
        pngs = ov["pngs"]
        if anim in ("words", "typewriter") and len(pngs) > 1:
            hold = 1.5 + 0.3 * len(pngs)  # full text must stay readable this long
            step = min(0.45, (en - st - hold) / len(pngs))
            if step < 0.08:  # not enough time: reveal everything at once instead
                anim, pngs = "slide_up", [pngs[-1]]
        if anim in ("words", "typewriter") and len(pngs) > 1:
            for w, png in enumerate(pngs):
                a = st + w * step
                b = st + (w + 1) * step if w < len(pngs) - 1 else en
                args += ["-loop", "1", "-t", "%.3f" % dur, "-i", str(png)]
                lab = "w%d_%d" % (j, w)
                f = "[%d:v]format=rgba" % n_in
                if w == len(pngs) - 1:
                    f += ",fade=t=out:st=%.3f:d=0.3:alpha=1" % max(a, en - 0.3)
                fc.append(f + "[%s]" % lab)
                fc.append("[%s][%s]overlay=0:0:enable='between(t,%.3f,%.3f)'[v%d_%d]" % (cur, lab, a, b, j, w))
                cur = "v%d_%d" % (j, w)
                n_in += 1
            continue
        args += ["-loop", "1", "-t", "%.3f" % dur, "-i", str(pngs[0])]
        lab = "o%d" % j
        f = "[%d:v]format=rgba" % n_in
        if anim != "none":
            f += ",fade=t=in:st=%.3f:d=0.4:alpha=1,fade=t=out:st=%.3f:d=0.35:alpha=1" % (st, max(st, en - 0.35))
        x, y = "0", "0"
        if anim == "slide_up":
            y = _ease_y(st)
        elif anim == "slide_side":
            x = _ease_x(st, 0.5, (-90 if ctx.rtl else 90))
        elif anim == "zoom":
            f += ",scale=w='iw*(0.86+0.14*min(1,max(0,(t-%.3f)/0.45)))':h=-1:eval=frame" % st
            x, y = "(W-w)/2", "(H-h)/2"
        fc.append(f + "[%s]" % lab)
        fc.append("[%s][%s]overlay=x='%s':y='%s':enable='between(t,%.3f,%.3f)'[v%d]" % (cur, lab, x, y, st, en, j))
        cur = "v%d" % j
        n_in += 1

    if not has_audio:
        fc.append("anullsrc=r=48000:cl=stereo,atrim=0:%.3f[aout]" % dur)
    fc.append("[%s]trim=duration=%.3f,setpts=PTS-STARTPTS[vout]" % (cur, dur))
    args += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
             "-c:v", ctx.vcodec, *ctx.inter_opts, "-r", str(fps),
             "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-t", "%.3f" % dur, str(out_path)]
    ctx.log.append(" ".join(_q(a) for a in args))
    run(args, timeout=60 * 30)
    return out_path


def _q(a):
    a = str(a)
    return "'%s'" % a if (" " in a or ";" in a or "[" in a) else a


# --------------------------------------------------------------------------
# Join + final pass
# --------------------------------------------------------------------------

def boundary_plan(ctx, scenes, durs, transition):
    """Transition for every boundary i (between scene i-1 and i): (xfade type, duration) or ("cut", 0).

    Two motion scenes meet with a hard cut: their designed transitions are drawn inside the frames and the
    background world is continuous, so the cut is invisible. Intro/outro always dissolve gently.
    """
    ttype = (transition or {}).get("type", "fade")
    td = float((transition or {}).get("duration", 0.35))
    if ttype == "slide":
        ttype = "slideright" if ctx.rtl else "slideleft"  # RTL stories move the other way
    if ttype not in XFADE_OK:
        ttype = "none"
    bounds = [None]
    for i in range(1, len(scenes)):
        a, b = scenes[i - 1], scenes[i]
        cap = min(durs[i - 1], durs[i]) / 2.5
        if a["kind"] == "motion" and b["kind"] == "motion":
            bounds.append(("cut", 0.0))
        elif b.get("_role") == "outro" or a.get("_role") == "intro":
            bounds.append(("fade", min(max(td, 0.3), cap)))
        elif ttype == "none":
            bounds.append(("cut", 0.0))
        else:
            bounds.append((ttype, min(td, cap)))
    return bounds


def _concat(segs, out_path):
    lst = out_path.with_suffix(".txt")
    lst.write_text("".join("file '%s'\n" % str(s).replace("'", "'\\''") for s in segs), encoding="utf-8")
    run([ffmpeg_bin(), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out_path)])
    return out_path


def join_segments(ctx, segs, durs, out_path, bounds):
    """Hard cuts are joined losslessly first (concat); dissolves/wipes then run between those groups. A cut is
    never faked as a one-frame crossfade: xfade drops the rest of the video when frame rounding leaves its
    first input a hair shorter than offset + duration."""
    if len(segs) == 1 or all(bd[1] == 0 for bd in bounds[1:]):
        _concat(segs, out_path)
        return [sum(durs[:i]) for i in range(len(durs))], sum(durs)
    groups = [[0]]
    for i in range(1, len(segs)):
        if bounds[i][1] == 0:
            groups[-1].append(i)
        else:
            groups.append([i])
    gfiles, gdurs, gbounds = [], [], [None]
    for n, g in enumerate(groups):
        if len(g) == 1:
            gfiles.append(segs[g[0]])
        else:
            gfiles.append(_concat([segs[i] for i in g], out_path.with_name("group_%02d.mp4" % n)))
        gdurs.append(sum(durs[i] for i in g))
        if n:
            gbounds.append(bounds[g[0]])
    args = [ffmpeg_bin(), "-y", "-v", "error", "-nostdin"]
    for s in gfiles:
        args += ["-i", str(s)]
    fc = []
    vprev, aprev = "0:v", "0:a"
    offset = 0.0
    for i in range(1, len(gfiles)):
        tt, td = gbounds[i]
        offset += gdurs[i - 1] - td
        fc.append("[%s][%d:v]xfade=transition=%s:duration=%.4f:offset=%.4f[xv%d]" % (vprev, i, tt, td, offset, i))
        fc.append("[%s][%d:a]acrossfade=d=%.4f:c1=tri:c2=tri[xa%d]" % (aprev, i, td, i))
        vprev, aprev = "xv%d" % i, "xa%d" % i
    total = offset + gdurs[-1]
    args += ["-filter_complex", ";".join(fc), "-map", "[%s]" % vprev, "-map", "[%s]" % aprev,
             "-c:v", ctx.vcodec, *ctx.inter_opts, "-r", str(ctx.fps), "-c:a", "aac", "-b:a", "256k",
             str(out_path)]
    ctx.log.append(" ".join(_q(a) for a in args))
    run(args, timeout=60 * 60)
    starts, acc = [], 0.0
    for i, d in enumerate(durs):
        starts.append(acc)
        acc += d - (bounds[i + 1][1] if i < len(durs) - 1 else 0)
    return starts, total


def whoosh_wav(path):
    if Path(path).exists():
        return path
    run([ffmpeg_bin(), "-y", "-v", "error", "-f", "lavfi", "-i",
         "anoisesrc=color=pink:duration=0.6:amplitude=0.5:sample_rate=48000",
         "-af", "highpass=f=500,lowpass=f=5000,afade=t=in:d=0.25,afade=t=out:st=0.25:d=0.35,volume=0.5,"
         "aformat=channel_layouts=stereo", str(path)])
    return path


def final_pass(ctx, main, total, global_ovs, out_mp4, audio_cfg, watermark, sfx_times):
    args = [ffmpeg_bin(), "-y", "-v", "error", "-nostdin", "-i", str(main)]
    fc = []
    cur = "0:v"
    n_in = 1
    for j, ov in enumerate(global_ovs):
        st, en = ov["start"], ov["end"]
        if ov.get("static"):
            # Loop the still for the whole video. A single-frame input is lost when FFmpeg re-initialises the
            # filter graph mid-stream (e.g. a hard-cut join of an untagged intro card and bt709 camera footage),
            # which made burned-in captions disappear in 1.0.0. Same input form as the animated overlays below.
            args += ["-loop", "1", "-t", "%.3f" % total, "-i", str(ov["png"])]
            fc.append("[%s][%d:v]overlay=0:0:enable='between(t,%.3f,%.3f)'[g%d]" % (cur, n_in, st, en, j))
        else:
            args += ["-loop", "1", "-t", "%.3f" % total, "-i", str(ov["png"])]
            fc.append("[%d:v]format=rgba,fade=t=in:st=%.3f:d=0.4:alpha=1,fade=t=out:st=%.3f:d=0.35:alpha=1[gi%d]"
                      % (n_in, st, max(st, en - 0.35), j))
            x = _ease_x(st, 0.5, (90 if ctx.rtl else -90))
            fc.append("[%s][gi%d]overlay=x='%s':y=0:enable='between(t,%.3f,%.3f)'[g%d]" % (cur, j, x, st, en, j))
        cur = "g%d" % j
        n_in += 1
    if watermark:
        args += ["-loop", "1", "-t", "%.3f" % total, "-i", str(watermark["png"])]
        fc.append("[%d:v]format=rgba,colorchannelmixer=aa=%.2f[wm]" % (n_in, watermark["opacity"]))
        fc.append("[%s][wm]overlay=0:0:enable='between(t,%.3f,%.3f)'[gwm]" % (cur, watermark["start"], watermark["end"]))
        cur = "gwm"
        n_in += 1
    fc.append("[%s]scale=out_range=tv:out_color_matrix=bt709,format=yuv420p[vout]" % cur)

    # ---- audio ----
    a_main = "[0:a]aformat=sample_rates=48000:channel_layouts=stereo"
    ov_vol = audio_cfg.get("original_volume")
    if ov_vol is not None:
        a_main += ",volume=%.3f" % float(ov_vol)
    mixes = []
    vo = audio_cfg.get("voiceover")
    music = audio_cfg.get("music")
    duck = audio_cfg.get("duck", True)
    need_split = 2 if (music and duck) else 1
    if need_split == 2:
        fc.append(a_main + ",asplit=2[am][asc]")
        mixes.append("[am]")
    else:
        fc.append(a_main + "[am]")
        mixes.append("[am]")
    if vo:
        args += ["-i", str(vo["src"])]
        fc.append("[%d:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=%.3f,adelay=%d|%d[vo]"
                  % (n_in, float(vo.get("volume", 1.0)), int(vo["start"] * 1000), int(vo["start"] * 1000)))
        n_in += 1
        if need_split == 2:
            fc.append("[vo]asplit=2[vom][vosc]")
            fc.append("[asc][vosc]amix=inputs=2:duration=first:normalize=0[asc2]")
            mixes.append("[vom]")
        else:
            mixes.append("[vo]")
    if music:
        args += ["-stream_loop", "-1", "-i", str(music["src"])]
        mv = float(music.get("volume", 0.18))
        fades = (",afade=t=in:d=1.0,afade=t=out:st=%.3f:d=2.0" % max(0, total - 2.0)) if music.get("fade", True) else ""
        fc.append("[%d:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:%.3f,volume=%.3f%s[mus]"
                  % (n_in, total, mv, fades))
        n_in += 1
        if duck:
            sc_in = "[asc2]" if vo else "[asc]"
            fc.append("[mus]%ssidechaincompress=threshold=0.02:ratio=10:attack=15:release=450[musd]" % sc_in)
            mixes.append("[musd]")
        else:
            mixes.append("[mus]")
    if sfx_times:
        args += ["-i", str(ctx.whoosh)]
        parts = []
        fc.append("[%d:a]asplit=%d%s" % (n_in, len(sfx_times), "".join("[sx%d]" % i for i in range(len(sfx_times)))))
        for i, t in enumerate(sfx_times):
            d = max(0, int((t - 0.3) * 1000))
            fc.append("[sx%d]adelay=%d|%d,volume=0.35[sxd%d]" % (i, d, d, i))
            parts.append("[sxd%d]" % i)
        fc.append("%samix=inputs=%d:duration=longest:normalize=0[sfx]" % ("".join(parts), len(parts)))
        mixes.append("[sfx]")
        n_in += 1
    if len(mixes) > 1:
        fc.append("%samix=inputs=%d:duration=first:normalize=0[amix]" % ("".join(mixes), len(mixes)))
        last = "[amix]"
    else:
        last = mixes[0]
    if audio_cfg.get("normalize", True):
        fc.append("%sloudnorm=I=%s:TP=-1.5:LRA=11,aresample=48000[aout]" % (last, audio_cfg.get("target_lufs", -14)))
    else:
        fc.append("%sanull[aout]" % last)
    crf, preset = ENC_FINAL[ctx.quality]
    venc = ["-c:v", "libx264", "-crf", crf, "-preset", preset, "-profile:v", "high", "-pix_fmt", "yuv420p"] \
        if ctx.vcodec == "libx264" else ["-c:v", ctx.vcodec, "-b:v", "12M", "-pix_fmt", "yuv420p"]
    args += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]", *venc,
             "-r", str(ctx.fps), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", "%.3f" % total,
             "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
             "-movflags", "+faststart", "-metadata", "comment=Made with URM Creator Studio", str(out_mp4)]
    ctx.log.append(" ".join(_q(a) for a in args))
    run(args, timeout=60 * 60)


def production_summary(plan, scenes, durs, look, identity, score_used, project_dir):
    """What the video is made of and where every element came from (provenance for the manifest + QC gates)."""
    from .project import asset_registry
    reg = asset_registry(project_dir)
    content = [(sc, d) for sc, d in zip(scenes, durs) if sc.get("_role") == "scene"]
    total = sum(d for _, d in content) or 1.0
    by_kind = {}
    for sc, d in content:
        by_kind[sc["kind"]] = round(by_kind.get(sc["kind"], 0) + d, 2)
    user_media = [sc for sc, _ in content if sc["kind"] in ("video", "image")]
    # "static" = stills and plain title cards without motion design around them
    static = sum(d for sc, d in content if sc["kind"] == "title" or (sc["kind"] == "image" and not sc.get("texts")))
    mode = (plan.get("production") or {}).get("mode")
    if mode not in ("asset", "creative", "mixed"):
        mode = "creative" if not user_media else ("mixed" if by_kind.get("motion") else "asset")
    assets = []
    seen = set()
    for sc, _ in content:
        srcs = []
        if sc["kind"] in ("video", "image"):
            srcs.append(sc.get("src"))
        if sc["kind"] == "motion" and (sc.get("params") or {}).get("image"):
            srcs.append(sc["params"]["image"])
        for src in srcs:
            if not src or src in seen:
                continue
            seen.add(src)
            r = reg.get(str(src).replace("\\", "/"), {})
            assets.append({"file": src, "origin": r.get("origin", "user"), "provider": r.get("provider"),
                           "license": r.get("license"), "prompt": r.get("prompt"), "credit": r.get("credit")})
    au = plan.get("audio") or {}
    if au.get("music"):
        m = au["music"] if isinstance(au["music"], dict) else {"src": au["music"]}
        r = reg.get(str(m.get("src")).replace("\\", "/"), {})
        assets.append({"file": m.get("src"), "kind": "music", "origin": r.get("origin", "user"),
                       "provider": r.get("provider"), "license": r.get("license"), "credit": r.get("credit")})
    if score_used:
        assets.append({"file": "soundtrack (synthesised)", "kind": "music", "origin": "engine",
                       "provider": "URM Creator Studio", "license": "original, generated for this video"})
    if by_kind.get("motion"):
        assets.append({"file": "motion graphics", "kind": "graphics", "origin": "engine",
                       "provider": "URM Creator Studio", "license": "original, generated for this video"})
    templates = [sc.get("template") for sc, _ in content if sc["kind"] == "motion"]
    return {"mode": mode, "content_seconds": round(total, 2), "seconds_by_kind": by_kind,
            "static_share": round(static / total, 3), "templates": templates,
            "distinct_templates": len(set(templates)), "look": (look or {}).get("name"),
            "palette": {k: ((look or {}).get("palette") or {}).get(k) for k in ("primary", "secondary", "accent", "bg")} if look else None,
            "identity": {k: v for k, v in (identity or {}).items() if k in ("name", "initials", "temporary")} or None,
            "score": score_used, "assets": assets,
            "has_cta": any(t == "cta" for t in templates) or any(sc.get("_role") == "outro" for sc in scenes)}


def cover_time(scenes, starts, motion_cards, intro_end, total):
    """A strong frame for the cover: the first motion headline fully visible, else 1 s into the content."""
    firsts = sorted(c["start"] for c in motion_cards if c["start"] < total * 0.5)
    if firsts:
        return round(min(total - 0.1, firsts[0] + 0.5), 2)
    return round(min(total - 0.1, max(intro_end + 1.0, 0.5)), 2)


def loudness_touchup(mp4, target, ctx):
    """Single-pass loudnorm lands within ~2 LU; measure and correct precisely
    (audio only, the video stream is copied untouched)."""
    from .media import loudness
    ld = loudness(mp4)
    lufs = ld.get("lufs")
    if lufs is None or lufs < -60:
        return
    gain = target - lufs
    if abs(gain) < 0.5:
        return
    tmp = mp4.with_name(mp4.stem + ".tmp.mp4")
    args = [ffmpeg_bin(), "-y", "-v", "error", "-i", str(mp4), "-map", "0:v", "-map", "0:a", "-c:v", "copy",
            "-af", "volume=%.2fdB,alimiter=limit=0.84:level=false" % gain, "-c:a", "aac", "-b:a", "192k",
            "-ar", "48000", "-movflags", "+faststart", str(tmp)]
    ctx.log.append(" ".join(_q(a) for a in args))
    run(args)
    os.replace(tmp, mp4)


# --------------------------------------------------------------------------
# Main entry
# --------------------------------------------------------------------------

def render(project_dir, preview=False, fmt_override=None, lang=None, progress=print):
    t0 = time.time()
    project_dir = Path(project_dir).resolve()
    plan = load_plan(project_dir)
    validate_plan(plan, project_dir)
    proj = read_json(project_dir / "project.json") if (project_dir / "project.json").exists() else {}
    slug = plan.get("brand", proj.get("brand"))
    brand = brandmod.load_brand(slug) if slug else None
    bs = brandmod.brand_style(brand)
    vlang = plan.get("language") or (brand or {}).get("primary_language") or "ar"
    lang_text = "ar" if vlang in ("ar", "bilingual", "mixed") else "en"
    fmt = fmt_override or plan.get("format", "vertical")
    W, H = FORMATS[fmt][0], FORMATS[fmt][1]
    if preview:
        W, H = W // 2 // 2 * 2, H // 2 // 2 * 2
    fps = int(plan.get("fps", 30))

    ctx = Ctx()
    ctx.W, ctx.H, ctx.fps, ctx.fmt = W, H, fps, fmt
    ctx.rtl = lang_text == "ar"
    ctx.quality = "preview" if preview else plan.get("quality", "standard")
    ctx.log = []
    enc = run([ffmpeg_bin(), "-hide_banner", "-encoders"], check=False).stdout.decode("utf-8", "replace")
    ctx.vcodec = "libx264" if " libx264 " in enc else ("h264_videotoolbox" if "h264_videotoolbox" in enc else "mpeg4")
    ctx.inter_opts = (["-crf", "15", "-preset", "veryfast", "-pix_fmt", "yuv420p"] if ctx.vcodec == "libx264"
                      else ["-b:v", "20M", "-pix_fmt", "yuv420p"])

    vdir = next_version_dir(project_dir, preview)
    work = project_dir / "work" / vdir.name
    work.mkdir(parents=True, exist_ok=True)
    cards = CardRenderer(project_dir / "work" / "cards")
    protect = brandmod.protected_terms(brand)
    numerals = bs.get("numerals", "western")

    cap_cfg = plan.get("captions") or {}
    reserve = 0
    if cap_cfg.get("src") and cap_cfg.get("burn", True) and cap_cfg.get("position", "bottom") in ("bottom", "lower"):
        reserve = round(H * (0.105 if fmt == "vertical" else 0.15))  # two caption lines + gap

    # ---------- scenes ----------
    scenes = expand_scenes(plan, brand, lang_text)
    sources = []
    progress("• scenes: %d" % len(scenes))
    for i, sc in enumerate(scenes):
        sc["_role"] = sc.get("_role", "scene")
        if sc["kind"] in ("video", "image"):
            sc["_src"] = resolve_src(project_dir, sc["src"])
            sources.append(sc["_src"])
            sc["_info"] = probe(sc["_src"])
        sc["_dur"] = scene_duration(sc, sc.get("_info"))
        if sc["kind"] == "title":
            bgkind = sc.get("background", "gradient")
            bghtml = background_html(W, H, bs, "solid" if bgkind == "solid" else "gradient")
            if isinstance(bgkind, str) and bgkind.startswith("#"):
                bghtml = background_html(W, H, dict(bs, primary=bgkind, secondary=bgkind), "solid")
            sc["_bg"] = cards.add(bghtml, W, H)
        ovs = []
        if sc["_role"] == "intro":
            ovs.append({"start": 0.15, "end": sc["_dur"] - 0.05, "animation": "zoom",
                        "pngs": [cards.add(intro_card(W, H, fmt, brand, bs, lang_text), W, H)], "text": "intro"})
        elif sc["_role"] == "outro":
            ovs.append({"start": 0.2, "end": sc["_dur"], "animation": "slide_up",
                        "pngs": [cards.add(outro_card(W, H, fmt, brand, bs, lang_text, sc.get("cta")), W, H)],
                        "text": "outro"})
        for t in sc.get("texts", []):
            txt = str(t["text"])
            st = float(t.get("start", 0.3 if sc["kind"] != "title" else 0.2))
            en = float(t.get("end", sc["_dur"] - 0.15))
            en = min(en, sc["_dur"])
            anim = t.get("animation", "fade")
            role = t.get("role", "headline")
            pos = t.get("position", "center" if sc["kind"] == "title" else ("lower" if role in ("subtitle", "body") else "center"))
            style = dict(t.get("style") or {})
            style.setdefault("reserve_bottom", reserve)
            if anim in ("words", "typewriter"):
                n = count_words(txt)
                pngs = [cards.add(build_card_html(width=W, height=H, fmt=fmt, text=txt, role=role, position=pos,
                                                  style=style, brand_style=bs, hide_after_word=k,
                                                  protect=protect, numerals=numerals), W, H) for k in range(n)]
            else:
                pngs = [cards.add(build_card_html(width=W, height=H, fmt=fmt, text=txt, role=role, position=pos,
                                                  style=style, brand_style=bs, protect=protect,
                                                  numerals=numerals), W, H)]
            full_from = st
            if anim in ("words", "typewriter") and len(pngs) > 1:
                hold = 1.5 + 0.3 * len(pngs)
                step = min(0.45, (en - st - hold) / len(pngs))
                if step >= 0.08:
                    full_from = st + (len(pngs) - 1) * step
            ovs.append({"start": st, "end": en, "animation": anim, "pngs": pngs, "text": txt, "position": pos,
                        "full_from": full_from})
        sc["_overlays"] = ovs

    durs = [sc["_dur"] for sc in scenes]
    ctx.roles = [sc["_role"] for sc in scenes]

    # timeline positions need transition overlap (per boundary: motion scenes cut under their own transitions)
    tr = plan.get("transition") or {"type": "fade", "duration": 0.35}
    bounds = boundary_plan(ctx, scenes, durs, tr)
    starts = []
    acc = 0.0
    for i, d in enumerate(durs):
        starts.append(acc)
        acc += d - (bounds[i + 1][1] if i < len(durs) - 1 else 0)
    total = acc
    td = max([bd[1] for bd in bounds[1:]] or [0.0])
    intro_end = durs[0] - (bounds[1][1] if len(bounds) > 1 else 0) / 2 if ctx.roles[0] == "intro" else 0.0
    outro_start = starts[-1] + bounds[-1][1] / 2 if ctx.roles[-1] == "outro" and len(bounds) > 1 else total
    content_offset = starts[1] if ctx.roles[0] == "intro" and len(starts) > 1 else 0.0

    # ---------- global overlays ----------
    global_ovs = []
    for lt in plan.get("overlays", []):
        kind = lt.get("kind", "lower_third")
        st = float(lt.get("start", 1.0)) + content_offset
        en = float(lt.get("end", lt.get("start", 1.0) + 4.0)) + content_offset
        if kind == "lower_third":
            # rise above any low-positioned scene text that is on screen at the same time
            lift = 0
            for i_sc, sc in enumerate(scenes):
                for ov in sc["_overlays"]:
                    if ov.get("position") in ("lower", "bottom"):
                        a, b = starts[i_sc] + ov["start"], starts[i_sc] + ov["end"]
                        if min(b, en) - max(a, st) > 0.2:
                            lift = round(H * (0.13 if fmt == "vertical" else 0.17))
            png = cards.add(lower_third_html(W, H, fmt, lt.get("title", ""), lt.get("subtitle", ""), bs, protect,
                                             reserve + lift), W, H)
        else:
            png = cards.add(build_card_html(width=W, height=H, fmt=fmt, text=lt.get("text", ""),
                                            role=lt.get("role", "headline"), position=lt.get("position", "upper"),
                                            style=dict(lt.get("style") or {}, reserve_bottom=reserve),
                                            brand_style=bs, protect=protect,
                                            numerals=numerals), W, H)
        global_ovs.append({"start": st, "end": min(en, outro_start), "png": png, "text": lt.get("title") or lt.get("text", ""),
                           "kind": kind})
    cues_final = []
    cap = plan.get("captions") or {}
    if cap.get("src"):
        cues = parse_captions(resolve_src(project_dir, cap["src"]))
        cues_final = [dict(c, start=c["start"] + content_offset, end=c["end"] + content_offset) for c in cues]
        if cap.get("burn", True):
            cpos = cap.get("position", "bottom")
            cstyle = {"caption_style": cap.get("style", bs.get("caption_style", "box"))}
            for c in cues_final:
                png = cards.add(build_card_html(width=W, height=H, fmt=fmt, text=c["text"].replace(" [؟]", "").replace(" [?]", ""),
                                                role="caption", position=cpos, style=cstyle, brand_style=bs,
                                                protect=protect, numerals=numerals), W, H)
                global_ovs.append({"start": c["start"], "end": c["end"], "png": png, "text": c["text"],
                                   "kind": "caption", "static": True})
    watermark = None
    wm_cfg = (plan.get("branding") or {}).get("watermark")
    if wm_cfg is None and brand:
        wm_cfg = (brand.get("watermark") or {}).get("enabled", False)
    logo = brandmod.logo_file(brand)
    if wm_cfg and logo:
        top, right, bottom, left = SAFE_MARGINS[fmt]
        side = "left" if ctx.rtl else "right"
        wm_html = ("<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;width:%dpx;height:%dpx;"
                   "background:transparent;overflow:hidden}img{position:absolute;top:%dpx;%s:%dpx;max-width:%dpx;"
                   "max-height:%dpx;object-fit:contain;filter:drop-shadow(0 2px 6px rgba(0,0,0,.45))}</style></head>"
                   "<body><img src='%s'></body></html>" % (W, H, round(top * H * 0.55), side, round(0.05 * W),
                                                           round(W * 0.16), round(H * 0.06), logo.as_uri()))
        watermark = {"png": cards.add(wm_html, W, H), "opacity": float((brand.get("watermark") or {}).get("opacity", 0.85)),
                     "start": intro_end, "end": outro_start}

    # ---------- motion-design scenes (creative-led production) ----------
    motion_idx = [i for i, sc in enumerate(scenes) if sc["kind"] == "motion"]
    motion_cards, motion_events = [], []
    look = identity = None
    if motion_idx:
        look = looksmod.resolve_look(plan, brand)
        if brand:
            look["custom_fonts"] = bs.get("custom_fonts") or []
        identity = looksmod.resolve_identity(plan, brand, lang_text, brandmod.logo_file(brand))
        if (plan.get("production") or {}).get("mode") in ("creative", "mixed", None):
            ctx.tint = (look.get("palette") or {}).get("bg")
        trans = look.get("transitions") or ["swap"]
        mscenes = []
        for n, i in enumerate(motion_idx):
            sc = scenes[i]
            prev_m = i > 0 and scenes[i - 1]["kind"] == "motion"
            next_m = i + 1 < len(scenes) and scenes[i + 1]["kind"] == "motion"
            # matched pairs: the outgoing scene's cover is the incoming scene's reveal
            if next_m and "tout" not in sc:
                sc["tout"] = scenes[i + 1].get("tin") or trans[n % len(trans)]
            if prev_m and "tin" not in sc:
                sc["tin"] = scenes[i - 1].get("tout", "swap")
            sc.setdefault("tin", "swap")
            sc.setdefault("tout", "swap")
            if not next_m and sc["tout"] in ("panels", "circle"):
                sc["tout"] = "swap"   # a cover only works when the next scene uncovers it
            if not prev_m and sc["tin"] in ("panels", "circle"):
                sc["tin"] = "swap"
            mscenes.append(dict(sc, duration=sc["_dur"], _t0=starts[i]))
        studio = MotionStudio(W=W, H=H, fps=fps, fmt=fmt, safe=SAFE_MARGINS[fmt], rtl=ctx.rtl, numerals=numerals,
                              look=look, identity=identity, scenes=mscenes, project_dir=project_dir,
                              log=ctx.log)
        progress("• motion design: %d scenes (look: %s)" % (len(motion_idx), look.get("name")))
        layout = studio.layout()
        for n, i in enumerate(motion_idx):
            lay = layout[n] if n < len(layout) else {}
            for tx in lay.get("texts", []):
                motion_cards.append({"scene": "motion", "kind": "motion_text", "text": tx["text"], "bbox": tx["bbox"],
                                     "t": starts[i] + min(max(tx["full_from"] + 0.4, (tx["full_from"] + tx["end"]) / 2),
                                                          tx["end"] - 0.1),
                                     "start": starts[i] + tx["full_from"], "end": starts[i] + tx["end"],
                                     "full_visible": round(tx["end"] - tx["full_from"], 2), "template": scenes[i]["template"]})
            for e in lay.get("events", []):
                motion_events.append(dict(e, t=round(starts[i] + e["t"], 3)))
        # clips are cached by content: a re-render after a soundtrack, caption or text-card change reuses them
        cache = project_dir / "work" / "motion-cache"
        cache.mkdir(parents=True, exist_ok=True)
        outs, todo = {}, {}
        for n, i in enumerate(motion_idx):
            key = studio.scene_key(n, ctx.vcodec, ctx.inter_opts)
            outs[n] = cache / ("motion_%s.mp4" % key)
            if not outs[n].exists():
                todo[n] = work / ("motion_%02d.part.mp4" % i)
        if todo:
            studio.render_scenes(todo, ctx.vcodec, ctx.inter_opts, progress=progress)
            for n, tmp_out in todo.items():
                os.replace(tmp_out, outs[n])
        else:
            progress("  ✓ motion scenes unchanged (reused)")
        for n, i in enumerate(motion_idx):
            scenes[i]["_src"] = outs[n]
            scenes[i]["_info"] = probe(outs[n])

    progress("• text cards: rendering with %s" % Path(cards.browser).name)
    cards.run()

    # ---------- segments ----------
    segs = []
    for i, sc in enumerate(scenes):
        progress("• scene %d/%d (%s, %.1fs)" % (i + 1, len(scenes), sc["_role"] if sc["_role"] != "scene" else sc["kind"], sc["_dur"]))
        segs.append(build_segment(ctx, i, sc, work / ("seg_%02d.mp4" % i)))

    progress("• joining scenes")
    main = work / "main.mp4"
    join_segments(ctx, segs, durs, main, bounds)

    audio_cfg = dict(plan.get("audio") or {})
    music = audio_cfg.get("music")
    if music:
        m = music if isinstance(music, dict) else {"src": music}
        audio_cfg["music"] = dict(m, src=resolve_src(project_dir, m["src"]))
        sources.append(audio_cfg["music"]["src"])
    vo = audio_cfg.get("voiceover")
    if vo:
        v = vo if isinstance(vo, dict) else {"src": vo}
        audio_cfg["voiceover"] = {"src": resolve_src(project_dir, v["src"]), "start": float(v.get("start", 0)) + content_offset,
                                  "volume": v.get("volume", 1.0)}
        audio_cfg["voiceover"]["length"] = probe(audio_cfg["voiceover"]["src"]).get("duration") or 0.0
        sources.append(audio_cfg["voiceover"]["src"])
    # ---------- original soundtrack (creative-led: no music file needed) ----------
    score_cfg = audio_cfg.get("score")
    # creative/mixed productions never go out silent by accident: with no music file and no score requested,
    # compose one in the look's mood ("score": false opts out explicitly)
    pmode = (plan.get("production") or {}).get("mode")
    if score_cfg is None and not audio_cfg.get("music") and (
            pmode in ("creative", "mixed") or (pmode is None and motion_idx)):
        score_cfg = {"auto": True}
    score_used = None
    if score_cfg and not audio_cfg.get("music"):
        score_cfg = dict(score_cfg) if isinstance(score_cfg, dict) else {}
        ev_all = list(motion_events) if score_cfg.get("sfx", True) else []
        if score_cfg.get("sfx", True):
            for i in range(1, len(scenes)):
                if not (scenes[i]["kind"] == "motion" and scenes[i - 1]["kind"] == "motion"):
                    ev_all.append({"t": round(starts[i], 3), "type": "whoosh", "strength": 0.6})
        cta = [starts[i] for i, sc in enumerate(scenes) if sc.get("template") in ("cta",) or sc["_role"] == "outro"]
        sspec = {"duration": round(total, 3), "mood": score_cfg.get("mood") or (look or {}).get("mood") or "inspiring",
                 "bpm": score_cfg.get("bpm"), "seed": int(score_cfg.get("seed", 5)), "events": ev_all,
                 "climax": cta[-1] if cta else None, "sfx": score_cfg.get("sfx", True)}
        progress("• original soundtrack (%s)" % sspec["mood"])
        wav = render_score(sspec, work / "soundtrack.wav", log=ctx.log)
        has_vo = bool(audio_cfg.get("voiceover"))
        audio_cfg["music"] = {"src": wav, "volume": float(score_cfg.get("volume", 0.32 if has_vo else 1.0)), "fade": False}
        audio_cfg.setdefault("duck", has_vo)
        score_used = {"mood": sspec["mood"], "events": len(ev_all), "auto": bool(score_cfg.get("auto")), "generated_by": "URM Creator Studio engine (synthesised, original)"}
    sfx_times = []
    if audio_cfg.get("sfx") and td > 0 and not score_used:
        ctx.whoosh = whoosh_wav(project_dir / "work" / "whoosh.wav")
        sfx_times = [starts[i] for i in range(1, len(starts)) if bounds[i][0] != "cut"]

    has_sound = any(sc["kind"] == "video" and sc["_info"].get("has_audio") and float(sc.get("volume", 1.0)) > 0
                    for sc in scenes) or bool(audio_cfg.get("music") or audio_cfg.get("voiceover") or sfx_times)
    if not has_sound:
        audio_cfg["normalize"] = False  # loudness normalisation of pure silence yields NaN samples

    quiet_source = None
    if has_sound and audio_cfg.get("normalize", True) and not (audio_cfg.get("music") or audio_cfg.get("voiceover")):
        from .media import loudness as _ld
        ml = _ld(main).get("lufs")
        if ml is not None and ml < -30:
            audio_cfg["normalize"] = False  # boosting room tone/hum by 20+ dB makes noise loud
            quiet_source = ml

    fingerprints_before = fingerprint(sources)
    name = (plan.get("output_name") or proj.get("slug") or project_dir.name)
    out_mp4 = vdir / ("%s_%s%s.mp4" % (name, fmt, "_preview" if preview else ""))
    for s in sources:
        if Path(s).resolve() == out_mp4.resolve():
            raise StudioError("unsafe_output", str(s))
    progress("• final mix and export")
    final_pass(ctx, main, total, global_ovs, out_mp4, audio_cfg, watermark, sfx_times)
    if audio_cfg.get("normalize", True):
        loudness_touchup(out_mp4, float(audio_cfg.get("target_lufs", -14)), ctx)

    if cues_final:
        write_srt(cues_final, vdir / "captions.srt")
        write_vtt(cues_final, vdir / "captions.vtt")
    shutil.copy2(project_dir / "plan.json", vdir / "plan.used.json")
    (vdir / "render.log").write_text("\n\n".join(ctx.log), encoding="utf-8")

    used_cards = []
    for sc in scenes:
        for ov in sc["_overlays"]:
            s0 = starts[scenes.index(sc)]
            ff = ov.get("full_from", ov["start"])
            used_cards.append({"scene": sc["_role"] if sc["_role"] != "scene" else sc["kind"],
                               "png": str(ov["pngs"][-1]), "text": ov["text"],
                               # sample when the whole text is visible (after a word-by-word reveal)
                               "t": s0 + max((ff + ov["end"]) / 2, min(ff + 0.5, ov["end"] - 0.4)),
                               "full_visible": round(ov["end"] - 0.35 - ff, 2), "start": s0 + ov["start"],
                               "end": s0 + ov["end"], "kind": "scene_text"})
    for ov in global_ovs:
        used_cards.append({"scene": ov["kind"], "png": str(ov["png"]), "text": ov["text"],
                           "t": (ov["start"] + ov["end"]) / 2, "start": ov["start"], "end": ov["end"],
                           "kind": ov["kind"]})
    used_cards += motion_cards
    onscreen = sorted([c for c in used_cards if c["kind"] in ("scene_text", "motion_text") and c["text"] not in ("intro", "outro")],
                      key=lambda c: c["start"])
    if onscreen and not cues_final:
        # no speech: the on-screen words as a subtitle file (accessibility, platform captions, translation)
        write_srt([{"start": max(0.0, c["start"]), "end": max(c["start"] + 0.5, c["end"]), "text": c["text"]} for c in onscreen],
                  vdir / "onscreen_text.srt")
    if watermark:
        used_cards.append({"scene": "watermark", "png": str(watermark["png"]), "text": "logo",
                           "t": (watermark["start"] + watermark["end"]) / 2, "kind": "watermark"})
    meta = {
        "studio_version": VERSION, "rendered_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "project": project_dir.name, "brand": slug, "format": fmt, "width": W, "height": H, "fps": fps,
        "preview": preview, "duration": round(total, 3), "content_offset": round(content_offset, 3),
        "intro_end": round(intro_end, 3), "outro_start": round(outro_start, 3), "language": vlang,
        "scene_starts": [round(s, 3) for s in starts], "scene_roles": ctx.roles, "output": str(out_mp4),
        "cards": used_cards, "sources": [str(s) for s in sources], "source_fingerprints": fingerprints_before,
        "seconds_taken": round(time.time() - t0, 1), "encoder": ctx.vcodec,
        "hdr_sources": [str(sc["_src"]) for sc in scenes if sc.get("_info", {}).get("hdr")],
        "caption_problems": check_captions([c for c in cues_final]) if cues_final else [],
        "quiet_source_lufs": quiet_source,
        "voiceover": ({"start": round(audio_cfg["voiceover"]["start"], 3),
                       "length": round(float(audio_cfg["voiceover"]["length"]), 3)} if audio_cfg.get("voiceover") else None),
        "production": production_summary(plan, scenes, durs, look, identity, score_used, project_dir),
        "cover_t": cover_time(scenes, starts, motion_cards, intro_end, total),
    }
    write_json(vdir / "render.json", meta)
    if not preview:
        friendly = project_dir / (("الفيديو-النهائي_%s.mp4" if vlang in ("ar", "bilingual", "mixed") else "final-video_%s.mp4") % fmt)
        shutil.copy2(out_mp4, friendly)  # always the newest final, easy to find
        meta["friendly_copy"] = str(friendly)
        write_json(vdir / "render.json", meta)
    if not plan.get("keep_work", False):
        for s in segs:
            try:
                s.unlink()
            except OSError:
                pass
    return vdir, meta
