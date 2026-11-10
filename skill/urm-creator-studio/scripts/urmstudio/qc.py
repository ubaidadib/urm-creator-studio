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
from .media import bbox_alpha, contact_sheet, frame_at, loudness, probe, ffmpeg_bin
from .common import run


def _check_card(png, W, H, fmt, kind):
    bb = bbox_alpha(png)
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
    add("video_codec", "ok" if info.get("vcodec") == "h264" and info.get("pix_fmt") == "yuv420p" else "warn",
        "%s %s" % (info.get("vcodec"), info.get("pix_fmt")))
    add("audio_track", "ok" if info.get("has_audio") else "fail", str(info.get("acodec")))

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

    # 3. text cards: clipping & safe area
    card_results = []
    for c in meta["cards"]:
        r = _check_card(c["png"], W, H, fmt, c["kind"])
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
        if c["kind"] == "scene_text" and c.get("full_visible") is not None and c["text"] not in ("intro", "outro"):
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
        h = Path(c["png"]).with_suffix(".html")
        if h.exists():
            card_html += h.read_text(encoding="utf-8", errors="ignore")
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

    statuses = [c["status"] for c in checks]
    overall = "FAIL" if "fail" in statuses else ("WARN" if "warn" in statuses else "PASS")
    report = {"overall": overall, "checks": checks, "cards": card_results, "frames": shots,
              "text_frames_sheet": str(sheet) if sheet else None, "overview": str(overview),
              "thumbnail": str(thumb),
              "visual_inspection_required": True,
              "visual_inspection_note": "Open text_frames.png and confirm Arabic letters join, words are in the "
                                        "right order, nothing is cut off, and diacritics/dots are visible."}
    write_json(qdir / "report.json", report)
    _write_md(vdir, meta, report, lang)
    return report


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
