@echo off
chcp 65001 >nul
REM Double-click to install URM Creator Studio on Windows
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
pause
