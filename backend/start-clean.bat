@echo off
echo Cleaning pip cache...
pip cache purge

echo.
echo Installing backend dependencies (minimal)...
cd /d C:\Users\Clone\Desktop\Zawadi\work\backend
pip install -r requirements.txt

echo.
echo Starting FastAPI Backend on http://localhost:8000
echo.
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

pause
