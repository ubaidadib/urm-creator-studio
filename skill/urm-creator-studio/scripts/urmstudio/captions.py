"""Subtitles: read/write SRT & VTT, readability checks, and local transcription.

Transcription never invents words: segments the recogniser is unsure about
are flagged for human review, and nothing is burned into a video until the
user has approved the text.
"""
import glob
import json
import os
import re
import tempfile
from pathlib import Path

from .common import StudioError, has_arabic, run, studio_home, which
from .media import ffmpeg_bin

RLM = "‏"
TS = re.compile(r"(\d+):(\d{2}):(\d{2})[,.](\d{1,3})")


def _t(s):
    m = TS.search(s)
    if not m:
        h, mi, se = 0, 0, 0
        parts = s.strip().split(":")
        if len(parts) == 2:  # VTT mm:ss.mmm
            mi = int(parts[0])
            se = float(parts[1])
            return mi * 60 + se
        raise ValueError("bad time %s" % s)
    h, mi, se, ms = m.groups()
    return int(h) * 3600 + int(mi) * 60 + int(se) + int(ms.ljust(3, "0")) / 1000.0


def parse(path):
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace").replace("\r\n", "\n")
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l for l in block.split("\n") if l.strip() != ""]
        if not lines or lines[0].strip().upper().startswith("WEBVTT"):
            continue
        i = next((k for k, l in enumerate(lines) if "-->" in l), None)
        if i is None:
            continue
        a, b = lines[i].split("-->")
        body = "\n".join(lines[i + 1:]).replace(RLM, "").replace("‎", "").strip()
        body = re.sub(r"<[^>]+>", "", body)
        if body:
            cues.append({"start": _t(a), "end": _t(b.split()[0] if b.split() else b), "text": body})
    cues.sort(key=lambda c: c["start"])
    return cues


def _fmt(t, sep=","):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        s, ms = s + 1, 0
    return "%02d:%02d:%02d%s%03d" % (h, m, s, sep, ms)


def _rtl_safe(text):
    # Right-to-left mark at the start/end of Arabic lines keeps trailing
    # punctuation on the correct side in players that guess direction poorly.
    return "\n".join((RLM + l + RLM) if has_arabic(l) else l for l in text.split("\n"))


def write_srt(cues, path, rtl_marks=True):
    out = []
    for i, c in enumerate(cues, 1):
        body = _rtl_safe(c["text"]) if rtl_marks else c["text"]
        out.append("%d\n%s --> %s\n%s\n" % (i, _fmt(c["start"]), _fmt(c["end"]), body))
    Path(path).write_text("\n".join(out), encoding="utf-8")
    return path


def write_vtt(cues, path):
    out = ["WEBVTT", ""]
    for c in cues:
        out.append("%s --> %s" % (_fmt(c["start"], "."), _fmt(c["end"], ".")))
        out.append(_rtl_safe(c["text"]))
        out.append("")
    Path(path).write_text("\n".join(out), encoding="utf-8")
    return path


def shift(cues, offset):
    return [dict(c, start=c["start"] + offset, end=c["end"] + offset) for c in cues]


def check(cues, max_cps=17.0, max_line=42, max_lines=2, min_dur=0.8):
    """Readability problems as a list of dicts (index, problem, detail)."""
    probs = []
    for i, c in enumerate(cues):
        d = c["end"] - c["start"]
        txt = c["text"]
        chars = len(re.sub(r"\s+", " ", txt.replace("\n", " ")).strip())
        if d <= 0:
            probs.append({"i": i + 1, "problem": "zero_length", "detail": "end before start"})
            continue
        if d < min_dur:
            probs.append({"i": i + 1, "problem": "too_short", "detail": "%.2fs" % d})
        if chars / d > max_cps:
            probs.append({"i": i + 1, "problem": "too_fast", "detail": "%.0f chars/s" % (chars / d)})
        lines = txt.split("\n")
        if len(lines) > max_lines:
            probs.append({"i": i + 1, "problem": "too_many_lines", "detail": str(len(lines))})
        if any(len(l) > max_line for l in lines) and len(lines) >= max_lines:
            probs.append({"i": i + 1, "problem": "line_too_long", "detail": str(max(len(l) for l in lines))})
        if i and c["start"] < cues[i - 1]["end"] - 0.01:
            probs.append({"i": i + 1, "problem": "overlap", "detail": "overlaps previous cue"})
        if "[?]" in txt or "[؟]" in txt:
            probs.append({"i": i + 1, "problem": "unclear_speech", "detail": "needs human review"})
    return probs


def reflow(cues, max_line=42):
    """Split long cues into ~2-line chunks, distributing time by characters."""
    res = []
    for c in cues:
        words = c["text"].replace("\n", " ").split()
        if len(" ".join(words)) <= max_line * 2:
            res.append(dict(c, text=_two_lines(words, max_line)))
            continue
        chunks, cur = [], []
        for w in words:
            if len(" ".join(cur + [w])) > max_line * 2 - 4 and cur:
                # prefer to break after the last sentence/clause mark in the chunk
                cut = max((k for k, x in enumerate(cur) if x[-1:] in ".!?،,؟;؛:"), default=-1)
                if 2 <= cut + 1 < len(cur):
                    chunks.append(cur[:cut + 1])
                    cur = cur[cut + 1:]
                else:
                    chunks.append(cur)
                    cur = []
            cur.append(w)
        if cur:
            chunks.append(cur)
        total = sum(len(" ".join(x)) for x in chunks)
        t = c["start"]
        dur = c["end"] - c["start"]
        for ch in chunks:
            d = dur * len(" ".join(ch)) / max(total, 1)
            res.append({"start": t, "end": t + d, "text": _two_lines(ch, max_line)})
            t += d
    return res


def _two_lines(words, max_line):
    s = " ".join(words)
    if len(s) <= max_line:
        return s
    best, best_diff = s, 10 ** 9
    for k in range(1, len(words)):
        a, b = " ".join(words[:k]), " ".join(words[k:])
        diff = abs(len(a) - len(b)) - (12 if words[k - 1][-1:] in ".!?،,؟;؛:" else 0)
        if len(a) <= max_line + 6 and diff < best_diff:
            best, best_diff = a + "\n" + b, diff
    return best


# --------------------------------------------------------------------------
# Transcription (whisper.cpp, fully local)
# --------------------------------------------------------------------------

def find_whisper():
    exe = which("whisper-cli") or which("whisper-cpp") or which("main.exe")
    model = os.environ.get("URM_WHISPER_MODEL")
    if not model or not Path(model).exists():
        cands = []
        for pat in ("~/models/ggml-*.bin", "~/.cache/whisper/ggml-*.bin", "~/whisper.cpp/models/ggml-*.bin",
                    "/opt/homebrew/share/whisper-cpp/ggml-*.bin", "/usr/local/share/whisper-cpp/ggml-*.bin",
                    str(studio_home() / "models" / "ggml-*.bin")):
            cands += glob.glob(os.path.expanduser(pat))
        # prefer bigger multilingual models (better Arabic); skip English-only ".en" models
        cands = [c for c in cands if ".en." not in c and "-en." not in c]
        rank = ["large-v3-turbo", "large-v3", "large", "medium", "small", "base", "tiny"]
        cands.sort(key=lambda c: next((i for i, r in enumerate(rank) if r in c), 99))
        model = cands[0] if cands else None
    return exe, model


def transcribe(media, out_srt, language="auto", min_conf=0.45, min_token=0.30, keep_json=None):
    exe, model = find_whisper()
    if not exe:
        raise StudioError("missing_tool", "whisper-cli (whisper.cpp)")
    if not model:
        raise StudioError("missing_tool", "speech model file (ggml-*.bin)")
    out_srt = Path(out_srt)
    with tempfile.TemporaryDirectory(prefix="urm-asr-") as td:
        wav = Path(td) / "audio.wav"
        run([ffmpeg_bin(), "-y", "-v", "error", "-i", str(media), "-vn", "-ac", "1", "-ar", "16000",
             "-c:a", "pcm_s16le", str(wav)])
        base = Path(td) / "out"
        args = [exe, "-m", model, "-f", str(wav), "-l", language, "-ojf", "-of", str(base)]
        cp = run(args, check=False, timeout=60 * 60)
        jf = Path(str(base) + ".json")
        if not jf.exists():
            raise StudioError("command_failed", "transcription failed: " +
                              cp.stderr.decode("utf-8", "replace")[-800:])
        data = json.loads(jf.read_text(encoding="utf-8", errors="replace"))
        if keep_json:
            Path(keep_json).write_text(jf.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    cues, flagged = [], 0
    detected = (data.get("result") or {}).get("language")
    for seg in data.get("transcription", []):
        txt = (seg.get("text") or "").strip()
        if not txt:
            continue
        off = seg.get("offsets") or {}
        start, end = off.get("from", 0) / 1000.0, off.get("to", 0) / 1000.0
        toks = [t for t in seg.get("tokens", []) if not str(t.get("text", "")).startswith("[_")]
        probs = [float(t.get("p", 1)) for t in toks if t.get("text", "").strip()]
        conf = sum(probs) / len(probs) if probs else 0.0
        low = min(probs) if probs else 0.0
        mark = ""
        # flag the whole segment when the average OR any single word-piece is uncertain
        if conf < min_conf or low < min_token or re.fullmatch(r"[\W_]*", txt):
            flagged += 1
            mark = " [؟]" if has_arabic(txt) else " [?]"
        cues.append({"start": start, "end": end, "text": txt + mark, "confidence": round(conf, 2),
                     "lowest": round(low, 2)})
    cues = reflow(cues)
    write_srt(cues, out_srt, rtl_marks=False)
    meta = out_srt.with_suffix(".review.json")
    meta.write_text(json.dumps({"status": "DRAFT - needs human review", "language": detected,
                                "model": Path(model).name, "segments": len(cues),
                                "flagged_unclear": flagged,
                                "note": "Speech recognition makes mistakes even when confident. Review every line.",
                                "confidence": [{"i": i + 1, "avg": c.get("confidence"), "lowest": c.get("lowest")}
                                               for i, c in enumerate(cues)]}, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return {"srt": str(out_srt), "segments": len(cues), "flagged": flagged, "language": detected}
