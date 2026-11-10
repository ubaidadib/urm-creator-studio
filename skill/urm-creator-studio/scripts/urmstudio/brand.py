"""Brand profiles: one folder per brand under <workspace>/brands/<slug>/.

brand.json is plain JSON so users (or Claude on their behalf) can change it
without touching code. Logos and custom fonts are COPIED into the brand
folder; originals are never moved or modified.
"""
import copy
import re
import shutil
from pathlib import Path

from .common import (StudioError, ensure_home, read_json, slugify, studio_home,
                     write_json, has_arabic)
from .textrender import BUNDLED_FONTS

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

STYLE_PRESETS = {
    # visual_style -> defaults used when the user says "I don't know"
    "modern": {"primary": "#1E3A8A", "secondary": "#0EA5E9", "accent": "#FACC15",
               "font_ar_heading": "Cairo", "font_ar_body": "Tajawal"},
    "luxury": {"primary": "#111111", "secondary": "#3A2E1F", "accent": "#C9A227",
               "font_ar_heading": "Amiri", "font_ar_body": "Noto Naskh Arabic"},
    "playful": {"primary": "#7C3AED", "secondary": "#EC4899", "accent": "#FDE047",
                "font_ar_heading": "Cairo", "font_ar_body": "Cairo"},
    "corporate": {"primary": "#0F2A44", "secondary": "#2F6690", "accent": "#3FB950",
                  "font_ar_heading": "Noto Kufi Arabic", "font_ar_body": "Tajawal"},
    "minimal": {"primary": "#18181B", "secondary": "#3F3F46", "accent": "#FFFFFF",
                "font_ar_heading": "Tajawal", "font_ar_body": "Tajawal"},
    "bold": {"primary": "#B91C1C", "secondary": "#111827", "accent": "#FBBF24",
             "font_ar_heading": "Cairo", "font_ar_body": "Cairo"},
}

DEFAULT_BRAND = {
    "schema": 1,
    "slug": "",
    "name": {"ar": "", "en": ""},
    "primary_language": "ar",          # ar | en | bilingual
    "logo": {"file": None, "has_logo": False},
    "colors": {"primary": "#1E3A8A", "secondary": "#0EA5E9", "accent": "#FACC15",
               "text": "#FFFFFF", "on_accent": "#111111"},
    "fonts": {"arabic_heading": "Cairo", "arabic_body": "Tajawal",
              "latin_heading": "Inter", "latin_body": "Inter", "custom": []},
    "personality": [],
    "visual_style": "modern",
    "handles": {"instagram": "", "tiktok": "", "youtube": "", "snapchat": "", "x": "",
                "facebook": "", "linkedin": "", "website": "", "whatsapp": ""},
    "tagline": {"ar": "", "en": ""},
    "intro": {"enabled": True, "duration": 2.0},
    "outro": {"enabled": True, "duration": 3.0, "show_handles": True,
              "cta": {"ar": "", "en": ""}},
    "watermark": {"enabled": False, "position": "top_corner", "opacity": 0.85},
    "captions": {"style": "box"},     # box | outline | brand
    "numerals": "western",            # western (123) | arabic_indic (١٢٣)
}

# Used when the user has not configured a brand: neutral, unbranded, no logo.
NEUTRAL_STYLE = {
    "primary": "#1F2937", "secondary": "#374151", "accent": "#F59E0B", "text_color": "#FFFFFF",
    "on_accent": "#111111", "font_ar_heading": "Cairo", "font_ar_body": "Tajawal",
    "font_latin_heading": "Inter", "font_latin_body": "Inter", "caption_style": "box",
    "custom_fonts": [], "numerals": "western",
}


def brands_dir() -> Path:
    return studio_home() / "brands"


def brand_path(slug) -> Path:
    return brands_dir() / slug / "brand.json"


def list_brands():
    d = brands_dir()
    if not d.exists():
        return []
    return sorted(p.parent.name for p in d.glob("*/brand.json"))


def load_brand(slug):
    if not slug:
        return None
    p = brand_path(slug)
    if not p.exists():
        raise StudioError("not_found", "brand '%s'" % slug)
    b = read_json(p)
    merged = _deep_merge(copy.deepcopy(DEFAULT_BRAND), b)
    merged["_dir"] = str(p.parent)
    return merged


def _deep_merge(base, over):
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def create_brand(name_ar="", name_en="", style="modern", slug=None, data=None):
    ensure_home()
    if not (name_ar or name_en or (data and data.get("name"))):
        raise StudioError("bad_brand", "a brand needs a name (Arabic or English)")
    b = copy.deepcopy(DEFAULT_BRAND)
    if style in STYLE_PRESETS:
        sp = STYLE_PRESETS[style]
        b["visual_style"] = style
        b["colors"].update({k: sp[k] for k in ("primary", "secondary", "accent")})
        b["fonts"]["arabic_heading"] = sp["font_ar_heading"]
        b["fonts"]["arabic_body"] = sp["font_ar_body"]
    if data:
        _deep_merge(b, data)
    if name_ar:
        b["name"]["ar"] = name_ar
    if name_en:
        b["name"]["en"] = name_en
    base = slug or slugify(b["name"].get("en") or b["name"].get("ar"), "brand")
    s, i = base, 2
    while brand_path(s).exists():
        s = "%s-%d" % (base, i)
        i += 1
    b["slug"] = s
    if b["name"]["ar"] and not b["name"]["en"]:
        b["primary_language"] = "ar"
    elif b["name"]["en"] and not b["name"]["ar"]:
        b["primary_language"] = "en"
    elif b["name"]["ar"] and b["name"]["en"] and not data:
        b["primary_language"] = "bilingual"
    problems = validate(b)
    hard = [p for p in problems if p[0] == "error"]
    if hard:
        raise StudioError("bad_brand", "; ".join(p[1] for p in hard))
    write_json(brand_path(s), b)
    (brand_path(s).parent / "assets").mkdir(exist_ok=True)
    return s


def set_value(slug, dotted_key, value):
    """Update one field, e.g. colors.primary=#112233 or handles.instagram=@me."""
    p = brand_path(slug)
    if not p.exists():
        raise StudioError("not_found", "brand '%s'" % slug)
    b = read_json(p)
    cur = b
    keys = dotted_key.split(".")
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
    v = value
    if isinstance(v, str):
        if v.lower() in ("true", "false"):
            v = v.lower() == "true"
        elif re.fullmatch(r"-?\d+(\.\d+)?", v):
            v = float(v) if "." in v else int(v)
    cur[keys[-1]] = v
    merged = _deep_merge(copy.deepcopy(DEFAULT_BRAND), b)
    hard = [x for x in validate(merged) if x[0] == "error"]
    if hard:
        raise StudioError("bad_brand", "; ".join(x[1] for x in hard))
    write_json(p, b)
    return b


IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
FONT_EXT = {".ttf", ".otf", ".woff", ".woff2"}


def import_logo(slug, src, variant="main"):
    src = Path(src).expanduser()
    if not src.exists():
        raise StudioError("not_found", str(src))
    if src.suffix.lower() not in IMAGE_EXT:
        raise StudioError("bad_brand", "logo must be PNG, JPG, WEBP or SVG")
    bdir = brand_path(slug).parent
    dst = bdir / "assets" / ("logo-%s%s" % (variant, src.suffix.lower()))
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)  # copy, never move
    b = read_json(brand_path(slug))
    b.setdefault("logo", {})
    key = "file" if variant == "main" else "file_%s" % variant
    b["logo"][key] = "assets/" + dst.name
    b["logo"]["has_logo"] = True
    write_json(brand_path(slug), b)
    return dst


def import_font(slug, src, family, weight="400", license_confirmed=False):
    src = Path(src).expanduser()
    if not src.exists():
        raise StudioError("not_found", str(src))
    if src.suffix.lower() not in FONT_EXT:
        raise StudioError("bad_brand", "font must be TTF, OTF, WOFF or WOFF2")
    if not license_confirmed:
        raise StudioError("bad_brand", "font licence not confirmed by the user")
    bdir = brand_path(slug).parent
    dst = bdir / "assets" / "fonts" / src.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    b = read_json(brand_path(slug))
    b.setdefault("fonts", {}).setdefault("custom", [])
    b["fonts"]["custom"] = [c for c in b["fonts"]["custom"] if c.get("file") != "assets/fonts/" + src.name]
    b["fonts"]["custom"].append({"family": family, "file": "assets/fonts/" + src.name,
                                 "weight": str(weight), "license_confirmed": True})
    write_json(brand_path(slug), b)
    return dst


def validate(b):
    """Return list of (level, message). level: error | warn."""
    probs = []
    if not (b.get("name", {}).get("ar") or b.get("name", {}).get("en")):
        probs.append(("error", "name is empty"))
    for k, v in (b.get("colors") or {}).items():
        if v and not HEX.match(str(v)):
            probs.append(("error", "colour %s must look like #1A2B3C (got %s)" % (k, v)))
    known = set(BUNDLED_FONTS) | {c.get("family") for c in b.get("fonts", {}).get("custom", [])}
    for k in ("arabic_heading", "arabic_body", "latin_heading", "latin_body"):
        f = b.get("fonts", {}).get(k)
        if f and f not in known:
            probs.append(("warn", "font '%s' is not bundled; a safe fallback will be used" % f))
    for k in ("arabic_heading", "arabic_body"):
        f = b.get("fonts", {}).get(k)
        if f in ("Inter",):
            probs.append(("error", "font %s has no Arabic letters; choose an Arabic font" % f))
    lg = b.get("logo") or {}
    if lg.get("has_logo") and lg.get("file") and b.get("_dir"):
        if not (Path(b["_dir"]) / lg["file"]).exists():
            probs.append(("error", "logo file missing: %s" % lg["file"]))
    for h, v in (b.get("handles") or {}).items():
        if v and has_arabic(v) and h not in ("website",):
            probs.append(("warn", "handle %s contains Arabic letters; platforms usually use Latin" % h))
    if b.get("numerals") not in ("western", "arabic_indic"):
        probs.append(("error", "numerals must be 'western' or 'arabic_indic'"))
    c = b.get("colors") or {}
    if c.get("primary") and c.get("text") and contrast(c["primary"], c["text"]) < 3.0:
        probs.append(("warn", "text colour on primary colour has low contrast (%.1f:1)"
                      % contrast(c["primary"], c["text"])))
    return probs


def _lum(hexc):
    hexc = hexc.lstrip("#")
    rgb = [int(hexc[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def brand_style(b):
    """Flatten a brand profile into what the card renderer needs."""
    if not b:
        return dict(NEUTRAL_STYLE)
    c = b.get("colors", {})
    f = b.get("fonts", {})
    bdir = Path(b.get("_dir", "."))
    custom = [{"family": x["family"], "file": str(bdir / x["file"]), "weight": x.get("weight", "400")}
              for x in f.get("custom", []) if x.get("file")]
    return {
        "primary": c.get("primary", "#1F2937"), "secondary": c.get("secondary", "#374151"),
        "accent": c.get("accent", "#F59E0B"), "text_color": c.get("text", "#FFFFFF"),
        "on_accent": c.get("on_accent", "#111111"),
        "font_ar_heading": f.get("arabic_heading", "Cairo"), "font_ar_body": f.get("arabic_body", "Tajawal"),
        "font_latin_heading": f.get("latin_heading", "Inter"), "font_latin_body": f.get("latin_body", "Inter"),
        "caption_style": (b.get("captions") or {}).get("style", "box"),
        "custom_fonts": custom, "numerals": b.get("numerals", "western"),
    }


def logo_file(b):
    if not b:
        return None
    lg = b.get("logo") or {}
    if lg.get("has_logo") and lg.get("file"):
        p = Path(b["_dir"]) / lg["file"]
        if p.exists():
            return p
    return None


def display_name(b, lang):
    if not b:
        return ""
    n = b.get("name", {})
    if lang == "ar":
        return n.get("ar") or n.get("en") or ""
    return n.get("en") or n.get("ar") or ""


def protected_terms(b):
    """Latin brand names / handles that must stay LTR inside Arabic text."""
    if not b:
        return ()
    terms = [b.get("name", {}).get("en", "")]
    terms += [v for v in (b.get("handles") or {}).values() if v]
    return tuple(t for t in terms if t and not has_arabic(t))


def apply_style(slug, style):
    """Re-apply a style preset's colours and fonts (used when the style is chosen after creation)."""
    if style not in STYLE_PRESETS:
        raise StudioError("bad_brand", "unknown style %s" % style)
    b = read_json(brand_path(slug))
    sp = STYLE_PRESETS[style]
    b["visual_style"] = style
    b.setdefault("colors", {}).update({k: sp[k] for k in ("primary", "secondary", "accent")})
    b.setdefault("fonts", {})["arabic_heading"] = sp["font_ar_heading"]
    b["fonts"]["arabic_body"] = sp["font_ar_body"]
    write_json(brand_path(slug), b)
    return b


def logo_colors(slug, n=3):
    """Dominant opaque colours of the brand logo as hex codes (most common first)."""
    from .media import ffmpeg_bin
    from .common import run
    b = load_brand(slug)
    lf = logo_file(b)
    if not lf:
        raise StudioError("bad_brand", "this brand has no logo")
    raw = run([ffmpeg_bin(), "-v", "error", "-i", str(lf), "-vf", "scale=48:48:flags=area", "-f", "rawvideo",
               "-pix_fmt", "rgba", "-"]).stdout
    counts = {}
    for i in range(0, len(raw) - 3, 4):
        r, g, bl, a = raw[i], raw[i + 1], raw[i + 2], raw[i + 3]
        if a < 160:
            continue
        key = (r // 24 * 24 + 12, g // 24 * 24 + 12, bl // 24 * 24 + 12)
        counts[key] = counts.get(key, 0) + 1
    picked = []
    for (r, g, bl), _ in sorted(counts.items(), key=lambda kv: -kv[1]):
        if all(abs(r - x) + abs(g - y) + abs(bl - z) > 90 for x, y, z in picked):
            picked.append((min(r, 255), min(g, 255), min(bl, 255)))
        if len(picked) >= n:
            break
    return ["#%02X%02X%02X" % c for c in picked]
