#!/usr/bin/env python3
"""URM Creator Studio command line.

Claude runs these commands for the user; beginners never need to type them.
Every command accepts --lang ar|en for its messages and --json for machine output.

  doctor                         check the computer (tools, browser, fonts)
  home                           create/print the workspace folder (brands, projects, inbox, models)
  settings [--language ar|en] [--mode beginner|creator|pro] [--brand SLUG]
  brand list | show SLUG | new | set SLUG KEY VALUE | logo SLUG FILE | font SLUG FILE FAMILY
        | check SLUG | preview SLUG
  project new TITLE [--brand SLUG] [--format vertical|square|portrait|landscape] [--language ar|en|bilingual]
                    [--type social_short|ad|brand_intro|product|explainer|event|personal|talking_head|long_form|campaign]
  project list | add SLUG FILES... | show SLUG
  inspect FILES... [--sheet DIR]   analyse media (length, size, sound, cuts) + contact sheets
  card "TEXT" --out FILE.png       draw one text card (typography test)
  render PROJECT [--preview] [--format F]
  qc VERSION_DIR                   re-run quality control on an export
  transcribe PROJECT|FILE [--language ar|en|auto]
  captions check FILE.srt | captions reflow FILE.srt [--out NEW.srt]
  open inbox|home|latest --project P|PATH [--reveal]   show a folder/video to the user
  brand style SLUG luxury · brand colors SLUG [--apply]  re-apply a style / read colours from the logo
  voiceover TEXTFILE OUT.wav --language ar --approved
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from urmstudio import brand as B  # noqa: E402
from urmstudio import captions as C  # noqa: E402
from urmstudio import doctor as D  # noqa: E402
from urmstudio import media as M  # noqa: E402
from urmstudio import project as P  # noqa: E402
from urmstudio.common import (FORMATS, StudioError, ensure_home, explain_error, load_settings,  # noqa: E402
                              out, save_settings, say, studio_home, ui_lang, fmt_time, read_json)

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def emit(args, data, text):
    if getattr(args, "json", False):
        out(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    else:
        out(text)


def cmd_doctor(a, lang):
    res = D.check(lang)
    emit(a, res, D.render_text(res, lang))
    return 0 if res["ready"] else 2


def cmd_settings(a, lang):
    s = load_settings()
    if a.language:
        s["language"] = a.language
    if a.mode:
        s["mode"] = a.mode
    if a.brand is not None:
        s["default_brand"] = a.brand or None
    if a.language or a.mode or a.brand is not None:
        save_settings(s)
    emit(a, s, json.dumps(s, ensure_ascii=False, indent=2))
    return 0


def cmd_brand(a, lang):
    ensure_home()
    if a.action == "list":
        rows = []
        for s in B.list_brands():
            b = B.load_brand(s)
            rows.append({"slug": s, "name": b["name"], "logo": bool(B.logo_file(b))})
        emit(a, rows, "\n".join("• %s — %s / %s %s" % (r["slug"], r["name"].get("ar"), r["name"].get("en"),
                                                       "🖼" if r["logo"] else "") for r in rows)
             or say(lang, "لا توجد هويات بعد.", "No brands yet."))
    elif a.action == "new":
        data = None
        if a.from_file:
            data = read_json(a.from_file)
        slug = B.create_brand(a.name_ar or "", a.name_en or "", a.style or "modern", a.slug, data)
        emit(a, {"slug": slug, "path": str(B.brand_path(slug))},
             say(lang, "✅ أُنشئت الهوية: %s" % slug, "✅ Brand created: %s" % slug))
    elif a.action == "show":
        b = B.load_brand(a.slug)
        b.pop("_dir", None)
        emit(a, b, json.dumps(b, ensure_ascii=False, indent=2))
    elif a.action == "set":
        B.set_value(a.slug, a.key, a.value)
        emit(a, {"ok": True}, say(lang, "✅ تم الحفظ.", "✅ Saved."))
    elif a.action == "logo":
        dst = B.import_logo(a.slug, a.file, a.variant or "main")
        emit(a, {"logo": str(dst)}, say(lang, "✅ نُسخ الشعار إلى ملف الهوية (الأصل لم يتغير).",
                                         "✅ Logo copied into the brand (original unchanged)."))
    elif a.action == "font":
        dst = B.import_font(a.slug, a.file, a.family, a.weight or "400", a.license_ok)
        emit(a, {"font": str(dst)}, say(lang, "✅ أضيف الخط.", "✅ Font added."))
    elif a.action == "style":
        B.apply_style(a.slug, a.key)
        emit(a, {"ok": True}, say(lang, "✅ طُبّق الأسلوب.", "✅ Style applied."))
    elif a.action == "colors":
        cols = B.logo_colors(a.slug)
        if a.apply and cols:
            for k, v in zip(("primary", "secondary", "accent"), cols):
                B.set_value(a.slug, "colors." + k, v)
        emit(a, {"colors": cols, "applied": a.apply}, " ".join(cols))
    elif a.action == "check":
        b = B.load_brand(a.slug)
        probs = B.validate(b)
        emit(a, probs, "\n".join("%s %s" % ("❌" if p[0] == "error" else "⚠️", p[1]) for p in probs)
             or say(lang, "✅ الهوية سليمة.", "✅ Brand looks good."))
        return 1 if any(p[0] == "error" for p in probs) else 0
    elif a.action == "preview":
        from urmstudio.render import intro_card, outro_card, background_html
        from urmstudio.textrender import CardRenderer
        b = B.load_brand(a.slug)
        bs = B.brand_style(b)
        lg = "ar" if b.get("primary_language") != "en" else "en"
        d = Path(b["_dir"]) / "preview"
        d.mkdir(exist_ok=True)
        cr = CardRenderer(d / ".cache")
        W, H = 1080, 1350
        bg = cr.add(background_html(W, H, bs), W, H)
        i = cr.add(intro_card(W, H, "portrait", b, bs, lg), W, H)
        o = cr.add(outro_card(W, H, "portrait", b, bs, lg), W, H)
        cr.run()
        outs = []
        for name, card in (("intro", i), ("outro", o)):
            dst = d / ("%s.png" % name)
            M.run([M.ffmpeg_bin(), "-y", "-v", "error", "-i", str(bg), "-i", str(card), "-filter_complex",
                   "[0:v][1:v]overlay=0:0", "-frames:v", "1", str(dst)])
            outs.append(str(dst))
        emit(a, {"previews": outs}, "\n".join(outs))
    return 0


def cmd_project(a, lang):
    if a.action == "new":
        brand = a.brand if a.brand is not None else load_settings().get("default_brand")
        if brand:
            B.load_brand(brand)  # must exist
        slug, d = P.new_project(a.title, brand, a.format or "vertical", a.language or "ar",
                                a.type or "social", a.mode or load_settings().get("mode", "beginner"))
        emit(a, {"slug": slug, "path": str(d)}, say(lang, "✅ مشروع جديد: %s\n📁 %s" % (slug, d),
                                                     "✅ New project: %s\n📁 %s" % (slug, d)))
    elif a.action == "list":
        rows = P.list_projects()
        emit(a, rows, "\n".join("• %s — %s (%s, %d)" % (r["slug"], r["title"], r["format"], r["versions"]) for r in rows)
             or say(lang, "لا توجد مشاريع بعد.", "No projects yet."))
    elif a.action == "add":
        added = P.add_media(a.slug, a.files)
        emit(a, [str(x) for x in added], say(lang, "✅ نُسخ %d ملف إلى المشروع (الأصول لم تتغير)." % len(added),
                                             "✅ Copied %d files into the project (originals unchanged)." % len(added)))
    elif a.action == "show":
        d = P.project_dir(a.slug)
        j = read_json(d / "project.json")
        j["path"] = str(d)
        j["media"] = [p.name for p in sorted((d / "media").iterdir())] if (d / "media").exists() else []
        lv = P.latest_version(a.slug)
        j["latest_version"] = str(lv) if lv else None
        emit(a, j, json.dumps(j, ensure_ascii=False, indent=2))
    return 0


def cmd_inspect(a, lang):
    res = []
    for f in a.files:
        p = Path(f).expanduser()
        files = [x for x in sorted(p.iterdir()) if x.is_file() and M.kind_of(x) != "unknown"] if p.is_dir() else [p]
        for x in files:
            info = M.analyze(x, deep=not a.quick)
            if a.sheet and info["kind"] in ("video", "image"):
                sd = Path(a.sheet)
                info["sheet"] = str(M.contact_sheet(x, sd / (x.stem + "_sheet.png")))
            res.append(info)
    lines = []
    for i in res:
        if i["kind"] == "video":
            lines.append("🎬 %s — %s, %sx%s %s, %s fps, %s%s%s" % (
                Path(i["path"]).name, fmt_time(i["duration"]), i.get("width"), i.get("height"), i.get("orientation"),
                i.get("fps"), say(lang, "فيه صوت" if i["has_audio"] else "بدون صوت", "with sound" if i["has_audio"] else "no sound"),
                (", %s LUFS" % i["audio"].get("lufs")) if i.get("audio") else "",
                ", HDR" if i.get("hdr") else ""))
        elif i["kind"] == "image":
            lines.append("🖼 %s — %sx%s %s" % (Path(i["path"]).name, i.get("width"), i.get("height"), i.get("orientation")))
        else:
            lines.append("🎵 %s — %s" % (Path(i["path"]).name, fmt_time(i["duration"])))
    emit(a, res, "\n".join(lines))
    return 0


def cmd_card(a, lang):
    from urmstudio.textrender import build_card_html, render_html_to_png
    fmt = a.format or "vertical"
    W, H = FORMATS[fmt][:2]
    b = B.load_brand(a.brand) if a.brand else None
    bs = B.brand_style(b)
    htmls = build_card_html(width=W, height=H, fmt=fmt, text=a.text.replace("\\n", "\n"), role=a.role,
                            position=a.position, brand_style=bs, background="#202631" if a.bg else None,
                            protect=B.protected_terms(b), numerals=bs.get("numerals"))
    render_html_to_png(htmls, a.out, W, H)
    bb = M.bbox_alpha(a.out) if not a.bg else None
    emit(a, {"png": a.out, "bbox": bb}, a.out)
    return 0


def cmd_render(a, lang):
    from urmstudio.render import render
    from urmstudio.qc import run_qc
    d = P.project_dir(a.project)
    vdir, meta = render(d, preview=a.preview, fmt_override=a.format, lang=lang,
                        progress=(lambda m: None) if a.json else out)
    rep = run_qc(vdir, lang)
    data = {"version_dir": str(vdir), "video": meta["output"], "duration": meta["duration"],
            "qc": rep["overall"], "qc_report": str(vdir / "QC_REPORT.md"),
            "inspect_frames": rep["text_frames_sheet"], "overview": rep["overview"],
            "seconds_taken": meta["seconds_taken"]}
    txt = say(lang, "🎉 الفيديو جاهز: %s\n⏱ المدة: %s\n🔍 الفحص: %s\n🖼 صور للمراجعة: %s",
              "🎉 Video ready: %s\n⏱ Length: %s\n🔍 Check: %s\n🖼 Frames to review: %s") % (
        meta["output"], fmt_time(meta["duration"]), rep["overall"], rep["text_frames_sheet"])
    emit(a, data, txt)
    return 0 if rep["overall"] != "FAIL" else 3


def cmd_qc(a, lang):
    from urmstudio.qc import run_qc
    rep = run_qc(a.version_dir, lang)
    emit(a, rep, (Path(a.version_dir) / "QC_REPORT.md").read_text(encoding="utf-8"))
    return 0 if rep["overall"] != "FAIL" else 3


def cmd_transcribe(a, lang):
    target = Path(a.target).expanduser()
    if target.exists() and target.is_file():
        # drafts go to the project's captions/ folder (or the workspace inbox), never next to the user's original
        cap_dir = target.parent.parent / "captions" if target.parent.name == "media" else ensure_home() / "inbox"
        cap_dir.mkdir(parents=True, exist_ok=True)
        media, out_srt, offset = target, cap_dir / (target.stem + ".draft.srt"), 0
    else:
        d = P.project_dir(a.target)
        lv = P.latest_version(a.target)
        if not lv:
            raise StudioError("not_found", "no rendered version yet; render once without captions first")
        meta = read_json(lv / "render.json")
        media, offset = Path(meta["output"]), meta.get("content_offset", 0)
        out_srt = d / "captions" / "transcript-draft.srt"
    if offset:
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="urm-tr-")) / "content.wav"
        end = None
        M.run([M.ffmpeg_bin(), "-y", "-v", "error", "-ss", str(offset), "-i", str(media), "-vn", "-ac", "1",
               "-ar", "16000", str(tmp)])
        media = tmp
    res = C.transcribe(media, out_srt, a.language or "auto")
    res["note"] = "DRAFT: review every line with the user before burning captions"
    emit(a, res, say(lang, "📝 مسودة الترجمة: %s\nعدد المقاطع: %d — مقاطع غير واضحة تحتاج مراجعتك: %d",
                     "📝 Draft subtitles: %s\nSegments: %d — unclear segments needing your review: %d")
         % (res["srt"], res["segments"], res["flagged"]))
    return 0


def cmd_captions(a, lang):
    cues = C.parse(a.file)
    if a.action == "check":
        probs = C.check(cues)
        emit(a, probs, "\n".join("#%s %s %s" % (p["i"], p["problem"], p["detail"]) for p in probs)
             or say(lang, "✅ الترجمة مريحة للقراءة.", "✅ Captions are comfortable to read."))
    elif a.action == "reflow":
        C.write_srt(C.reflow(cues), a.out or a.file, rtl_marks=False)
        emit(a, {"ok": True}, "ok")
    return 0


def cmd_open(a, lang):
    """Show a file or folder to the user in Finder / Explorer (beginners can't use paths)."""
    import platform
    import subprocess
    t = a.target
    if t in ("inbox", "home"):
        p = ensure_home() / ("inbox" if t == "inbox" else "")
    elif t == "latest" and a.project:
        lv = P.latest_version(a.project)
        if not lv:
            raise StudioError("not_found", "no rendered version yet")
        p = Path(read_json(lv / "render.json")["output"])
    else:
        p = Path(t).expanduser()
    if not p.exists():
        raise StudioError("not_found", str(p))
    sysname = platform.system()
    if sysname == "Darwin":
        cmd = ["open", "-R", str(p)] if p.is_file() and a.reveal else ["open", str(p)]
    elif sysname == "Windows":
        cmd = ["explorer", "/select,", str(p)] if p.is_file() and a.reveal else ["explorer", str(p)]
    else:
        cmd = ["xdg-open", str(p.parent if (p.is_file() and a.reveal) else p)]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    emit(a, {"opened": str(p)}, say(lang, "✅ فُتح لك على الشاشة.", "✅ Opened on your screen."))
    return 0


def cmd_voiceover(a, lang):
    from urmstudio.voice import synthesize
    text = Path(a.textfile).read_text(encoding="utf-8")
    p = synthesize(text, a.out, a.language or "ar", a.voice, a.rate, a.approved)
    emit(a, {"wav": str(p)}, str(p))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="studio", description="URM Creator Studio")
    ap.add_argument("--lang", choices=["ar", "en"])
    ap.add_argument("--json", action="store_true")
    sp = ap.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("doctor")
    s = sp.add_parser("home")
    s = sp.add_parser("settings")
    s.add_argument("--language", choices=["ar", "en"])
    s.add_argument("--mode", choices=["beginner", "creator", "pro"])
    s.add_argument("--brand")

    s = sp.add_parser("brand")
    s.add_argument("action", choices=["list", "new", "show", "set", "logo", "font", "check", "preview", "style",
                                      "colors"])
    s.add_argument("--apply", action="store_true")
    s.add_argument("slug", nargs="?")
    s.add_argument("key", nargs="?")
    s.add_argument("value", nargs="?")
    s.add_argument("--name-ar")
    s.add_argument("--name-en")
    s.add_argument("--style", choices=["modern", "luxury", "playful", "corporate", "minimal", "bold"])
    s.add_argument("--slug", dest="slug_opt")
    s.add_argument("--from-file")
    s.add_argument("--variant")
    s.add_argument("--weight")
    s.add_argument("--license-ok", action="store_true")

    s = sp.add_parser("project")
    s.add_argument("action", choices=["new", "list", "add", "show"])
    s.add_argument("slug", nargs="?")
    s.add_argument("files", nargs="*")
    s.add_argument("--title")
    s.add_argument("--brand")
    s.add_argument("--format", choices=list(FORMATS))
    s.add_argument("--language", choices=["ar", "en", "bilingual"])
    s.add_argument("--type")
    s.add_argument("--mode", choices=["beginner", "creator", "pro"])

    s = sp.add_parser("inspect")
    s.add_argument("files", nargs="+")
    s.add_argument("--sheet")
    s.add_argument("--quick", action="store_true")

    s = sp.add_parser("card")
    s.add_argument("text")
    s.add_argument("--out", required=True)
    s.add_argument("--role", default="headline")
    s.add_argument("--position", default="center")
    s.add_argument("--format", choices=list(FORMATS))
    s.add_argument("--brand")
    s.add_argument("--bg", action="store_true", help="dark background instead of transparent")

    s = sp.add_parser("render")
    s.add_argument("project")
    s.add_argument("--preview", action="store_true")
    s.add_argument("--format", choices=list(FORMATS))

    s = sp.add_parser("qc")
    s.add_argument("version_dir")

    s = sp.add_parser("transcribe")
    s.add_argument("target")
    s.add_argument("--language", default="auto")

    s = sp.add_parser("captions")
    s.add_argument("action", choices=["check", "reflow"])
    s.add_argument("file")
    s.add_argument("--out")

    s = sp.add_parser("open")
    s.add_argument("target", help="inbox | home | latest | PATH")
    s.add_argument("--project")
    s.add_argument("--reveal", action="store_true", help="show the file selected in its folder")

    s = sp.add_parser("voiceover")
    s.add_argument("textfile")
    s.add_argument("out")
    s.add_argument("--language", choices=["ar", "en"])
    s.add_argument("--voice")
    s.add_argument("--rate", type=int)
    s.add_argument("--approved", action="store_true")

    a = ap.parse_args(argv)
    lang = ui_lang(a.lang)
    if a.cmd == "brand":
        a.file = a.key
        a.family = a.value
        if a.action == "new":
            a.slug = a.slug_opt
        elif a.action in ("logo", "font"):
            pass
    if a.cmd == "project":
        if a.action == "new":
            a.title = a.title or a.slug
            if not a.title:
                ap.error("project new needs a title")
    try:
        if a.cmd == "home":
            out(str(ensure_home()))
            return 0
        return {"doctor": cmd_doctor, "settings": cmd_settings, "brand": cmd_brand, "project": cmd_project,
                "inspect": cmd_inspect, "card": cmd_card, "render": cmd_render, "qc": cmd_qc,
                "transcribe": cmd_transcribe, "captions": cmd_captions, "voiceover": cmd_voiceover,
                "open": cmd_open}[a.cmd](a, lang)
    except StudioError as e:
        msg = explain_error(e, lang)
        if a.json:
            out(json.dumps({"error": e.code, "message": msg, "detail": e.detail}, ensure_ascii=False))
        else:
            sys.stderr.write("❌ " + msg + "\n")
            if e.code == "command_failed":
                sys.stderr.write(e.detail[-1500:] + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
