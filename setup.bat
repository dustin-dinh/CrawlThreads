@echo off
setlocal
cd /d "%~dp0"
echo [1/5] Checking runtimes...
where python >nul 2>&1 || (echo Python 3.11 or newer is required. & exit /b 1)
where node >nul 2>&1 || (echo Node.js 20 or newer is required. & exit /b 1)

echo [2/5] Creating Python environment...
if not exist ".venv\Scripts\python.exe" python -m venv .venv || exit /b 1

echo [3/5] Installing backend dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt || exit /b 1

echo [4/5] Installing and building frontend...
pushd frontend
call npm.cmd install || (popd & exit /b 1)
call npm.cmd run build || (popd & exit /b 1)
popd

echo [5/5] Initializing database...
set PYTHONPATH=%CD%\backend
".venv\Scripts\python.exe" -m alembic upgrade head || exit /b 1
".venv\Scripts\python.exe" -m app.cli || exit /b 1

if not exist ".env" copy /Y ".env.example" ".env" >nul
echo.
echo Setup complete. Start Story Miner with run.bat
endlocal

