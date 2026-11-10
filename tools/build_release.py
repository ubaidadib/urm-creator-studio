#!/usr/bin/env python3
"""Build the shareable ZIP packages after a portability & privacy scan.

  python3 tools/build_release.py

dist/URM-Creator-Studio-v<version>.zip   recipient package (skill, docs, examples, installers, licences)
dist/URM-Creator-Studio-v<version>.zip.sha256  checksum
(The URM ENROLL launch kit is kept outside this repository.)

The scan fails the build if any packaged text file contains a machine-specific absolute path, an e-mail
address other than placeholders, something that looks like an API key / token / password, or if any media
file other than the allowed fonts/images is included.
"""
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skill" / "urm-creator-studio" / "scripts"))
from urmstudio.common import VERSION  # noqa: E402

# Recipient package: only what end users need. Tests, dev tools and internal reports stay in the repository.
RECIPIENT = ["README.md", "README.ar.md", "LICENSE", "USAGE-TERMS.md", "USAGE-TERMS.ar.md", "CHANGELOG.md",
             "SECURITY.md", "RELEASE_NOTES.md", "install.sh", "install.ps1", "Install-macOS.command",
             "Install-macOS-English.command", "Install-Windows.bat", "Install-Windows-English.bat",
             "skill", "docs", "examples"]
EXCLUDE_DIRS = {"__pycache__", ".git", "results", "dist", ".DS_Store", "evidence", "onboarding"}
EXCLUDE_FILES = {".DS_Store"}
ALLOWED_BINARY = {".ttf", ".png", ".jpg", ".mp4"}
MAX_MEDIA_MB = {"recipient": 8, "launch": 40}

PATTERNS = [
    (re.compile(r"/Users/[A-Za-z0-9._-]+/"), "absolute macOS home path"),
    (re.compile(r"/home/[a-z0-9._-]+/"), "absolute Linux home path"),
    (re.compile(r"[A-Za-z]:\\\\Users\\\\[A-Za-z0-9._-]+"), "absolute Windows user path"),
    (re.compile(r"/private/tmp/|/var/folders/"), "temporary path"),
    (re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}"), "API key"),
    (re.compile(r"(?i)(password|passwd|secret|api_key|apikey|token)\s*[:=]\s*['\"][^'\"]{6,}"), "credential"),
    (re.compile(r"[A-Za-z0-9._%+-]+@(gmail|hotmail|outlook|yahoo|icloud)\.com"), "personal e-mail address"),
]


def collect(entries, kind):
    files = []
    for e in entries:  # noqa
        p = ROOT / e
        if not p.exists():
            continue
        if p.is_file():
            files.append(p)
            continue
        for f in sorted(p.rglob("*")):
            if f.is_file() and not any(part in EXCLUDE_DIRS for part in f.relative_to(ROOT).parts) \
                    and f.name not in EXCLUDE_FILES:
                files.append(f)
    return files


def scan(files, kind):
    problems = []
    for f in files:
        rel = f.relative_to(ROOT)
        ext = f.suffix.lower()
        if ext in ALLOWED_BINARY:
            mb = f.stat().st_size / 1e6
            if ext == ".mp4" and kind == "recipient":
                problems.append("%s: video files are not allowed in the recipient package" % rel)
            if mb > MAX_MEDIA_MB[kind]:
                problems.append("%s: %.1f MB is too large" % (rel, mb))
            continue
        if ext in {".wav", ".mp3", ".mov", ".m4a", ".bin", ".zip", ".env", ".key", ".pem"}:
            problems.append("%s: file type not allowed" % rel)
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            problems.append("%s: unexpected binary file" % rel)
            continue
        for rx, label in PATTERNS:
            for m in rx.finditer(text):
                if f.name == "build_release.py":  # the patterns themselves
                    continue
                problems.append("%s: %s (%s)" % (rel, label, m.group(0)[:40]))
    return problems


def build(files, out, prefix):
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in files:
            rel = f.relative_to(ROOT)
            info = zipfile.ZipInfo.from_file(f, arcname=str(Path(prefix) / rel))
            if f.suffix in (".sh", ".command") or f.name == "studio.py":
                info.external_attr = (0o755 << 16)
            with open(f, "rb") as fh:
                z.writestr(info, fh.read(), compress_type=zipfile.ZIP_DEFLATED)
    return out


def main():
    import hashlib
    rec = collect(RECIPIENT, "recipient")
    probs = scan(rec, "recipient")
    if probs:
        print("❌ release scan failed:")
        for p in probs:
            print("  -", p)
        sys.exit(1)
    dist = ROOT / "dist"
    a = build(rec, dist / ("URM-Creator-Studio-v%s.zip" % VERSION), "URM-Creator-Studio")
    digest = hashlib.sha256(a.read_bytes()).hexdigest()
    (dist / (a.name + ".sha256")).write_text("%s  %s\n" % (digest, a.name), encoding="utf-8")
    print("✅ %s (%.2f MB, %d files)\n   sha256 %s" % (a.relative_to(ROOT), a.stat().st_size / 1e6,
                                                   len(zipfile.ZipFile(a).namelist()), digest))


if __name__ == "__main__":
    main()
