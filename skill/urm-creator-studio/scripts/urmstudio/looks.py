"""Visual looks and temporary identities for creative-led production.

A *look* is the complete visual language of a video made without brand assets: palette, type pairing,
background world, transition family, camera behaviour and soundtrack mood. When the user has a brand, the
look is derived from the brand's colours and fonts instead, so motion scenes stay on-brand.

A *temporary identity* is what stands in for a missing logo: the business name as a wordmark plus a monogram
mark built from its initials. It is clearly a placeholder the user can replace later with a real logo.
"""
import re

from . import brand as brandmod
from .common import has_arabic

LOOKS = {
    # name: palette + defaults. "mood" picks the soundtrack; "transitions" the family used between scenes.
    "academy": {"label": ("أكاديمي واثق", "Confident academy"), "for": "education, training, consulting, trust",
                "palette": {"bg": "#081329", "bg2": "#11305C", "primary": "#2F6FEB", "secondary": "#16B3A3",
                            "accent": "#FFC23D", "text": "#FFFFFF", "muted": "#C8D5F0"},
                "fonts": ("Cairo", "Tajawal", "Inter", "Inter"), "mood": "inspiring",
                "transitions": ["slide", "panels", "swap"], "grid": False},
    "fresh": {"label": ("حديث ومنعش", "Fresh & modern"), "for": "health, apps, services, startups",
              "palette": {"bg": "#04211F", "bg2": "#0A4640", "primary": "#12B886", "secondary": "#22B8CF",
                          "accent": "#FFE066", "text": "#FFFFFF", "muted": "#C3F0E3"},
              "fonts": ("Cairo", "Tajawal", "Inter", "Inter"), "mood": "corporate",
              "transitions": ["slide", "swap", "circle"], "grid": False},
    "warm": {"label": ("دافئ وودود", "Warm & friendly"), "for": "food, cafés, family, community, retail",
             "palette": {"bg": "#2B1207", "bg2": "#5E2611", "primary": "#E8590C", "secondary": "#F59F00",
                         "accent": "#FFF3BF", "text": "#FFFFFF", "muted": "#FFE3C7"},
             "fonts": ("Cairo", "Tajawal", "Inter", "Inter"), "mood": "playful",
             "transitions": ["swap", "slide", "circle"], "grid": False},
    "luxury": {"label": ("فاخر وهادئ", "Luxury & calm"), "for": "fashion, perfume, jewellery, hospitality, real estate",
               "palette": {"bg": "#0B0A09", "bg2": "#201B14", "primary": "#8C6D35", "secondary": "#3D3020",
                           "accent": "#D9B45B", "text": "#FFF8EC", "muted": "#E3D6BD"},
               "fonts": ("Amiri", "Noto Naskh Arabic", "Inter", "Inter"), "mood": "luxury",
               "transitions": ["swap", "swap", "slide"], "grid": False},
    "tech": {"label": ("تقني وجريء", "Tech & bold"), "for": "software, AI, gaming, electronics",
             "palette": {"bg": "#05060F", "bg2": "#14164A", "primary": "#6366F1", "secondary": "#06B6D4",
                         "accent": "#A3E635", "text": "#FFFFFF", "muted": "#C7CBF5"},
             "fonts": ("Noto Kufi Arabic", "Tajawal", "Inter", "Inter"), "mood": "energetic",
             "transitions": ["panels", "slide", "circle"], "grid": True},
    "bold": {"label": ("حماسي وقوي", "Bold & energetic"), "for": "sales, sport, events, launches",
             "palette": {"bg": "#130606", "bg2": "#420E0E", "primary": "#E03131", "secondary": "#F76707",
                         "accent": "#FFD43B", "text": "#FFFFFF", "muted": "#FFD8C2"},
             "fonts": ("Cairo", "Cairo", "Inter", "Inter"), "mood": "energetic",
             "transitions": ["panels", "slide", "panels"], "grid": False},
    "calm": {"label": ("هادئ ونقي", "Calm & clean"), "for": "wellness, beauty, clinics, non-profits",
             "palette": {"bg": "#EFE7DC", "bg2": "#FBF8F3", "primary": "#3F7D6E", "secondary": "#9DBF9E",
                         "accent": "#E07A5F", "text": "#1D2A27", "muted": "#4E5F5A", "light": True},
             "fonts": ("Tajawal", "Tajawal", "Inter", "Inter"), "mood": "calm",
             "transitions": ["swap", "slide", "swap"], "grid": False},
    "playful": {"label": ("مرح وملوّن", "Playful & colourful"), "for": "kids, youth, games, social creators",
                "palette": {"bg": "#1C0A38", "bg2": "#4A1D96", "primary": "#8B5CF6", "secondary": "#EC4899",
                            "accent": "#FDE047", "text": "#FFFFFF", "muted": "#E9D5FF"},
                "fonts": ("Cairo", "Cairo", "Inter", "Inter"), "mood": "playful",
                "transitions": ["circle", "slide", "panels"], "grid": False},
}

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _hex(rgb):
    return "#" + "".join("%02x" % max(0, min(255, int(round(v)))) for v in rgb)


def mix(a, b, p):
    ra, rb = _rgb(a), _rgb(b)
    return _hex([x + (y - x) * p for x, y in zip(ra, rb)])


def _lum(h):
    return brandmod._lum(h)


def complete_palette(p):
    """Add the derived colours the runtime needs (readable text on the accent, light tints, cards)."""
    p = dict(p)
    light = bool(p.get("light"))
    p.setdefault("muted", mix(p["text"], p["bg"], 0.25))
    p["primaryLight"] = mix(p["primary"], "#FFFFFF", 0.35 if not light else 0.0)
    p["accentText"] = "#111111" if _lum(p["accent"]) > 0.45 else "#FFFFFF"
    p["card"] = "rgba(255,255,255,0.09)" if not light else "rgba(255,255,255,0.78)"
    p["particle"] = mix(p["text"], p["accent"], 0.3)
    p["light"] = light
    return p


def look_from_brand(b):
    """Derive a motion look from a saved brand profile (colours, fonts, numerals)."""
    st = brandmod.brand_style(b)
    prim, sec, acc = st["primary"], st["secondary"], st["accent"]
    base = prim if _lum(prim) <= _lum(sec) else sec
    if _lum(base) > 0.35:   # very light brand colours: build a dark stage from them
        base = mix(base, "#000000", 0.55)
    bg, bg2 = mix(base, "#000000", 0.72), mix(base, "#000000", 0.42)
    if _lum(acc) < 0.12 or brandmod.contrast(acc, bg) < 2.5:
        acc = mix(acc, "#FFFFFF", 0.6) if _lum(acc) < 0.5 else acc
    pal = {"bg": bg, "bg2": bg2, "primary": prim, "secondary": sec, "accent": acc,
           "text": "#FFFFFF", "muted": mix("#FFFFFF", prim, 0.2)}
    style = (b or {}).get("visual_style", "modern")
    mood = {"luxury": "luxury", "playful": "playful", "bold": "energetic", "minimal": "calm",
            "corporate": "corporate"}.get(style, "inspiring")
    trans = {"luxury": ["swap"], "minimal": ["swap"], "bold": ["panels", "slide"],
             "playful": ["circle", "slide"]}.get(style, ["slide", "panels", "swap"])
    return {"name": "brand", "palette": complete_palette(pal),
            "fonts": {"ar_head": st["font_ar_heading"], "ar_body": st["font_ar_body"],
                      "lat_head": st["font_latin_heading"], "lat_body": st["font_latin_body"]},
            "mood": mood, "transitions": trans, "grid": False, "grain": True}


def resolve_look(plan, b):
    """plan["look"] may be a preset name, a dict with overrides, or absent (brand → brand look, else academy)."""
    spec = plan.get("look")
    if isinstance(spec, str):
        spec = {"preset": spec}
    spec = dict(spec or {})
    preset = spec.get("preset")
    if preset and preset not in LOOKS:
        preset = None
    if b and not preset:
        lk = look_from_brand(b)
    else:
        L = LOOKS[preset or "academy"]
        f = L["fonts"]
        lk = {"name": preset or "academy", "palette": complete_palette(L["palette"]),
              "fonts": {"ar_head": f[0], "ar_body": f[1], "lat_head": f[2], "lat_body": f[3]},
              "mood": L["mood"], "transitions": list(L["transitions"]), "grid": L["grid"], "grain": True}
    # explicit overrides (e.g. colours the user mentioned in the brief)
    pal = dict(lk["palette"])
    for k, v in (spec.get("palette") or {}).items():
        if k in ("bg", "bg2", "primary", "secondary", "accent", "text", "muted") and HEX.match(str(v)):
            pal[k] = v
    lk["palette"] = complete_palette({k: v for k, v in pal.items() if k not in ("primaryLight", "accentText", "card", "particle")})
    for k in ("mood", "grid", "grain"):
        if k in spec:
            lk[k] = spec[k]
    if spec.get("transitions"):
        lk["transitions"] = list(spec["transitions"])
    if spec.get("fonts"):
        lk["fonts"].update({k: v for k, v in spec["fonts"].items() if k in lk["fonts"]})
    return lk


def initials(name):
    words = [w for w in re.split(r"[\s\-_/&]+", name or "") if w and w[0].isalnum()]
    if not words:
        return ""
    if has_arabic(name):
        return words[0][0]
    return "".join(w[0] for w in words[:2]).upper()


def resolve_identity(plan, b, lang, logo_path=None):
    """Brand name + mark for motion scenes: the real logo when there is one, otherwise a temporary monogram."""
    spec = dict(plan.get("identity") or {})
    name = spec.get("name") or (brandmod.display_name(b, lang) if b else "")
    latin = (b or {}).get("name", {}).get("en") if b else None
    ident = {"name": name, "initials": spec.get("initials") or initials(latin or name),
             "shape": spec.get("shape", "circle"), "temporary": not bool(logo_path)}
    if logo_path:
        ident["logo_path"] = str(logo_path)
    return ident
