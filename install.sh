#!/usr/bin/env bash
# URM Creator Studio installer (macOS / Linux)
# مثبّت استوديو URM للإبداع
#
# Copies the skill into Claude Code's skills folder, creates your workspace
# (~/URM-Creator-Studio) and checks your computer. It asks before installing
# anything else. Your videos and brands are never touched by re-installing.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/skill/urm-creator-studio"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
DEST="$SKILLS_DIR/urm-creator-studio"

# Arabic-first: Arabic unless the user asks for English (./install.sh --en or URM_STUDIO_LANG=en)
LANG_UI="${URM_STUDIO_LANG:-ar}"
for arg in "$@"; do
  case "$arg" in --en) LANG_UI=en ;; --ar) LANG_UI=ar ;; esac
done
t() { if [ "$LANG_UI" = "ar" ]; then printf '%s\n' "$1"; else printf '%s\n' "$2"; fi; }

echo
t "🎬 تثبيت استوديو URM للإبداع" "🎬 Installing URM Creator Studio"
echo "------------------------------------------------------------"

if [ ! -f "$SRC/SKILL.md" ]; then
  t "❌ لم أجد ملفات الاستوديو بجانب هذا الملف. فكّ ضغط الحزمة كاملة ثم أعد المحاولة." \
    "❌ Studio files not found next to this script. Unzip the whole package and try again."
  exit 1
fi

PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  t "❌ بايثون 3.8 أو أحدث غير موجود." "❌ Python 3.8 or newer is required."
  if [ "$(uname)" = "Darwin" ]; then
    t "   الحل: افتح Terminal واكتب:  xcode-select --install   ثم أعد تشغيل هذا المثبّت." \
      "   Fix: open Terminal and run:  xcode-select --install   then run this installer again."
  else
    t "   الحل: ثبّت python3 من مدير الحزم في نظامك." "   Fix: install python3 with your package manager."
  fi
  exit 1
fi

mkdir -p "$SKILLS_DIR"
if [ -d "$DEST" ]; then
  BK="$DEST.backup-$(date +%Y%m%d-%H%M%S)"
  mv "$DEST" "$BK"
  t "ℹ️  وُجدت نسخة سابقة، نُقلت إلى: $BK" "ℹ️  Previous version moved to: $BK"
fi
cp -R "$SRC" "$DEST"
find "$DEST" -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true
t "✅ نُسخ الاستوديو إلى: $DEST" "✅ Studio copied to: $DEST"

"$PY" "$DEST/scripts/studio.py" --lang "$LANG_UI" home >/dev/null
"$PY" "$DEST/scripts/studio.py" --lang "$LANG_UI" settings --language "$LANG_UI" >/dev/null
echo
set +e
"$PY" "$DEST/scripts/studio.py" --lang "$LANG_UI" doctor
READY=$?
set -e

if ! command -v ffmpeg >/dev/null 2>&1 && [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
  echo
  if [ "$LANG_UI" = "ar" ]; then
    read -r -p "هل تريد تثبيت محرّك الفيديو FFmpeg الآن عبر Homebrew؟ (مجاني، عدة دقائق) [y/N] " ANS
  else
    read -r -p "Install the FFmpeg video engine now with Homebrew? (free, a few minutes) [y/N] " ANS
  fi
  case "${ANS:-}" in
    y|Y|yes|Yes|نعم|ن)
      brew install ffmpeg && "$PY" "$DEST/scripts/studio.py" --lang "$LANG_UI" doctor && READY=0 ;;
    *) t "حسنًا، يمكنك تثبيته لاحقًا وسيساعدك المساعد في ذلك." "OK — you can install it later; the assistant will help." ;;
  esac
fi

echo
echo "------------------------------------------------------------"
if [ "$LANG_UI" = "ar" ]; then
  cat <<'EOF'
🎉 انتهى التثبيت.

الخطوة التالية:
  1. افتح Claude Code (تطبيق Claude على سطح المكتب ← تبويب Code، أو اكتب claude في Terminal).
  2. اكتب:  مرحبًا، أريد صنع فيديو
     (أو اكتب  /urm-creator-studio )
  3. ضع صورك وفيديوهاتك في مجلد  URM-Creator-Studio/inbox  داخل مجلدك الشخصي.

الدليل الكامل بالعربية: docs/ar/
EOF
else
  cat <<'EOF'
🎉 Installation finished.

Next:
  1. Open Claude Code (Claude desktop app → Code tab, or type  claude  in Terminal).
  2. Type:  Hi, I want to make a video
     (or type  /urm-creator-studio )
  3. Put your photos and videos in the  URM-Creator-Studio/inbox  folder in your home folder.

Full guide: docs/en/
EOF
fi
exit 0
