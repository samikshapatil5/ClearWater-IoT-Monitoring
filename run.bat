@echo off
cd /d "%~dp0"
echo Installing frontend dependencies...
npm install
if errorlevel 1 goto error
if not exist "backend\.env" copy "backend\.env.example" "backend\.env" >nul
echo Installing backend dependencies...
npm --prefix backend install
if errorlevel 1 goto error
echo.
echo Starting ClearWater frontend + Agentic AI backend...
npm run dev
exit /b 0
:error
echo.
echo Installation failed. Check that Node.js and npm are installed.
pause
