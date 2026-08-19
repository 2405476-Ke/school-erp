@echo off
cd /d C:\Users\Clone\Desktop\Zawadi\work\backend

echo Installing Python dependencies...
pip install -r requirements.txt --quiet

echo.
echo Starting FastAPI Backend on http://localhost:8000
echo.
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

pause
