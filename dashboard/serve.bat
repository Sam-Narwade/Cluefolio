@echo off
setlocal
cd /d "%~dp0.."
python dashboard\serve.py --port 8080
endlocal
pause
