@echo off
setlocal
cd /d %~dp0
where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed or not on PATH.
  pause
  exit /b 1
)
python -m venv ml_service\.venv
call ml_service\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r ml_service\requirements.txt
echo.
echo CNN-LSTM environment ready.
echo Next: put your real labelled CSV somewhere in the project and run:
echo python ml_service\train.py --csv data\your_real_dataset.csv --window 12 --epochs 25
pause
