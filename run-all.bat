@echo off
setlocal
cd /d %~dp0
echo ==========================================
echo ClearWater - Integrated Frontend + Backend
echo ==========================================
if not exist node_modules\vite\bin\vite.js (
  echo Installing frontend dependencies...
  call npm install
  if errorlevel 1 pause & exit /b 1
)
if not exist backend\TASK_3_AGENTIC_AI\.env (
  copy backend\TASK_3_AGENTIC_AI\.env.example backend\TASK_3_AGENTIC_AI\.env >nul
  echo Created backend\TASK_3_AGENTIC_AI\.env. Configure Firebase and Gemini before expecting live Firebase/LLM results.
)
echo.
echo Starting DL API on port 8000 and Agentic AI API on port 5000.
echo Python 3.11 is recommended for TensorFlow compatibility.
start "ClearWater DL API" cmd /k "cd /d %~dp0backend\ClearWater_DL_API && py -3.11 -m uvicorn api.main:app --host 127.0.0.1 --port 8000"
start "ClearWater Agentic AI API" cmd /k "cd /d %~dp0backend\TASK_3_AGENTIC_AI && py -3.11 -m api.agent_api"
start "ClearWater Frontend" cmd /k "cd /d %~dp0 && npm run dev"
echo.
echo Frontend: http://localhost:5173
echo Agentic AI API: http://127.0.0.1:5000/api/health
echo DL API docs: http://127.0.0.1:8000/docs
echo.
echo If 'py -3.11' is not installed, edit this file to use your Python 3.11 executable.
pause
