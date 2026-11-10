# URM Creator Studio installer (Windows PowerShell)
# مثبّت استوديو URM للإبداع لنظام ويندوز
# Usage: right-click > Run with PowerShell, or double-click Install-Windows.bat
param([switch]$en)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ar = -not $en -and ($env:URM_STUDIO_LANG -ne "en")
function T($a, $e) { if ($ar) { Write-Host $a } else { Write-Host $e } }
function Refresh-Path {
  $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = Join-Path $here "skill\urm-creator-studio"
$skills = if ($env:CLAUDE_SKILLS_DIR) { $env:CLAUDE_SKILLS_DIR } else { Join-Path $env:USERPROFILE ".claude\skills" }
$dest = Join-Path $skills "urm-creator-studio"
$lang = if ($ar) { "ar" } else { "en" }

T "🎬 تثبيت استوديو URM للإبداع" "🎬 Installing URM Creator Studio"
if (-not (Test-Path (Join-Path $src "SKILL.md"))) {
  T "❌ لم أجد ملفات الاستوديو. فكّ ضغط الحزمة كاملة ثم أعد المحاولة." "❌ Studio files not found. Unzip the whole package first."
  exit 1
}

$py = $null
foreach ($c in @("py", "python", "python3")) {
  try { & $c -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" 2>$null; if ($LASTEXITCODE -eq 0) { $py = $c; break } } catch {}
}
if (-not $py) {
  T "❌ بايثون غير مثبّت." "❌ Python is not installed."
  $q0 = if ($ar) { "هل تريد تثبيته الآن عبر winget؟ (y/N)" } else { "Install it now with winget? (y/N)" }
  $ans = Read-Host $q0
  if ($ans -match '^(y|Y|نعم|ن)$') {
    winget install -e --id Python.Python.3.12
    Refresh-Path
    foreach ($c in @("py", "python")) {
      try { & $c -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" 2>$null; if ($LASTEXITCODE -eq 0) { $py = $c; break } } catch {}
    }
  }
  if (-not $py) {
    T "ℹ️ أغلق هذه النافذة ثم شغّل المثبّت مرة أخرى." "ℹ️ Close this window and run the installer again."
    exit 1
  }
}

New-Item -ItemType Directory -Force -Path $skills | Out-Null
if (Test-Path $dest) {
  $bk = "$dest.backup-" + (Get-Date -Format "yyyyMMdd-HHmmss")
  Move-Item $dest $bk
  T "ℹ️ نُقلت النسخة السابقة إلى: $bk" "ℹ️ Previous version moved to: $bk"
}
Copy-Item -Recurse $src $dest
Get-ChildItem -Path $dest -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
T "✅ نُسخ الاستوديو إلى: $dest" "✅ Studio copied to: $dest"

$studio = Join-Path $dest "scripts\studio.py"
& $py $studio --lang $lang home | Out-Null
& $py $studio --lang $lang settings --language $lang | Out-Null
& $py $studio --lang $lang doctor

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  $q = if ($ar) { "هل تريد تثبيت محرّك الفيديو FFmpeg الآن عبر winget؟ (مجاني) (y/N)" } else { "Install the FFmpeg video engine now with winget? (free) (y/N)" }
  $ans = Read-Host $q
  if ($ans -match '^(y|Y|نعم|ن)$') {
    winget install -e --id Gyan.FFmpeg
    Refresh-Path
    & $py $studio --lang $lang doctor
    T "ℹ️ إذا كان Claude Code مفتوحًا، أغلقه وافتحه من جديد حتى يتعرّف على FFmpeg." "ℹ️ If Claude Code is open, close and reopen it so FFmpeg is found."
  }
}

if ($ar) {
@"

🎉 انتهى التثبيت.
الخطوة التالية:
  1. افتح Claude Code (تطبيق Claude ← تبويب Code).
  2. اكتب: مرحبًا، أريد صنع فيديو   (أو /urm-creator-studio)
  3. ضع صورك وفيديوهاتك في مجلد URM-Creator-Studio\inbox داخل مجلدك الشخصي.
الدليل الكامل: docs\ar\
"@ | Write-Host
} else {
@"

🎉 Installation finished.
Next:
  1. Open Claude Code (Claude app → Code tab).
  2. Type: Hi, I want to make a video   (or /urm-creator-studio)
  3. Put your photos and videos in URM-Creator-Studio\inbox in your user folder.
Full guide: docs\en\
"@ | Write-Host
}
