#!/usr/bin/env python3
"""Regression test: burned-in captions must be VISIBLE in the rendered video (checked in real frames).

Covers the 1.0.0 defect where captions silently disappeared when
  * the plan uses hard cuts (transition "none"), so segments are joined with `concat -c copy`, and
  * a brand intro card (untagged colour) is followed by camera footage tagged bt709/tv (normal phone footage).
FFmpeg then re-initialises the filter graph at the colour change, and captions that were fed as a single image
frame were lost. The test checks pixels, not exit codes.

  python3 tests/regression_captions_hardcut.py --fixtures DIR --out DIR [--skill PATH_TO_SKILL]

Cases (all with the brand intro and outro):
  en_hardcut_tagged   English captions, hard cuts, bt709-tagged footage   (the 1.0.0 failure case)
  ar_hardcut_tagged   Arabic captions, hard cuts, bt709-tagged footage   (the 1.0.0 failure case)
  en_fade_tagged      English captions, fade transitions                 (control: xfade path)
  en_hardcut_plain    English captions, hard cuts, untagged footage      (control)
  *_nocap             the same videos without captions                   (no-subtitle workflow + pixel baseline)
Writes OUT/RESULTS.json, OUT/RESULTS.md and OUT/frames/<case>.png (one frame per caption cue, for a human to look at).
"""
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN_SRT = ("1\n00:00:00,300 --> 00:00:02,600\nHello everyone, welcome back.\n\n"
          "2\n00:00:02,700 --> 00:00:05,600\nToday: three simple tips to stay focused.\n")
AR_SRT = ("1\n00:00:00,300 --> 00:00:02,600\nأهلًا وسهلًا بكم في المقهى.\n\n"
          "2\n00:00:02,700 --> 00:00:05,600\nقهوتك المفضلة بانتظارك كل صباح.\n")


def sh(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)


def frame_gray(video, t, box, scale=4):
    x0, y0, x1, y1 = box
    w, h = max(2, (x1 - x0) // scale * scale), max(2, (y1 - y0) // scale * scale)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % t, "-i", str(video), "-frames:v", "1", "-vf",
                          "crop=%d:%d:%d:%d,scale=%d:%d" % (w, h, x0, y0, w // scale, h // scale),
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skill", default=str(ROOT / "skill" / "urm-creator-studio"))
    a = ap.parse_args()
    skill, fx, out = Path(a.skill), Path(a.fixtures), Path(a.out)
    ws = out / "workspace"
    shutil.rmtree(ws, ignore_errors=True); (out / "frames").mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, URM_STUDIO_HOME=str(ws))

    def st(*args):
        cp = sh([sys.executable, skill / "scripts" / "studio.py", "--lang", "en", "--json", *args], env=env)
        try:
            return json.loads(cp.stdout) if cp.stdout.strip() else {}, cp.returncode
        except json.JSONDecodeError:
            return {"raw": cp.stdout[-500:], "err": cp.stderr[-500:]}, cp.returncode

    # phone-style footage: same pictures, but tagged bt709 / limited range like real camera files
    media = out / "media"; media.mkdir(exist_ok=True)
    for name in ("speech_en.mp4", "speech_ar.mp4"):
        dst = media / name.replace(".mp4", "_bt709.mp4")
        if not dst.exists():
            r = sh(["ffmpeg", "-v", "error", "-y", "-i", fx / name, "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-c:a", "copy", dst])
            if r.returncode: sys.exit("fixture prep failed: " + r.stderr)
    res, _ = st("brand", "new", "--from-file", str(ROOT / "examples" / "brands" / "bilingual-studio.json"))
    brand = res["slug"]
    st("brand", "logo", brand, str(fx / "logo_bilingual.png"))

    cases = [("en_hardcut_tagged", "en", media / "speech_en_bt709.mp4", "none", EN_SRT),
             ("ar_hardcut_tagged", "ar", media / "speech_ar_bt709.mp4", "none", AR_SRT),
             ("en_fade_tagged", "en", media / "speech_en_bt709.mp4", "fade", EN_SRT),
             ("en_hardcut_plain", "en", fx / "speech_en.mp4", "none", EN_SRT)]
    results = []
    for name, lang, clip, trans, srt in cases:
        renders = {}
        for cap in (True, False):
            label = name if cap else name + "_nocap"
            res, _ = st("project", "new", "--title", label, "--brand", brand, "--format", "vertical", "--language", lang)
            slug = res["slug"]; pdir = ws / "projects" / slug
            st("project", "add", slug, str(clip))
            plan = {"title": label, "brand": brand, "format": "vertical", "language": lang,
                    "transition": {"type": trans, "duration": 0.35 if trans != "none" else 0},
                    "scenes": [{"kind": "video", "src": "media/" + clip.name, "start": 0.0, "end": 3.0},
                               {"kind": "video", "src": "media/" + clip.name, "start": 3.0, "end": 6.0}],
                    "branding": {"intro": True, "outro": True}}
            if cap:
                (pdir / "captions").mkdir(exist_ok=True)
                (pdir / "captions" / (lang + ".srt")).write_text(srt, encoding="utf-8")
                plan["captions"] = {"src": "captions/%s.srt" % lang, "burn": True, "style": "box"}
            (pdir / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
            r, code = st("render", slug)
            renders[cap] = (r, code)
        (rc, cc), (rn, cn) = renders[True], renders[False]
        row = {"case": name, "transition": trans, "footage": clip.name, "render_exit": [cc, cn]}
        if cc or cn or "version_dir" not in rc:
            row.update(status="FAIL", reason="render failed", detail=str(rc)[:400]); results.append(row); continue
        vd, vdn = Path(rc["version_dir"]), Path(rn["version_dir"])
        mp4 = next(vd.glob("*_vertical.mp4")); mp4n = next(vdn.glob("*_vertical.mp4"))
        rj = json.loads((vd / "render.json").read_text(encoding="utf-8"))
        caps = [c for c in rj.get("cards", []) if c.get("kind") == "caption"]
        from PIL import Image
        checks, shots = [], []
        for c in caps:
            box = Image.open(c["png"]).getbbox()
            t = (c["start"] + c["end"]) / 2
            a, b = frame_gray(mp4, t, box), frame_gray(mp4n, t, box)
            diff = sum(abs(x - y) for x, y in zip(a, b)) / max(1, len(a))
            checks.append({"text": c.get("text"), "t": round(t, 2), "box": box, "mean_pixel_diff_vs_nocap": round(diff, 1),
                           "visible": diff > 12})
            png = out / "frames" / ("%s_t%.2f.png" % (name, t))
            sh(["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % t, "-i", mp4, "-frames:v", "1", "-vf", "scale=540:-1", png]); shots.append(png)
        if shots:
            sh(["ffmpeg", "-v", "error", "-y", *sum([["-i", s] for s in shots], []), "-filter_complex",
                "hstack=inputs=%d" % len(shots) if len(shots) > 1 else "null", out / "frames" / ("%s.png" % name)])
        srt_ok = (vd / "captions.srt").exists() and (vd / "captions.vtt").exists()
        vtt_head = (vd / "captions.vtt").read_text(encoding="utf-8").startswith("WEBVTT") if srt_ok else False
        nocap_ok = not any(c.get("kind") == "caption" for c in json.loads((vdn / "render.json").read_text(encoding="utf-8")).get("cards", []))
        ok = bool(caps) and all(x["visible"] for x in checks) and srt_ok and vtt_head and nocap_ok
        row.update(status="PASS" if ok else "FAIL", captions=checks, sidecars_srt_vtt=srt_ok and vtt_head,
                   nocap_render_ok=nocap_ok, qc=[json.loads((d / "qc" / "report.json").read_text())["overall"] for d in (vd, vdn)],
                   video=str(mp4))
        results.append(row)
        print("[%s] %s — captions visible: %s" % (row["status"], name, [x["visible"] for x in checks]))
    ver = sh(["ffmpeg", "-version"]).stdout.split("\n")[0]
    summary = {"skill": str(skill), "ffmpeg": ver, "results": results,
               "passed": sum(r["status"] == "PASS" for r in results), "total": len(results)}
    (out / "RESULTS.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Caption visibility regression", "", "Engine: `%s`  " % skill, "FFmpeg: %s" % ver, "",
             "| Case | Transition | Footage | Result | Captions visible (pixel diff vs no-caption render) | SRT+VTT | No-caption render |",
             "|---|---|---|---|---|---|---|"]
    for r in results:
        vis = ", ".join("%s (%.0f)" % ("yes" if c["visible"] else "NO", c["mean_pixel_diff_vs_nocap"]) for c in r.get("captions", []))
        lines.append("| %s | %s | %s | **%s** | %s | %s | %s |" % (r["case"], r["transition"], r["footage"], r["status"], vis or r.get("reason", ""),
                                                             r.get("sidecars_srt_vtt"), r.get("nocap_render_ok")))
    (out / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("%d/%d PASS" % (summary["passed"], summary["total"]))
    sys.exit(0 if summary["passed"] == summary["total"] else 1)


if __name__ == "__main__":
    main()
