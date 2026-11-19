"""Creative-led production: motion-design scenes and the original soundtrack.

Motion scenes are drawn frame by frame by motion/runtime.js inside a headless Chromium, which this module
drives over a private HTTP server on 127.0.0.1 (standard library only; nothing leaves the computer). Each
frame is piped straight into FFmpeg, so a scene becomes an ordinary video clip that the rest of the
pipeline (text cards, captions, joins, mix, QC) treats like footage.

Jobs run in parallel, one Chromium per scene, each with its own temporary profile.
"""
import atexit
import json
import os
import platform
import shutil
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from .common import FONTS_DIR, SKILL_DIR, StudioError, AR_DIGITS, has_arabic
from .media import ffmpeg_bin
from .textrender import BUNDLED_FONTS, find_browser

MOTION_DIR = SKILL_DIR / "motion"
TEMPLATES = {
    # name: (what it is for, required params)
    "kinetic_title": ("hook / headline with kinetic typography, orbit rings and floating shapes", ("title",)),
    "word_cloud": ("floating words in depth around a central line (languages, keywords, services)", ("words",)),
    "globe": ("rotating dotted globe with flight arcs (international, reach, travel)", ()),
    "features": ("2–4 benefit cards with drawn icons", ("items",)),
    "stats": ("1–3 counting numbers with progress rings (only true numbers)", ("items",)),
    "journey": ("a path drawing through steps or levels (process, progress, timeline)", ("steps",)),
    "contrast": ("from → to statement with a strike-through swap (problem → solution)", ("from", "to")),
    "quote": ("a real testimonial with stars", ("text",)),
    "showcase": ("an image (user, AI-generated or licensed stock) in a shaped frame with parallax and chips", ("image",)),
    "cta": ("closing call to action with brand mark, name and a button", ()),
    "logo_reveal": ("brand mark + name reveal (opening ident)", ()),
}
TRANSITIONS = ("swap", "slide", "panels", "circle", "none")
ICON_NAMES = ("globe book chat cap award users star check shield clock heart pin calendar phone spark chart plane "
              "bulb trophy briefcase home laptop gift mail play leaf rocket cart camera coffee music").split()

PAGE = ("<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;background:#000;overflow:hidden}"
        "</style></head><body><canvas id='c'></canvas><script src='/score.js'></script>"
        "<script src='/runtime.js'></script></body></html>")


def validate_motion_scene(i, sc, project_dir):
    errs = []
    t = sc.get("template")
    if t not in TEMPLATES:
        errs.append("scene %d: template must be one of %s" % (i, ", ".join(TEMPLATES)))
        return errs
    try:
        if float(sc.get("duration", 0)) < 1.0:
            errs.append("scene %d: motion scenes need a duration of at least 1 second" % i)
    except (TypeError, ValueError):
        errs.append("scene %d: duration must be a number" % i)
    p = sc.get("params") or {}
    for req in TEMPLATES[t][1]:
        if not p.get(req):
            errs.append("scene %d (%s): params.%s is required" % (i, t, req))
    if t == "showcase" and p.get("image"):
        src = Path(os.path.expanduser(str(p["image"])))
        if not src.is_absolute():
            src = Path(project_dir) / src
        if not src.exists():
            errs.append("scene %d: image not found: %s" % (i, p["image"]))
    for it in p.get("items", []) if t == "features" else []:
        if it.get("icon") and it["icon"] not in ICON_NAMES:
            errs.append("scene %d: unknown icon '%s' (use one of: %s)" % (i, it["icon"], ", ".join(ICON_NAMES)))
    for k in ("tin", "tout"):
        if sc.get(k) and sc[k] not in TRANSITIONS:
            errs.append("scene %d: %s must be one of %s" % (i, k, ", ".join(TRANSITIONS)))
    return errs


def _numerals(text, numerals):
    """Arabic-Indic digits in Arabic texts when the brand uses them (never inside Latin words)."""
    if numerals != "arabic_indic" or not isinstance(text, str) or not has_arabic(text):
        return text
    out = []
    for w in text.split(" "):
        bare = w.strip(".,%:/-+()")
        out.append(w.translate(AR_DIGITS) if (has_arabic(w) or (bare and bare.replace(".", "").isdigit())) else w)
    return " ".join(out)


def _apply_numerals(obj, numerals, rtl):
    if isinstance(obj, dict):
        return {k: (v if k in ("image", "icon", "value") else _apply_numerals(v, numerals, rtl)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_apply_numerals(v, numerals, rtl) for v in obj]
    return _numerals(obj, numerals)


class _Server:
    """Serves the runtime, fonts and whitelisted images; receives frames, layout and the soundtrack."""

    def __init__(self, spec, files):
        self.spec = json.dumps(spec, ensure_ascii=False).encode("utf-8")
        self.files = files            # url path -> local Path (whitelist; nothing else is served)
        self.sinks = {}               # scene index -> ffmpeg stdin
        self.counts = {}
        self.results = {}
        self.errors = {}
        self.done = {}
        self.locks = {}
        srv = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _ok(self, body=b"", ctype="text/plain"):
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                path = unquote(self.path.split("?")[0])
                if path == "/" or path == "/index.html":
                    return self._ok(PAGE.encode("utf-8"), "text/html; charset=utf-8")
                if path == "/spec.json":
                    return self._ok(srv.spec, "application/json")
                f = srv.files.get(path)
                if f is None or not Path(f).exists():
                    self.send_response(404)
                    self.end_headers()
                    return
                ctype = {".js": "text/javascript", ".ttf": "font/ttf", ".otf": "font/otf", ".png": "image/png",
                         ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
                         ".svg": "image/svg+xml"}.get(Path(f).suffix.lower(), "application/octet-stream")
                return self._ok(Path(f).read_bytes(), ctype)

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(n) if n else b""
                path = self.path.split("?")[0]
                parts = path.strip("/").split("/")
                try:
                    if parts[0] == "frame":
                        k, i = int(parts[1]), int(parts[2])
                        with srv.locks.setdefault(k, threading.Lock()):
                            if i != srv.counts.get(k, 0):
                                raise ValueError("frame %d of scene %d arrived out of order" % (i, k))
                            srv.sinks[k].write(body)
                            srv.counts[k] = i + 1
                    elif parts[0] == "layout":
                        srv.results["layout"] = json.loads(body.decode("utf-8"))
                    elif parts[0] == "score":
                        srv.results["score"] = body
                    elif parts[0] == "done":
                        srv.done[parts[1] if len(parts) > 1 else "?"] = True
                    elif parts[0] == "error":
                        job = parts[1] if len(parts) > 1 else "?"
                        srv.errors[job] = body.decode("utf-8", "replace")
                        srv.done[job] = True
                except Exception as e:  # report instead of hanging the browser
                    srv.errors["server"] = str(e)
                self._ok()

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


_LIVE = set()   # browsers currently drawing; killed at exit even if the render is interrupted


def _kill_live():
    for proc in list(_LIVE):
        try:
            proc.kill()
        except Exception:
            pass
    _LIVE.clear()


atexit.register(_kill_live)


def _chrome(browser, url, W, H, profile):
    cmd = [browser, "--headless=new", "--disable-gpu", "--mute-audio", "--hide-scrollbars", "--no-first-run",
           "--no-default-browser-check", "--disable-extensions", "--force-device-scale-factor=1",
           "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
           "--disable-backgrounding-occluded-windows", "--window-size=%d,%d" % (min(W, 1920), min(H, 1920)),
           "--user-data-dir=%s" % profile, url]
    if platform.system() == "Linux" and hasattr(os, "geteuid") and os.geteuid() == 0:
        cmd.insert(1, "--no-sandbox")
    proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _LIVE.add(proc)
    return proc


def _wait(srv, job, proc, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if srv.done.get(job) or srv.errors.get("server"):
            break
        if proc.poll() is not None and not srv.done.get(job):
            time.sleep(0.3)
            if not srv.done.get(job):
                break
        time.sleep(0.05)
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    _LIVE.discard(proc)
    if srv.errors.get(job) or srv.errors.get("server"):
        raise StudioError("command_failed", "motion renderer: %s" % (srv.errors.get(job) or srv.errors.get("server"))[:900])
    if not srv.done.get(job):
        raise StudioError("command_failed", "motion renderer did not finish %s within %d s" % (job, timeout))


def default_workers():
    """How many headless browsers draw scenes at once. Each one holds full-size RGBA frames (~0.3-0.5 GB at
    1080x1920), so machines with 8 GB of RAM or less use 2; URM_MOTION_WORKERS overrides (1-6)."""
    env = os.environ.get("URM_MOTION_WORKERS")
    if env and env.isdigit():
        return max(1, min(6, int(env)))
    cores = os.cpu_count() or 4
    try:
        mem = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError, AttributeError):
        mem = 8 << 30
    if mem <= (8 << 30) + (1 << 28):
        return max(1, min(2, cores // 2))
    return max(1, min(4, cores // 2))


class MotionStudio:
    """One render's motion work: build the spec once, then layout → frames (parallel) → soundtrack."""

    def __init__(self, *, W, H, fps, fmt, safe, rtl, numerals, look, identity, scenes, project_dir, seed=7,
                 browser=None, workers=None, log=None):
        self.browser = browser or find_browser()
        if not self.browser:
            raise StudioError("no_browser")
        self.W, self.H, self.fps = W, H, fps
        self.log = log if log is not None else []
        self.workers = workers or default_workers()
        files = {"/runtime.js": MOTION_DIR / "runtime.js", "/score.js": MOTION_DIR / "score.js"}
        fonts = []
        for fam, items in BUNDLED_FONTS.items():
            for rel, weight in items:
                p = FONTS_DIR / rel
                if p.exists():
                    url = "/fonts/" + rel
                    files[url] = p
                    fonts.append({"family": fam, "url": url, "weight": weight})
        for cf in (look.get("custom_fonts") or []):
            p = Path(cf.get("file", ""))
            if p.exists():
                url = "/cfonts/%d%s" % (len(files), p.suffix)
                files[url] = p
                fonts.append({"family": cf["family"], "url": url, "weight": cf.get("weight", "100 900")})
        images = []

        def img_url(path):
            p = Path(os.path.expanduser(str(path)))
            if not p.is_absolute():
                p = Path(project_dir) / p
            url = "/img/%d%s" % (len(images), p.suffix.lower())
            files[url] = p
            images.append(url)
            return url

        ident = dict(identity or {})
        if ident.get("logo_path"):
            ident["logo"] = img_url(ident.pop("logo_path"))
        sc_specs = []
        for i, sc in enumerate(scenes):
            params = _apply_numerals(dict(sc.get("params") or {}), numerals, rtl)
            if params.get("image"):
                params["image"] = img_url(sc["params"]["image"])
            sc_specs.append({"id": i, "template": sc["template"], "duration": float(sc["duration"]), "params": params,
                             "t0": float(sc.get("_t0", 0)), "tin": sc.get("tin", "swap"), "tout": sc.get("tout", "swap"),
                             "camera": sc.get("camera", ("push", "drift", "pull")[i % 3]), "seed": 101 + i * 37})
        self.spec = {"width": W, "height": H, "fps": fps, "format": fmt, "safe": list(safe), "rtl": rtl,
                     "numerals": numerals, "look": look, "identity": ident, "scenes": sc_specs, "fonts": fonts,
                     "images": images, "seed": seed, "alpha": False}
        self.files = files

    def scene_key(self, k, vcodec, inter_opts):
        """Content hash of everything that affects scene k's pixels (spec, runtime code, fonts list, encoder)."""
        import hashlib
        h = hashlib.sha1()
        common = {x: self.spec[x] for x in ("width", "height", "fps", "safe", "rtl", "numerals", "look", "identity",
                                             "seed")}
        h.update(json.dumps([common, self.spec["scenes"][k], vcodec, list(inter_opts)], sort_keys=True,
                            ensure_ascii=False).encode("utf-8"))
        h.update((MOTION_DIR / "runtime.js").read_bytes())
        for url in self.spec.get("images", []):
            f = Path(self.files[url])
            if f.exists():
                st = f.stat()
                h.update(("%s:%d:%d" % (f, st.st_size, int(st.st_mtime))).encode("utf-8"))
        return h.hexdigest()[:16]

    def _run_jobs(self, jobs, timeout_for):
        """jobs: list of job names; runs up to self.workers browsers at once."""
        srv = _Server(self.spec, self.files)
        tmp = tempfile.mkdtemp(prefix="urm-motion-")
        try:
            def one(job):
                prof = Path(tmp) / job.replace(":", "_")
                proc = _chrome(self.browser, "http://127.0.0.1:%d/?job=%s" % (srv.port, job), self.W, self.H, prof)
                _wait(srv, job, proc, timeout_for(job))
            if len(jobs) == 1:
                one(jobs[0])
            else:
                with ThreadPoolExecutor(max_workers=self.workers) as ex:
                    list(ex.map(one, jobs))
            return srv
        finally:
            srv.close()
            shutil.rmtree(tmp, ignore_errors=True)

    def layout(self):
        """Text boxes (for QC) and sound-design events of every motion scene, without drawing frames."""
        srv = self._run_jobs(["layout"], lambda j: 120)
        return srv.results.get("layout") or []

    def render_scenes(self, out_paths, vcodec, inter_opts, progress=print):
        """Render every motion scene to its own MP4 (video only)."""
        srv = _Server(self.spec, self.files)
        tmp = tempfile.mkdtemp(prefix="urm-motion-")
        encs = {}
        try:
            for k, out in out_paths.items():
                args = [ffmpeg_bin(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
                        "-s", "%dx%d" % (self.W, self.H), "-framerate", str(self.fps), "-i", "-",
                        "-vf", "format=yuv420p", "-c:v", vcodec, *inter_opts, "-r", str(self.fps), "-an", str(out)]
                self.log.append(" ".join(args))
                encs[k] = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                           stderr=open(Path(tmp) / ("enc%d.log" % k), "wb"))
                srv.sinks[k] = encs[k].stdin

            def one(k):
                n = int(round(self.spec["scenes"][k]["duration"] * self.fps))
                job = "scene:%d" % k
                t0 = time.time()
                proc = _chrome(self.browser, "http://127.0.0.1:%d/?job=%s" % (srv.port, job), self.W, self.H,
                               Path(tmp) / ("s%d" % k))
                _wait(srv, job, proc, 90 + n * 1.5)
                if srv.counts.get(k, 0) != n:
                    raise StudioError("command_failed", "motion scene %d: %d of %d frames" % (k, srv.counts.get(k, 0), n))
                progress("  ✓ motion scene %d (%s, %d frames, %.0fs)" % (k + 1, self.spec["scenes"][k]["template"], n,
                                                                       time.time() - t0))

            with ThreadPoolExecutor(max_workers=self.workers) as ex:
                list(ex.map(one, list(out_paths)))
        finally:
            for k, p in encs.items():
                try:
                    p.stdin.close()
                except Exception:
                    pass
            errs = []
            for k, p in encs.items():
                p.wait(timeout=600)
                if p.returncode != 0:
                    lf = Path(tmp) / ("enc%d.log" % k)
                    errs.append("scene %d: %s" % (k, lf.read_text("utf-8", "replace")[-400:] if lf.exists() else "?"))
            srv.close()
            shutil.rmtree(tmp, ignore_errors=True)
        if errs:
            raise StudioError("command_failed", "motion encode: " + " | ".join(errs))
        return out_paths


def render_score(score_spec, out_wav, browser=None, log=None):
    """Compose and render the original soundtrack to a WAV file."""
    ms = MotionStudio.__new__(MotionStudio)
    ms.browser = browser or find_browser()
    if not ms.browser:
        raise StudioError("no_browser")
    ms.W, ms.H, ms.fps, ms.workers = 320, 240, 30, 1
    ms.log = log if log is not None else []
    ms.files = {"/runtime.js": MOTION_DIR / "runtime.js", "/score.js": MOTION_DIR / "score.js"}
    ms.spec = {"width": 320, "height": 240, "fps": 30, "safe": [0, 0, 0, 0], "look": {"palette": {}}, "score": score_spec,
               "fonts": [], "scenes": []}
    srv = ms._run_jobs(["score"], lambda j: 60 + score_spec["duration"] * 4)
    data = srv.results.get("score")
    if not data or len(data) < 1000:
        raise StudioError("command_failed", "soundtrack synthesis produced no audio")
    Path(out_wav).write_bytes(data)
    return Path(out_wav)
