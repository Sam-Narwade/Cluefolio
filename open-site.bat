@echo off
REM Open Cluefolio in your default browser. No server, no port, no network.

set ROOT=%~dp0

if exist "%ROOT%site\cluefolio.html" (
  start "" "%ROOT%site\cluefolio.html"
  exit /b 0
)

if exist "%ROOT%site\index.html" (
  start "" "%ROOT%site\index.html"
  exit /b 0
)

echo The site has not been built yet.
echo Run: python scripts\build_site.py
echo Then: python scripts\bundle_site.py
pause
exit /b 1
