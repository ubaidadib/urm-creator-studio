#!/usr/bin/env python3
"""Acceptance tests for URM Creator Studio.

  python3 tests/run_acceptance.py --fixtures DIR --out RESULTS_DIR [--skill PATH_TO_SKILL] [--only 3,5]

Runs every scenario in a brand-new, isolated workspace (URM_STUDIO_HOME inside RESULTS_DIR), renders real
videos, runs QC, and collects the QC frame sheets so a human/Claude can inspect the Arabic text.
Scenarios 1 and 2 (beginner onboarding conversations) are tested separately (see tests/ONBOARDING_TESTS.md);
here they cover the language-specific device check.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


class Runner:
    def __init__(self, skill, fixtures, out):
        self.skill = Path(skill)
        self.fx = Path(fixtures)
        self.out = Path(out)
        self.ws = self.out / "workspace"
        if self.ws.exists():
            shutil.rmtree(self.ws, ignore_errors=True)
        self.env = dict(os.environ, URM_STUDIO_HOME=str(self.ws))
        self.results = []

    def st(self, *args, check=True, lang="en"):
        cmd = [sys.executable, str(self.skill / "scripts" / "studio.py"), "--lang", lang, "--json", *map(str, args)]
        cp = subprocess.run(cmd, capture_output=True, text=True, env=self.env)
        if check and cp.returncode not in (0,):
            raise RuntimeError("studio %s failed (%s): %s %s" % (args[:2], cp.returncode, cp.stdout[-800:], cp.stderr[-800:]))
        try:
            return json.loads(cp.stdout) if cp.stdout.strip() else {}, cp.returncode
        except json.JSONDecodeError:
            return {"raw": cp.stdout}, cp.returncode

    def project_dir(self, slug):
        return self.ws / "projects" / slug

    def write_plan(self, slug, plan):
        (self.project_dir(slug) / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    def render(self, slug, **kw):
        args = ["render", slug]
        if kw.get("preview"):
            args.append("--preview")
        if kw.get("fmt"):
            args += ["--format", kw["fmt"]]
        res, code = self.st(*args, check=False)
        return res, code

    def record(self, sid, name, status, details, evidence=None):
        self.results.append({"id": sid, "name": name, "status": status, "details": details, "evidence": evidence or []})
        print("[%s] %s — %s" % (status, name, details if isinstance(details, str) else ""))

    def collect(self, res, label):
        ev = []
        if res.get("inspect_frames") and Path(res["inspect_frames"]).exists():
            dst = self.out / "frames" / ("%s.png" % label)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(res["inspect_frames"], dst)
            ev.append(str(dst.relative_to(self.out)))
        return ev

    def qc_summary(self, res):
        vd = Path(res["version_dir"])
        rep = json.loads((vd / "qc" / "report.json").read_text(encoding="utf-8"))
        return rep["overall"], {c["check"]: c["status"] for c in rep["checks"]}, rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skill", default=str(ROOT / "skill" / "urm-creator-studio"))
    ap.add_argument("--only")
    a = ap.parse_args()
    only = set(a.only.split(",")) if a.only else None
    R = Runner(a.skill, a.fixtures, a.out)
    fx = R.fx
    t0 = time.time()
    originals = {p.name: sha(p) for p in fx.iterdir() if p.is_file()}

    def want(i):
        return only is None or str(i) in only

    # ---------------------------------------------------------------- 1 & 2 device check in both languages
    if want(1) or want(2):
        for sid, lang, needle in ((1, "ar", "جهازك"), (2, "en", "computer")):
            cp = subprocess.run([sys.executable, str(R.skill / "scripts" / "studio.py"), "--lang", lang, "doctor"],
                                capture_output=True, text=True, env=R.env)
            ok = cp.returncode == 0 and needle in cp.stdout
            R.record(sid, "Device check in %s for a beginner" % ("Arabic" if lang == "ar" else "English"),
                     "PASS" if ok else "FAIL", cp.stdout.strip().splitlines()[-1] if cp.stdout else cp.stderr[-300:])

    # ---------------------------------------------------------------- brands
    def mk_brand(file, logo=None):
        res, _ = R.st("brand", "new", "--from-file", str(ROOT / "examples" / "brands" / file))
        slug = res["slug"]
        if logo:
            R.st("brand", "logo", slug, str(fx / logo))
        return slug

    cafe = mk_brand("arabic-cafe.json", "logo_arabic.png")
    sami = mk_brand("english-creator.json", "logo_english.png")
    sana = mk_brand("bilingual-studio.json", "logo_bilingual.png")
    bakery = mk_brand("no-logo-bakery.json")

    # ---------------------------------------------------------------- 3 Arabic business with Arabic logo
    if want(3):
        res, _ = R.st("project", "new", "--title", "cafe-opening", "--brand", cafe, "--format", "vertical", "--language", "ar")
        slug = res["slug"]
        R.st("project", "add", slug, fx / "clip_landscape.mp4", fx / "photo_portrait.jpg", fx / "music_pad.wav")
        (R.project_dir(slug) / "captions" / "ar.srt").write_text(
            "1\n00:00:00,300 --> 00:00:03,000\nأهلًا بكم في مقهى الريحان\n\n"
            "2\n00:00:03,100 --> 00:00:06,400\nقهوة مختصة تُحمَّص كل يوم، بأسعار تبدأ من ١٥ ريالًا!\n\n"
            "3\n00:00:06,500 --> 00:00:09,500\nتابعونا على @alrayhan.cafe\n", encoding="utf-8")
        R.write_plan(slug, {
            "title": "افتتاح الفرع", "brand": cafe, "format": "vertical", "language": "ar",
            "transition": {"type": "slide", "duration": 0.4},
            "scenes": [
                {"kind": "video", "src": "media/clip_landscape.mp4", "start": 0.5, "end": 5.0,
                 "texts": [{"text": "افتتاح الفرع الجديد", "role": "headline", "position": "upper", "animation": "words"}]},
                {"kind": "image", "src": "media/photo_portrait.jpg", "duration": 3.5, "motion": "zoom_in",
                 "texts": [{"text": "خصم ٢٠٪ طوال الأسبوع الأول", "role": "headline", "animation": "slide_up"}]},
                {"kind": "title", "duration": 3.0,
                 "texts": [{"text": "الافتتاح: الخميس ٢٠ نوفمبر\nالساعة ٨ مساءً", "role": "headline", "animation": "zoom"}]}],
            "overlays": [{"kind": "lower_third", "title": "مقهى الريحان", "subtitle": "حي النخيل", "start": 1.0, "end": 4.5}],
            "captions": {"src": "captions/ar.srt", "burn": True},
            "audio": {"music": {"src": "media/music_pad.wav", "volume": 0.2}, "duck": True, "sfx": True}})
        res, code = R.render(slug)
        overall, checks, _ = R.qc_summary(res)
        friendly = list(R.project_dir(slug).glob("*_vertical.mp4"))
        checks["friendly_final_copy"] = "ok" if friendly else "fail"
        if not friendly:
            overall = "FAIL"
        R.record(3, "Arabic business with Arabic logo (vertical reel, captions, lower third, music)",
                 "PASS" if code == 0 and overall in ("PASS", "WARN") else "FAIL",
                 {"qc": overall, "checks": checks, "seconds": res.get("seconds_taken")}, R.collect(res, "03_arabic_business"))

    # ---------------------------------------------------------------- 4 English creator brand (+ transcription EN)
    if want(4):
        res, _ = R.st("project", "new", "--title", "focus-tips", "--brand", sami, "--format", "vertical", "--language", "en")
        slug = res["slug"]
        R.st("project", "add", slug, fx / "speech_en.mp4", fx / "clip_vertical_silent.mp4")
        R.write_plan(slug, {
            "title": "Focus tips", "brand": sami, "format": "vertical", "language": "en",
            "scenes": [{"kind": "video", "src": "media/speech_en.mp4",
                        "texts": [{"text": "3 simple tips to stay focused", "role": "headline", "position": "upper",
                                   "animation": "words", "end": 3.0}]},
                       {"kind": "video", "src": "media/clip_vertical_silent.mp4", "start": 0, "end": 3,
                        "texts": [{"text": "Try it today!", "role": "headline", "animation": "zoom"}]}],
            "branding": {"cta": {"en": "Follow for more tips"}}})
        res, code = R.render(slug, preview=True)
        tr, tcode = R.st("transcribe", slug, "--language", "en", check=False)
        ok_tr = tcode == 0 and tr.get("segments", 0) > 0
        draft = Path(R.project_dir(slug) / "captions" / "transcript-draft.srt")
        text = draft.read_text(encoding="utf-8") if draft.exists() else ""
        if ok_tr:
            shutil.copy2(draft, R.project_dir(slug) / "captions" / "en.srt")  # simulated user approval
            plan = json.loads((R.project_dir(slug) / "plan.json").read_text(encoding="utf-8"))
            plan["captions"] = {"src": "captions/en.srt", "burn": True, "style": "outline"}
            R.write_plan(slug, plan)
        res, code = R.render(slug)
        overall, checks, _ = R.qc_summary(res)
        R.record(4, "English creator brand (talking clip, transcription, burned English captions)",
                 "PASS" if code == 0 and ok_tr and overall in ("PASS", "WARN") else "FAIL",
                 {"qc": overall, "checks": checks, "transcript": text.strip()[:400], "flagged": tr.get("flagged")},
                 R.collect(res, "04_english_creator"))

    # ---------------------------------------------------------------- 5 bilingual brand
    if want(5):
        res, _ = R.st("project", "new", "--title", "sana-post", "--brand", sana, "--format", "square", "--language", "bilingual")
        slug = res["slug"]
        R.st("project", "add", slug, fx / "photo_landscape.jpg", fx / "clip_landscape.mp4")
        R.write_plan(slug, {
            "title": "Dar Al-Sana", "brand": sana, "format": "square", "language": "bilingual",
            "scenes": [
                {"kind": "image", "src": "media/photo_landscape.jpg", "duration": 4, "motion": "pan_right",
                 "texts": [{"text": "تصميم يحكي قصتك", "role": "headline", "position": "upper", "animation": "slide_up"},
                           {"text": "Design that tells your story", "role": "subtitle", "position": "lower",
                            "animation": "fade", "start": 0.8}]},
                {"kind": "video", "src": "media/clip_landscape.mp4", "start": 1, "end": 5,
                 "texts": [{"text": "هوية بصرية · Branding · موشن جرافيك", "role": "subtitle", "animation": "slide_side"}]}],
            "overlays": [{"kind": "lower_third", "title": "دار السَّنا Dar Al-Sana Studio", "subtitle": "www.daralsana.example",
                          "start": 0.5, "end": 3.5}]})
        res, code = R.render(slug)
        overall, checks, _ = R.qc_summary(res)
        R.record(5, "Bilingual Arabic-English brand (square post, mixed-direction texts)",
                 "PASS" if code == 0 and overall in ("PASS", "WARN") else "FAIL",
                 {"qc": overall, "checks": checks}, R.collect(res, "05_bilingual_brand"))

    # ---------------------------------------------------------------- 6 brand without logo
    if want(6):
        res, _ = R.st("project", "new", "--title", "bakery", "--brand", bakery, "--format", "portrait", "--language", "ar")
        slug = res["slug"]
        R.st("project", "add", slug, fx / "photo_portrait.jpg")
        R.write_plan(slug, {
            "title": "مخبز", "brand": bakery, "format": "portrait", "language": "ar",
            "scenes": [{"kind": "image", "src": "media/photo_portrait.jpg", "duration": 4, "motion": "zoom_out",
                        "texts": [{"text": "خبز طازج كل صباح من الساعة 6", "role": "headline", "animation": "fade"}]}]})
        res, code = R.render(slug)
        overall, checks, _ = R.qc_summary(res)
        R.record(6, "Brand without a logo (typographic wordmark intro/outro, Arabic-Indic numerals)",
                 "PASS" if code == 0 and overall in ("PASS", "WARN") else "FAIL",
                 {"qc": overall, "checks": checks}, R.collect(res, "06_no_logo"))

    # ---------------------------------------------------------------- 7 user without brand
    if want(7):
        res, _ = R.st("project", "new", "--title", "alula-trip", "--brand", "", "--format", "landscape", "--language", "ar")
        slug = res["slug"]
        R.st("project", "add", slug, fx / "photo_landscape.jpg", fx / "photo_portrait.jpg")
        R.write_plan(slug, {
            "title": "رحلة", "brand": None, "format": "landscape", "language": "ar",
            "scenes": [{"kind": "title", "duration": 2.5, "texts": [{"text": "رحلة العُلا ٢٠٢٦", "role": "title", "animation": "zoom"}]},
                       {"kind": "image", "src": "media/photo_landscape.jpg", "duration": 3, "motion": "zoom_in"},
                       {"kind": "image", "src": "media/photo_portrait.jpg", "duration": 3, "motion": "none", "framing": "fit_blur",
                        "texts": [{"text": "ذكريات لا تُنسى", "role": "subtitle", "position": "lower", "animation": "fade"}]}]})
        res, code = R.render(slug)
        overall, checks, rep = R.qc_summary(res)
        meta = json.loads((Path(res["version_dir"]) / "render.json").read_text(encoding="utf-8"))
        neutral = meta["brand"] in (None, "") and meta["scene_roles"][0] != "intro" and meta["scene_roles"][-1] != "outro"
        R.record(7, "User without a configured brand (neutral style, no intro/outro, landscape)",
                 "PASS" if code == 0 and neutral and overall in ("PASS", "WARN") else "FAIL",
                 {"qc": overall, "checks": checks, "roles": meta["scene_roles"]}, R.collect(res, "07_no_brand"))

    # ---------------------------------------------------------------- 8 Arabic social video with Arabic transcription
    if want(8):
        res, _ = R.st("project", "new", "--title", "cafe-voice", "--brand", cafe, "--format", "vertical", "--language", "ar")
        slug = res["slug"]
        R.st("project", "add", slug, fx / "speech_ar.mp4")
        R.write_plan(slug, {"title": "صوت", "brand": cafe, "format": "vertical", "language": "ar",
                            "scenes": [{"kind": "video", "src": "media/speech_ar.mp4",
                                        "texts": [{"text": "قهوتك المفضلة بانتظارك", "role": "headline", "position": "upper",
                                                   "animation": "slide_up", "end": 3.5}]}],
                            "branding": {"intro": False}})
        R.render(slug, preview=True)
        tr, tcode = R.st("transcribe", slug, "--language", "ar", check=False)
        draft = R.project_dir(slug) / "captions" / "transcript-draft.srt"
        text = draft.read_text(encoding="utf-8") if draft.exists() else ""
        ok_tr = tcode == 0 and "الريحان" in text
        if draft.exists():
            shutil.copy2(draft, R.project_dir(slug) / "captions" / "ar.srt")  # simulated approval after review
            plan = json.loads((R.project_dir(slug) / "plan.json").read_text(encoding="utf-8"))
            plan["captions"] = {"src": "captions/ar.srt", "burn": True}
            R.write_plan(slug, plan)
        res, code = R.render(slug)
        overall, checks, _ = R.qc_summary(res)
        R.record(8, "Arabic social video (Arabic speech → local transcription → burned Arabic captions)",
                 "PASS" if code == 0 and ok_tr and overall in ("PASS", "WARN") else "FAIL",
                 {"qc": overall, "checks": checks, "transcript": text.strip()[:500], "flagged": tr.get("flagged")},
                 R.collect(res, "08_arabic_social"))

    # ---------------------------------------------------------------- 9 English social video (+ 2 extra formats)
    if want(9):
        res, _ = R.st("project", "new", "--title", "loop-bottle", "--brand", sami, "--format", "vertical", "--language", "en")
        slug = res["slug"]
        R.st("project", "add", slug, fx / "photo_landscape.jpg", fx / "photo_portrait.jpg", fx / "music_pad.wav")
        R.write_plan(slug, {
            "title": "Loop launch", "brand": sami, "format": "vertical", "language": "en",
            "transition": {"type": "slide", "duration": 0.3},
            "scenes": [
                {"kind": "title", "duration": 2.0, "texts": [{"text": "Meet Loop.", "role": "title", "animation": "zoom"}]},
                {"kind": "image", "src": "media/photo_portrait.jpg", "duration": 2.5, "motion": "zoom_in",
                 "texts": [{"text": "Keeps drinks cold for 24h", "role": "headline", "animation": "words"}]},
                {"kind": "image", "src": "media/photo_landscape.jpg", "duration": 2.5, "motion": "pan_left",
                 "texts": [{"text": "Leak-proof. Recycled steel.", "role": "headline", "animation": "slide_up"}]},
                {"kind": "title", "duration": 2.5, "texts": [{"text": "$29", "role": "title", "animation": "zoom"},
                                                             {"text": "Order now — link in bio", "role": "cta", "position": "lower",
                                                              "animation": "slide_up", "start": 0.6}]}],
            "audio": {"music": {"src": "media/music_pad.wav", "volume": 0.35}, "sfx": True}})
        ok_all = True
        details = {}
        ev = []
        for fmt in ("vertical", "square", "landscape"):
            res, code = R.render(slug, fmt=fmt)
            overall, checks, _ = R.qc_summary(res)
            details[fmt] = {"qc": overall, "checks": checks}
            ok_all &= code == 0 and overall in ("PASS", "WARN")
            ev += R.collect(res, "09_english_social_%s" % fmt)
        R.record(9, "English social video (product ad, music, exported vertical + square + landscape)",
                 "PASS" if ok_all else "FAIL", details, ev)

    # ---------------------------------------------------------------- 10 mixed-language video with Arabic subtitles
    if want(10):
        res, _ = R.st("project", "new", "--title", "clinic-interview", "--brand", sana, "--format", "vertical", "--language", "ar")
        slug = res["slug"]
        R.st("project", "add", slug, fx / "speech_en.mp4")
        # Arabic subtitles = faithful translation of the English speech (as Claude would write them, user-approved)
        (R.project_dir(slug) / "captions" / "ar.srt").write_text(
            "1\n00:00:00,200 --> 00:00:02,600\nمرحبًا بالجميع، أهلًا بعودتكم إلى القناة.\n\n"
            "2\n00:00:02,700 --> 00:00:06,500\nسأعرض عليكم اليوم 3 نصائح بسيطة\nلتبقوا مركّزين.\n", encoding="utf-8")
        R.write_plan(slug, {"title": "مقابلة", "brand": sana, "format": "vertical", "language": "ar",
                            "scenes": [{"kind": "video", "src": "media/speech_en.mp4",
                                        "texts": [{"text": "Interview | مقابلة", "role": "subtitle", "position": "upper",
                                                   "animation": "fade"}]}],
                            "overlays": [{"kind": "lower_third", "title": "Dr. Lina Haddad", "subtitle": "طبيبة أسنان",
                                          "start": 0.3, "end": 3.0}],
                            "captions": {"src": "captions/ar.srt", "burn": True, "style": "box"},
                            "branding": {"intro": False}})
        res, code = R.render(slug)
        overall, checks, _ = R.qc_summary(res)
        vtt = (Path(res["version_dir"]) / "captions.vtt").exists()
        R.record(10, "Mixed-language video (English speech, Arabic subtitles burned + .srt/.vtt sidecars)",
                 "PASS" if code == 0 and vtt and overall in ("PASS", "WARN") else "FAIL",
                 {"qc": overall, "checks": checks, "sidecars": vtt}, R.collect(res, "10_mixed_arabic_subs"))

    # ---------------------------------------------------------------- X1 brand isolation negative test
    if want("x1"):
        res, _ = R.st("project", "new", "--title", "leak-test", "--brand", sami, "--format", "square", "--language", "en")
        slug = res["slug"]
        R.write_plan(slug, {"title": "leak", "brand": sami, "format": "square", "language": "en",
                            "scenes": [{"kind": "title", "duration": 2,
                                        "texts": [{"text": "Visit @alrayhan.cafe", "role": "headline"}]}],
                            "branding": {"intro": False, "outro": False}})
        res, code = R.render(slug, preview=True)
        overall, checks, _ = R.qc_summary(res)
        caught = checks.get("brand_isolation") == "fail" and code == 3
        R.record("X1", "Brand-isolation check catches another brand's handle (deliberate leak)",
                 "PASS" if caught else "FAIL", {"qc": overall, "brand_isolation": checks.get("brand_isolation")})

    # ---------------------------------------------------------------- X2 originals untouched
    after = {p.name: sha(p) for p in fx.iterdir() if p.is_file()}
    changed = [k for k in originals if originals[k] != after.get(k)]
    R.record("X2", "Original media files unchanged after all renders", "PASS" if not changed else "FAIL",
             "changed: %s" % changed if changed else "all %d fixture files identical (SHA-256)" % len(after))

    # ---------------------------------------------------------------- X3 cross-recipient leakage across all outputs
    leaks = []
    names = {}
    for b in (cafe, sami, sana, bakery):
        j = json.loads((R.ws / "brands" / b / "brand.json").read_text(encoding="utf-8"))
        names[b] = [n for n in [j["name"].get("ar"), j["name"].get("en")] + list(j.get("handles", {}).values()) if n and len(n) > 3]
    for pj in (R.ws / "projects").glob("*/output/v*/render.json"):
        meta = json.loads(pj.read_text(encoding="utf-8"))
        if pj.parent.parent.parent.name == "leak-test":
            continue
        html = "".join(Path(c["png"]).with_suffix(".html").read_text(encoding="utf-8", errors="ignore")
                       for c in meta["cards"] if Path(c["png"]).with_suffix(".html").exists())
        for b, ns in names.items():
            if b == meta["brand"]:
                continue
            for n in ns:
                if n in html and n not in names.get(meta["brand"] or "", []):
                    leaks.append("%s contains %s" % (pj.parent.parent.parent.name, n))
        if "URM ENROLL" in html:
            leaks.append("%s contains URM ENROLL" % pj.parent.parent.parent.name)
    R.record("X3", "No recipient branding leaks into another recipient's project (all renders scanned)",
             "PASS" if not leaks else "FAIL", "; ".join(leaks) or "no foreign names, handles or URM ENROLL text found")

    total = round(time.time() - t0, 1)
    (R.out / "results.json").write_text(json.dumps({"seconds": total, "results": R.results}, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
    lines = ["# Acceptance results", "", "Total time: %ss" % total, "", "| # | Scenario | Result |", "|---|---|---|"]
    for r in R.results:
        lines.append("| %s | %s | %s |" % (r["id"], r["name"], r["status"]))
    (R.out / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    fails = [r for r in R.results if r["status"] != "PASS"]
    print("\n%d scenarios, %d failed, %ss" % (len(R.results), len(fails), total))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
