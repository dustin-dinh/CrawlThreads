@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Story Miner is not set up yet. Run setup.bat first.
  pause
  exit /b 1
)
if not exist "frontend\dist\index.html" (
  echo Frontend build is missing. Run setup.bat first.
  pause
  exit /b 1
)
set PYTHONPATH=%CD%\backend
start "" /B powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8765'"
echo Story Miner is running at http://127.0.0.1:8765
echo Press Ctrl+C to stop.
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8765
endlocal

