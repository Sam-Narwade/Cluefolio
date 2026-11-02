@echo off
setlocal
title Cluefolio local server
cd /d "%~dp0"

echo.
echo  Cluefolio local server
echo  ----------------------
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo  Python was not found on PATH.
  echo  Install Python 3.9+ from python.org, then run this again.
  echo.
  pause
  exit /b 1
)

echo  Building the site...
python scripts\build_site.py
if errorlevel 1 (
  echo.
  echo  Build failed. See the message above.
  pause
  exit /b 1
)

echo.
echo  Starting the server. Keep this window open.
echo  Close this window or press Ctrl+C to stop.
echo.

python scripts\build_site.py --serve --port 8080

echo.
echo  Server stopped.
pause
