#!/usr/bin/env bash
# Double-click to install URM Creator Studio on a Mac.
# انقر مرتين لتثبيت استوديو URM للإبداع على جهاز ماك.
cd "$(dirname "$0")"
bash ./install.sh "$@"
echo
read -r -p "اضغط Enter لإغلاق النافذة / Press Enter to close… " _
