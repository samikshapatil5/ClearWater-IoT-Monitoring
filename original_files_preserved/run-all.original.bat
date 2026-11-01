@echo off
setlocal
cd /d %~dp0

echo ==========================================
echo ClearWater - Complete Development Startup
echo ==========================================

if not exist backend\.env copy backend\.env.example backend\.env >nul

where npm >nul 2>nul
if errorlevel 1 (
  echo ERROR: npm was not found. Restart VS Code after installing Node.js.
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo WARNING: Python was not found. The CNN-LSTM service will not start.
  echo The Node.js demo fallback will still work.
) else (
  if exist ml_service\.venv\Scripts\uvicorn.exe (
    start "ClearWater CNN-LSTM" cmd /k "cd /d %~dp0ml_service && call .venv\Scripts\activate.bat && uvicorn app:app --host 0.0.0.0 --port 8000"
  ) else (
    echo Python is installed but ML dependencies are not set up.
    echo Run setup-ml.bat once if you want the CNN-LSTM API.
  )
)

if not exist node_modules npm install
if not exist backend\node_modules npm --prefix backend install

start "ClearWater Web + Backend" cmd /k "cd /d %~dp0 && npm run dev"

echo.
echo Frontend: http://localhost:5173
 echo Backend:  http://localhost:5000
 echo ML API:   http://localhost:8000
 echo.
pause
