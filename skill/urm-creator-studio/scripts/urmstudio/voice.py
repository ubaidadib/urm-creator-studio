"""Optional synthetic narration using the operating system's own voices.

Only runs with approved=True: the skill must ask the user first and must
label the narration as synthetic. It never imitates a real person's voice.
"""
import platform
import tempfile
from pathlib import Path

from .common import StudioError, run, which
from .media import ffmpeg_bin

DEFAULT_VOICES = {"ar": "Majed", "en": "Samantha"}


def list_voices(lang="ar"):
    if platform.system() != "Darwin" or not which("say"):
        return []
    txt = run(["say", "-v", "?"], check=False).stdout.decode("utf-8", "replace")
    res = []
    for line in txt.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            loc = next((p for p in parts if "_" in p and len(p) <= 7), "")
            if loc.startswith(lang + "_") or (lang == "en" and loc.startswith("en_")):
                res.append(line.split("  ")[0].strip())
    return res


def synthesize(text, out_path, lang="ar", voice=None, rate=None, approved=False):
    if not approved:
        raise StudioError("bad_plan", "synthetic narration needs the user's explicit approval")
    if platform.system() != "Darwin" or not which("say"):
        raise StudioError("missing_tool", "system voice (macOS 'say')")
    voice = voice or DEFAULT_VOICES.get(lang, "Samantha")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="urm-vo-") as td:
        tf = Path(td) / "t.txt"
        tf.write_text(text, encoding="utf-8")
        aiff = Path(td) / "vo.aiff"
        args = ["say", "-v", voice, "-o", str(aiff), "-f", str(tf)]
        if rate:
            args += ["-r", str(rate)]
        run(args)
        run([ffmpeg_bin(), "-y", "-v", "error", "-i", str(aiff), "-ar", "48000", "-ac", "2", str(out_path)])
    return out_path
