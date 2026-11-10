"""Media inspection with ffprobe/ffmpeg (read-only on source files)."""
import json
import re
from pathlib import Path

from .common import StudioError, run, which

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".3gp", ".mts"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp", ".tif", ".tiff"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".opus"}


def ffmpeg_bin():
    b = which("ffmpeg")
    if not b:
        raise StudioError("missing_tool", "ffmpeg")
    return b


def ffprobe_bin():
    b = which("ffprobe")
    if not b:
        raise StudioError("missing_tool", "ffprobe")
    return b


def kind_of(path):
    ext = Path(path).suffix.lower()
    if ext in VIDEO_EXT:
        return "video"
    if ext in IMAGE_EXT:
        return "image"
    if ext in AUDIO_EXT:
        return "audio"
    return "unknown"


def probe(path):
    path = Path(path)
    if not path.exists():
        raise StudioError("not_found", str(path))
    cp = run([ffprobe_bin(), "-v", "error", "-print_format", "json", "-show_format",
              "-show_streams", str(path)])
    data = json.loads(cp.stdout.decode("utf-8", "replace") or "{}")
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"
              and not (s.get("disposition") or {}).get("attached_pic")), None)
    a = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    fmt = data.get("format", {})
    info = {"path": str(path), "kind": kind_of(path), "size_mb": round(int(fmt.get("size", 0)) / 1e6, 2),
            "duration": float(fmt.get("duration") or 0), "has_video": bool(v), "has_audio": bool(a)}
    if v:
        w, h = int(v.get("width", 0)), int(v.get("height", 0))
        rot = 0
        for sd in v.get("side_data_list", []) or []:
            if "rotation" in sd:
                rot = int(float(sd["rotation"]))
        if "rotate" in (v.get("tags") or {}):
            rot = int(v["tags"]["rotate"])
        if abs(rot) % 180 == 90:
            w, h = h, w
        fr = v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1"
        try:
            n, d = fr.split("/")
            fps = round(float(n) / float(d), 3) if float(d) else 0
        except Exception:
            fps = 0
        trc = v.get("color_transfer", "")
        info.update({
            "width": w, "height": h, "fps": fps, "rotation": rot, "vcodec": v.get("codec_name"),
            "pix_fmt": v.get("pix_fmt"), "orientation": orientation(w, h),
            "hdr": trc in ("arib-std-b67", "smpte2084"), "color_transfer": trc,
            "variable_fps": (v.get("r_frame_rate") != v.get("avg_frame_rate")),
        })
        if info["kind"] == "image":
            info["duration"] = 0
    if a:
        info.update({"acodec": a.get("codec_name"), "sample_rate": int(a.get("sample_rate", 0) or 0),
                     "channels": a.get("channels")})
    return info


def orientation(w, h):
    if not w or not h:
        return "unknown"
    r = w / h
    if r < 0.8:
        return "vertical"
    if r > 1.25:
        return "landscape"
    return "square"


def loudness(path, start=None, dur=None):
    """Integrated loudness (LUFS), true peak, and silence ratio of the audio."""
    args = [ffmpeg_bin(), "-hide_banner", "-nostats"]
    if start is not None:
        args += ["-ss", str(start)]
    if dur is not None:
        args += ["-t", str(dur)]
    args += ["-i", str(path), "-vn", "-af", "ebur128=peak=true,silencedetect=n=-45dB:d=0.6",
             "-f", "null", "-"]
    cp = run(args, check=False)
    err = cp.stderr.decode("utf-8", "replace")
    res = {}
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    if m:
        res["lufs"] = float(m[-1])
    m = re.findall(r"Peak:\s+(-?[\d.inf]+) dBFS", err)
    if m:
        try:
            res["true_peak"] = float(m[-1])
        except ValueError:
            pass
    sil = sum(float(x) for x in re.findall(r"silence_duration: ([\d.]+)", err))
    res["silence_seconds"] = round(sil, 2)
    return res


def scene_changes(path, threshold=0.32, limit=400):
    cp = run([ffmpeg_bin(), "-hide_banner", "-nostats", "-i", str(path), "-an",
              "-vf", "select='gt(scene,%s)',showinfo" % threshold, "-f", "null", "-"], check=False)
    err = cp.stderr.decode("utf-8", "replace")
    ts = [round(float(x), 2) for x in re.findall(r"pts_time:([\d.]+)", err)]
    return ts[:limit]


def contact_sheet(path, out_png, cols=4, rows=3, width=1600):
    """One image with evenly spaced frames, for Claude to look at the footage."""
    info = probe(path)
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    n = cols * rows
    if info["kind"] == "image":
        run([ffmpeg_bin(), "-y", "-v", "error", "-i", str(path), "-vf",
             "scale=%d:-2" % width, "-frames:v", "1", str(out_png)])
        return out_png
    dur = max(info["duration"], 0.1)
    step = dur / n
    tile_w = width // cols
    run([ffmpeg_bin(), "-y", "-v", "error", "-i", str(path), "-vf",
         "fps=1/%f,scale=%d:-2,tile=%dx%d:padding=4:color=black" % (max(step, 0.04), tile_w, cols, rows),
         "-frames:v", "1", str(out_png)])
    return out_png


def frame_at(path, t, out_png, width=None):
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    vf = ["scale=%d:-2" % width] if width else []
    args = [ffmpeg_bin(), "-y", "-v", "error", "-ss", "%.3f" % t, "-i", str(path)]
    if vf:
        args += ["-vf", ",".join(vf)]
    run(args + ["-frames:v", "1", str(out_png)])
    return out_png


def bbox_alpha(png):
    """Bounding box of visible (non-transparent) pixels: (x1, y1, x2, y2) or None."""
    cp = run([ffmpeg_bin(), "-hide_banner", "-i", str(png), "-vf", "alphaextract,bbox=min_val=24",
              "-f", "null", "-"], check=False)
    m = re.search(r"x1:(\d+) x2:(\d+) y1:(\d+) y2:(\d+)", cp.stderr.decode("utf-8", "replace"))
    if not m:
        return None
    x1, x2, y1, y2 = map(int, m.groups())
    if x2 < x1 or y2 < y1:
        return None
    return (x1, y1, x2, y2)


def analyze(path, deep=True):
    info = probe(path)
    if info["kind"] == "video" and deep:
        if info["has_audio"]:
            info["audio"] = loudness(path)
        info["cuts"] = scene_changes(path)
    elif info["kind"] == "audio" and deep:
        info["audio"] = loudness(path)
    return info
