@echo off
chcp 65001 > nul
cd /d "%~dp0"
python "%~dp0download_note_membership.py"
echo.
echo スマホ向けWebページ（GitHub Pages）へ反映しています...
git add index.html app.css app.js articles/ images/
git commit -m "Update articles archive"
git push origin main
pause
