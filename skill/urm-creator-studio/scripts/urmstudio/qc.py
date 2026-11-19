"""Quality control for a rendered version folder.

Automatic checks + frames for visual inspection. Claude must still LOOK at
qc/text_frames.png (and the individual frames) before telling the user that
Arabic text is correct: automatic checks cannot see whether letters join.
"""
import json
import re
from pathlib import Path

from . import brand as brandmod
from .common import FORMATS, SAFE_MARGINS, read_json, write_json, studio_home, say
from .media import bbox_alpha, contact_sheet, frame_at, loudness, probe, ffmpeg_bin, ffprobe_bin
from .common import run


def _check_card(png, W, H, fmt, kind, bbox=None):
    bb = tuple(bbox) if bbox else bbox_alpha(png)
    if not bb:
        return {"status": "empty"}
    x1, y1, x2, y2 = bb
    res = {"bbox": bb}
    edge = 2
    if x1 <= edge or y1 <= edge or x2 >= W - 1 - edge or y2 >= H - 1 - edge:
        res["status"] = "fail"
        res["problem"] = "touches_frame_edge (text may be cut off)"
        return res
    top, right, bottom, left = SAFE_MARGINS[fmt]
    tol = 0.02
    if kind in ("watermark",):
        res["status"] = "ok"
        return res
    if (y1 < (top - tol) * H or y2 > (1 - bottom + tol) * H or x1 < (left - tol) * W
            or x2 > (1 - right + tol) * W):
        res["status"] = "warn"
        res["problem"] = "outside_safe_area (may be hidden by app buttons)"
        return res
    res["status"] = "ok"
    return res


def make_grid(images, out_png, W, H, tile_w=360, cols=3):
    """Place frames in a grid (same aspect ratio) for one-glance review."""
    tw = tile_w + 8
    th = int(round(tile_w * H / W / 2)) * 2 + 8
    cols = min(cols, len(images))
    args = [ffmpeg_bin(), "-y", "-v", "error"]
    for s in images:
        args += ["-i", s]
    fc = "".join("[%d:v]scale=%d:%d,pad=%d:%d:4:4:black[s%d];" % (i, tile_w, th - 8, tw, th, i)
                 for i in range(len(images)))
    if len(images) == 1:
        fc += "[s0]null[out]"
    else:
        pos = "|".join("%d_%d" % ((i % cols) * tw, (i // cols) * th) for i in range(len(images)))
        fc += "".join("[s%d]" % i for i in range(len(images)))
        fc += "xstack=inputs=%d:layout=%s:fill=black[out]" % (len(images), pos)
    run(args + ["-filter_complex", fc, "-map", "[out]", "-frames:v", "1", str(out_png)])
    return out_png


def run_qc(vdir, lang="ar"):
    vdir = Path(vdir)
    meta = read_json(vdir / "render.json")
    out = Path(meta["output"])
    qdir = vdir / "qc"
    (qdir / "frames").mkdir(parents=True, exist_ok=True)
    W, H, fmt = meta["width"], meta["height"], meta["format"]
    checks = []

    def add(name, status, detail=""):
        checks.append({"check": name, "status": status, "detail": detail})

    # 1. file & stream sanity
    info = probe(out)
    add("file_exists", "ok" if out.exists() and info["size_mb"] > 0 else "fail", "%.1f MB" % info["size_mb"])
    add("resolution", "ok" if (info.get("width"), info.get("height")) == (W, H) else "fail",
        "%sx%s" % (info.get("width"), info.get("height")))
    add("duration", "ok" if abs(info["duration"] - meta["duration"]) < 0.5 else "warn",
        "%.2fs (planned %.2fs)" % (info["duration"], meta["duration"]))
    # the picture itself must last the whole video (the container length follows the longest stream)
    vd = video_stream_seconds(out)
    if vd is not None:
        add("picture_complete", "ok" if vd >= meta["duration"] - 0.25 else "fail",
            "picture %.2fs of %.2fs" % (vd, meta["duration"]))
    add("video_codec", "ok" if info.get("vcodec") == "h264" and info.get("pix_fmt") == "yuv420p" else "warn",
        "%s %s" % (info.get("vcodec"), info.get("pix_fmt")))
    add("audio_track", "ok" if info.get("has_audio") else "fail", str(info.get("acodec")))
    # the whole file must decode without errors (no corrupt frames, no truncated streams)
    errs = decode_errors(out)
    add("decodes_cleanly", "fail" if errs else "ok", "; ".join(errs[:3]) or "every frame decodes")
    creative_mode = (meta.get("production") or {}).get("mode") in ("creative", "mixed")
    black, silent = black_and_silence(out, bool(info.get("has_audio")))
    # a fade from/to black at the very start or end is normal; black inside the video is not
    inner = [b for b in black if b[0] > 0.3 and b[0] + b[1] < meta["duration"] - 0.3]
    if inner:
        add("no_black_frames", "fail" if creative_mode else "warn",
            ", ".join("%.1fs black at %.1fs" % (d, st) for st, d in inner[:5]))
    else:
        add("no_black_frames", "ok", "no black frames inside the video")
    # narration must be heard to the end
    vo = meta.get("voiceover")
    if vo and vo.get("length"):
        heard = meta["duration"] - vo["start"]
        if vo["length"] > heard + 0.15:
            add("voiceover_complete", "fail", "narration is %.1fs but only %.1fs fit in the video; the end is cut off "
                "— lengthen scenes or shorten the narration" % (vo["length"], max(0.0, heard)))
        else:
            add("voiceover_complete", "ok", "narration %.1fs, video %.1fs" % (vo["length"], meta["duration"]))

    # 2. loudness
    ld = loudness(out)
    lufs = ld.get("lufs")
    if lufs is None:
        add("loudness", "warn", "could not measure")
    elif meta["duration"] - ld.get("silence_seconds", 0) < 1.0:
        add("loudness", "ok", "silent video (no music or speech)")
    elif meta.get("quiet_source_lufs") is not None:
        add("loudness", "ok", "%.1f LUFS — quiet original kept as is (see quiet_original_audio)" % lufs)
    else:
        st = "ok" if -16.5 <= lufs <= -11.5 else "warn"
        add("loudness", st, "%.1f LUFS (target -14), peak %s dBTP" % (lufs, ld.get("true_peak")))

    # 2b. no accidental dead air (silence in the middle of a video that has sound)
    if meta["duration"] - ld.get("silence_seconds", 0) >= 1.0:
        gaps = [(st, d) for st, d in silent if d is not None and st > 0.5 and st + d < meta["duration"] - 0.5]
        add("no_dead_air", "warn" if gaps else "ok",
            ", ".join("%.1fs silent at %.1fs" % (d, st) for st, d in gaps[:5]) or "sound throughout")
    # 3. text cards: clipping & safe area
    card_results = []
    for c in meta["cards"]:
        r = _check_card(c.get("png"), W, H, fmt, c["kind"], c.get("bbox"))
        r.update({"text": c["text"][:60], "kind": c["kind"], "t": round(c["t"], 2)})
        card_results.append(r)
    bad = [r for r in card_results if r["status"] == "fail"]
    warn = [r for r in card_results if r["status"] == "warn"]
    add("text_not_clipped", "fail" if bad else "ok", "; ".join("%s @%ss" % (r["text"], r["t"]) for r in bad))
    add("text_in_safe_area", "warn" if warn else "ok", "; ".join("%s @%ss" % (r["text"], r["t"]) for r in warn))

    # 3b. two texts on screen at the same time must not cover each other
    overlaps = []
    timed = [(c, r) for c, r in zip(meta["cards"], card_results) if r.get("bbox") and c["kind"] != "watermark"]
    spans = {}
    for c in meta["cards"]:
        c.setdefault("png", "motion:%s@%.2f" % (c["text"][:40], c["t"]))
        spans[c["png"]] = (c.get("start", c["t"] - 0.01), c.get("end", c["t"] + 0.01))
    for i in range(len(timed)):
        for j in range(i + 1, len(timed)):
            (ci, ri), (cj, rj) = timed[i], timed[j]
            if ci["png"] == cj["png"] or ci.get("scene") == cj.get("scene") == "caption":
                continue
            si, sj = spans[ci["png"]], spans[cj["png"]]
            if min(si[1], sj[1]) - max(si[0], sj[0]) < 0.5:  # brief co-existence during a crossfade is fine
                continue
            a, b = ri["bbox"], rj["bbox"]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                overlaps.append("%s ↔ %s" % (ci["text"][:25], cj["text"][:25]))
    add("text_overlap", "warn" if overlaps else "ok", "; ".join(overlaps[:6]))

    # 3b2. every text must be fully readable long enough (1.5 s + 0.3 s per word)
    short = []
    for c in meta["cards"]:
        if c["kind"] in ("scene_text", "motion_text") and c.get("full_visible") is not None and c["text"] not in ("intro", "outro"):
            need = 1.0 + 0.25 * len(c["text"].split())  # minimum; 1.5 s + 0.3 s/word is the comfortable target
            if c["full_visible"] < need:
                short.append("%s (%.1fs < %.1fs)" % (c["text"][:25], c["full_visible"], need))
    add("text_reading_time", "warn" if short else "ok", "; ".join(short[:5]))
    if meta.get("quiet_source_lufs") is not None:
        add("quiet_original_audio", "warn", "original sound is very quiet (%.0f LUFS, likely room noise); it was "
            "not boosted — consider muting it or adding music" % meta["quiet_source_lufs"])

    # 3c. Arabic typography lint: one numeral system per text
    mixed = []
    for c in meta["cards"]:
        t = c.get("text") or ""
        if re.search(r"[0-9]", t) and re.search(r"[\u0660-\u0669\u06F0-\u06F9]", t):
            mixed.append(t[:30])
    add("numerals_consistent", "warn" if mixed else "ok", "; ".join(mixed[:5]))

    # 4. frames for visual inspection: every text moment (captions sampled)
    shots = []
    seen = set()
    caps = [c for c in meta["cards"] if c["kind"] == "caption"]
    others = [c for c in meta["cards"] if c["kind"] not in ("caption", "watermark")]
    sample = sorted(others + caps[:: max(1, len(caps) // 6)][:6], key=lambda c: c["t"])
    for c in sample:
        t = round(min(max(c["t"], 0.05), meta["duration"] - 0.05), 2)
        if any(abs(t - x) < 0.4 for x in seen):
            continue
        seen.add(t)
        f = frame_at(out, t, qdir / "frames" / ("t%07.2f.png" % t), width=min(W, 720))
        shots.append(str(f))
    sheet = None
    if shots:
        sheet = qdir / "text_frames.png"
        try:
            make_grid(shots, sheet, W, H)
        except Exception:
            sheet = None
    overview = contact_sheet(out, qdir / "overview.png", cols=4, rows=2, width=1440)
    thumb = frame_at(out, min(meta["duration"] - 0.1, max(meta.get("intro_end", 0) + 1.0, 0.5)),
                     vdir / "thumbnail.jpg")

    # 5. originals untouched
    from .render import fingerprint
    after = fingerprint(meta.get("source_fingerprints", {}).keys())
    changed = [p for p, fp in meta.get("source_fingerprints", {}).items() if after.get(p) != fp]
    add("originals_untouched", "fail" if changed else "ok", ", ".join(changed))

    # 6. brand isolation: no other brand's name/logo in this render's cards
    leaks = []
    my = meta.get("brand")
    others_b = [b for b in brandmod.list_brands() if b != my]
    card_html = ""
    for c in meta["cards"]:
        if c["kind"] == "motion_text":
            card_html += "\n" + c["text"]
            continue
        h = Path(c["png"]).with_suffix(".html")
        if h.exists():
            card_html += h.read_text(encoding="utf-8", errors="ignore")
    ident = (meta.get("production") or {}).get("identity") or {}
    card_html += "\n" + (ident.get("name") or "")
    for ob in others_b:
        try:
            b = brandmod.load_brand(ob)
        except Exception:
            continue
        names = [b["name"].get("ar"), b["name"].get("en")] + [v for v in (b.get("handles") or {}).values()]
        for n in names:
            if n and len(n) >= 3 and n in card_html:
                # same text could be legitimately shared; flag only if it isn't in this brand too
                mine = brandmod.load_brand(my) if my else {}
                my_names = [mine.get("name", {}).get("ar"), mine.get("name", {}).get("en")] + \
                           list((mine.get("handles") or {}).values()) if mine else []
                if n not in my_names:
                    leaks.append("%s:%s" % (ob, n))
        if "/brands/%s/" % ob in card_html.replace("\\", "/"):
            leaks.append("%s:asset" % ob)
    if "URM ENROLL" in card_html and not (my and "urm" in my.lower()):
        leaks.append("distributor branding (URM ENROLL) in recipient video")
    add("brand_isolation", "fail" if leaks else "ok", ", ".join(leaks))

    # 7. captions
    cp = meta.get("caption_problems") or []
    if cp:
        add("caption_readability", "warn", "; ".join("#%s %s %s" % (p["i"], p["problem"], p["detail"]) for p in cp[:8]))
    if meta.get("hdr_sources"):
        add("hdr_footage", "warn", "HDR clips converted without full tone-mapping; check colours: "
            + ", ".join(Path(p).name for p in meta["hdr_sources"]))

    # 8. creative quality gates (the anti-slideshow rules)
    prod = meta.get("production") or {}
    creative = prod.get("mode") in ("creative", "mixed")
    freezes = freeze_spans(out, meta["duration"])
    long_f = [f for f in freezes if f[1] >= 2.0]
    mid_f = [f for f in freezes if 1.2 <= f[1] < 2.0]
    detail = ", ".join("%.1fs at %.1fs" % (d, st) for st, d in freezes[:6])
    if long_f:
        add("no_frozen_moments", "fail" if creative else "warn", "picture does not move for " + detail)
    elif mid_f:
        add("no_frozen_moments", "warn", "short still moments: " + detail)
    else:
        add("no_frozen_moments", "ok", "the picture keeps moving")
    share = prod.get("static_share")
    if share is not None:
        if share > 0.5:
            add("not_a_slideshow", "fail" if creative else "warn",
                "%.0f%% of the content is still images or plain title cards" % (share * 100))
        elif share > 0.3:
            add("not_a_slideshow", "warn", "%.0f%% of the content is still images or plain title cards" % (share * 100))
        else:
            add("not_a_slideshow", "ok", "%.0f%% still content" % (share * 100))
    if creative:
        probs = []
        if meta["duration"] >= 15 and prod.get("distinct_templates", 0) < 3:
            probs.append("only %d kinds of scenes (use at least 3 for variety)" % prod.get("distinct_templates", 0))
        if not prod.get("has_cta"):
            probs.append("no closing call-to-action scene")
        if meta["duration"] - ld.get("silence_seconds", 0) < 1.0:
            probs.append("no music or sound")
        firsts = sorted(c["start"] for c in meta["cards"] if c["kind"] in ("motion_text", "scene_text"))
        if not firsts or firsts[0] - meta.get("content_offset", 0) > 2.0:
            probs.append("no on-screen hook in the first 2 seconds")
        add("creative_structure", ("fail" if prod.get("mode") == "creative" else "warn") if probs else "ok", "; ".join(probs) or
            "%d scene types, hook, soundtrack, call to action" % prod.get("distinct_templates", 0))

    statuses = [c["status"] for c in checks]
    overall = "FAIL" if "fail" in statuses else ("WARN" if "warn" in statuses else "PASS")
    report = {"overall": overall, "checks": checks, "cards": card_results, "frames": shots,
              "text_frames_sheet": str(sheet) if sheet else None, "overview": str(overview),
              "thumbnail": str(thumb),
              "visual_inspection_required": True,
              "visual_inspection_note": "Open text_frames.png and confirm Arabic letters join, words are in the "
                                        "right order, nothing is cut off, and diacritics/dots are visible."}
    # 9. deliverables: cover + production manifest
    cover = None
    try:
        cover = frame_at(out, min(meta["duration"] - 0.1, meta.get("cover_t") or 1.0), vdir / "cover.jpg")
    except Exception:
        cover = None
    report["cover"] = str(cover) if cover else None
    write_json(qdir / "report.json", report)
    _write_md(vdir, meta, report, lang)
    write_manifest(vdir, meta, report)
    return report


def video_stream_seconds(video):
    cp = run([ffprobe_bin(),
              "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
              "stream=nb_read_packets,r_frame_rate", "-of", "json", str(video)], check=False)
    try:
        st = json.loads(cp.stdout.decode("utf-8"))["streams"][0]
        num, den = (int(x) for x in st["r_frame_rate"].split("/"))
        return int(st["nb_read_packets"]) * den / float(num)
    except Exception:
        return None


def decode_errors(video):
    """Full decode of every stream; returns the decoder's error lines (empty = the file plays cleanly)."""
    cp = run([ffmpeg_bin(), "-hide_banner", "-nostats", "-v", "error", "-i", str(video), "-map", "0",
              "-f", "null", "-"], check=False)
    lines = [ln for ln in cp.stderr.decode("utf-8", "replace").splitlines() if ln.strip()]
    if cp.returncode != 0 and not lines:
        lines = ["ffmpeg exit %s" % cp.returncode]
    return lines


def black_and_silence(video, has_audio=True):
    """(black spans, silent spans): black = 98% of pixels near pure black for 0.4 s or more (a dark look
    is not black); silence = below -45 dB for 2 s or more."""
    args = [ffmpeg_bin(), "-hide_banner", "-nostats", "-i", str(video),
            "-filter_complex", "[0:v]scale=270:-2,blackdetect=d=0.4:pic_th=0.98:pix_th=0.03[v]"
            + (";[0:a]silencedetect=n=-45dB:d=2.0[a]" if has_audio else ""),
            "-map", "[v]"] + (["-map", "[a]"] if has_audio else []) + ["-f", "null", "-"]
    txt = run(args, check=False).stderr.decode("utf-8", "replace")
    black = [(float(a), float(b) - float(a)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", txt)]
    ss = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", txt)]
    sd = [float(x) for x in re.findall(r"silence_duration: ([\d.]+)", txt)]
    silent = list(zip(ss, sd))
    if len(ss) > len(sd):
        silent.append((ss[-1], None))  # silent until the end
    return black, silent


def freeze_spans(video, duration):
    """(start, seconds) of moments where the picture does not change at all."""
    cp = run([ffmpeg_bin(), "-hide_banner", "-i", str(video), "-map", "0:v", "-vf",
              "scale=270:-2,freezedetect=n=0.0015:d=1.0", "-f", "null", "-"], check=False)
    txt = cp.stderr.decode("utf-8", "replace")
    starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", txt)]
    durs = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", txt)]
    res = list(zip(starts, durs))
    if len(starts) > len(durs):   # frozen until the end
        res.append((starts[-1], max(0.0, duration - starts[-1])))
    return res


def write_manifest(vdir, meta, report):
    """production.json: what was delivered, how it was made, and where every element came from."""
    prod = meta.get("production") or {}
    files = {"video": meta["output"], "cover": report.get("cover"), "thumbnail": report.get("thumbnail"),
             "qc_report": str(vdir / "QC_REPORT.md")}
    for name in ("captions.srt", "captions.vtt", "onscreen_text.srt"):
        if (vdir / name).exists():
            files[name.replace(".", "_")] = str(vdir / name)
    m = {"studio_version": meta.get("studio_version"), "rendered_at": meta.get("rendered_at"),
         "project": meta.get("project"), "format": meta["format"], "size": "%dx%d" % (meta["width"], meta["height"]),
         "fps": meta.get("fps"), "duration": meta["duration"], "preview": meta.get("preview"),
         "production_mode": prod.get("mode"), "look": prod.get("look"), "palette": prod.get("palette"), "identity": prod.get("identity"),
         "scenes": prod.get("seconds_by_kind"), "motion_templates": prod.get("templates"),
         "assets": prod.get("assets"),
         # file names relative to this version folder: the manifest can travel with the video without
         # revealing the user's folders or account name
         "deliverables": {k: (Path(v).name if v else None) for k, v in files.items()}, "qc": report["overall"],
         "notes": ["Engine-generated graphics and soundtrack are original to this video.",
                   "AI-generated or stock files keep the provider and licence recorded under assets; they were "
                   "not made by URM Creator Studio."]}
    write_json(vdir / "production.json", m)


ICON = {"ok": "✅", "warn": "⚠️", "fail": "❌", "empty": "▫️"}
NAMES = {
    "file_exists": ("الملف موجود", "File created"),
    "resolution": ("المقاس صحيح", "Correct size"),
    "duration": ("المدة", "Duration"),
    "video_codec": ("صيغة متوافقة مع المنصات", "Platform-compatible format"),
    "audio_track": ("مسار الصوت", "Audio track"),
    "loudness": ("مستوى الصوت مناسب للسوشيال", "Loudness for social media"),
    "text_not_clipped": ("النصوص غير مقصوصة", "Text not cut off"),
    "text_in_safe_area": ("النصوص بعيدة عن أزرار التطبيقات", "Text clear of app buttons"),
    "originals_untouched": ("ملفاتك الأصلية لم تتغير", "Your originals untouched"),
    "brand_isolation": ("لا توجد هوية أخرى في الفيديو", "No other brand in the video"),
    "caption_readability": ("سهولة قراءة الترجمة", "Caption readability"),
    "hdr_footage": ("ألوان مقاطع HDR", "HDR clip colours"),
    "text_overlap": ("النصوص لا تغطي بعضها", "Texts don't cover each other"),
    "numerals_consistent": ("نوع الأرقام موحّد في كل نص", "One numeral style per text"),
    "text_reading_time": ("كل نص يبقى وقتًا كافيًا للقراءة", "Every text stays long enough to read"),
    "quiet_original_audio": ("صوت الفيديو الأصلي خافت جدًا", "Original sound very quiet"),
    "picture_complete": ("الصورة كاملة حتى نهاية الفيديو", "Picture runs to the end"),
    "no_frozen_moments": ("الصورة تتحرك طوال الفيديو", "The picture keeps moving"),
    "not_a_slideshow": ("ليس عرض شرائح", "Not a slideshow"),
    "decodes_cleanly": ("الملف يعمل بدون أخطاء", "File plays without errors"),
    "no_black_frames": ("لا توجد لقطات سوداء", "No black frames"),
    "voiceover_complete": ("التعليق الصوتي كامل حتى النهاية", "Narration heard to the end"),
    "no_dead_air": ("لا يوجد صمت مفاجئ", "No accidental silence"),
    "creative_structure": ("بناء إبداعي كامل (افتتاحية، تنوع، موسيقى، دعوة)", "Complete creative structure (hook, variety, sound, CTA)"),
}


def _write_md(vdir, meta, report, lang):
    L = []
    L.append("# QC — %s (%s)\n" % (vdir.name, meta["format"]))
    L.append("**%s**  \n" % report["overall"])
    for c in report["checks"]:
        ar, en = NAMES.get(c["check"], (c["check"], c["check"]))
        L.append("- %s %s / %s %s" % (ICON.get(c["status"], ""), ar, en, ("— " + c["detail"]) if c["detail"] else ""))
    L.append("\nFrames to inspect / صور للمراجعة: `qc/text_frames.png`, `qc/overview.png`")
    (vdir / "QC_REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
