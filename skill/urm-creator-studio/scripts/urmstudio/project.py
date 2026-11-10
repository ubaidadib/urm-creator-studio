"""Projects: <workspace>/projects/<slug>/ with plan.json, media/, captions/, output/vNNN/."""
import datetime
import shutil
from pathlib import Path

from .common import FORMATS, StudioError, ensure_home, read_json, slugify, studio_home, write_json
from .media import kind_of, probe


def projects_dir():
    return studio_home() / "projects"


def project_dir(slug):
    p = Path(slug)
    if p.is_absolute() and p.exists():
        return p
    d = projects_dir() / slug
    if not d.exists():
        raise StudioError("not_found", "project '%s'" % slug)
    return d


def list_projects():
    d = projects_dir()
    if not d.exists():
        return []
    res = []
    for p in sorted(d.glob("*/project.json")):
        try:
            j = read_json(p)
        except Exception:
            continue
        outs = sorted((p.parent / "output").glob("v[0-9][0-9][0-9]"))  # finals only
        res.append({"slug": p.parent.name, "title": j.get("title"), "brand": j.get("brand"),
                    "format": j.get("format"), "versions": len(outs)})
    return res


def new_project(title, brand=None, fmt="vertical", language="ar", video_type="social", mode="beginner"):
    ensure_home()
    if fmt not in FORMATS:
        raise StudioError("bad_plan", "unknown format %s" % fmt)
    base = slugify(title, "video")
    slug, i = base, 2
    while (projects_dir() / slug).exists():
        slug = "%s-%d" % (base, i)
        i += 1
    d = projects_dir() / slug
    for sub in ("media", "captions", "output", "work"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    write_json(d / "project.json", {
        "schema": 1, "slug": slug, "title": title, "brand": brand, "format": fmt, "language": language,
        "video_type": video_type, "mode": mode,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
    })
    write_json(d / "plan.json", {
        "title": title, "brand": brand, "format": fmt, "language": language, "fps": 30,
        "quality": "standard", "transition": {"type": "fade", "duration": 0.35},
        "scenes": [], "overlays": [], "captions": {}, "audio": {"normalize": True},
        "branding": {},
    })
    return slug, d


def add_media(slug, files):
    """COPY files into the project (originals stay where they are, unchanged)."""
    d = project_dir(slug) / "media"
    d.mkdir(exist_ok=True)
    added = []
    for f in files:
        src = Path(f).expanduser()
        if not src.exists():
            raise StudioError("not_found", str(src))
        if src.is_dir():
            for g in sorted(src.iterdir()):
                if g.is_file() and kind_of(g) != "unknown":
                    added.append(_copy(g, d))
            continue
        added.append(_copy(src, d))
    return added


def _copy(src, d):
    dst = d / src.name
    n = 2
    while dst.exists():
        if dst.stat().st_size == src.stat().st_size:
            return dst  # already copied
        dst = d / ("%s-%d%s" % (src.stem, n, src.suffix))
        n += 1
    shutil.copy2(src, dst)
    try:
        dst.chmod(0o444)  # read-only working copy: protects against accidental edits
    except OSError:
        pass
    return dst


def latest_version(slug, include_previews=True):
    """Most recently rendered output folder (final or preview)."""
    out = project_dir(slug) / "output"
    outs = list(out.glob("v[0-9][0-9][0-9]"))
    if include_previews:
        outs += list(out.glob("preview-[0-9][0-9][0-9]"))
    outs = [o for o in outs if (o / "render.json").exists()]
    return max(outs, key=lambda o: (o / "render.json").stat().st_mtime) if outs else None
