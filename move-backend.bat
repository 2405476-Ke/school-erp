@echo off
echo Moving backend from school-erp subfolder to work root...

cd /d C:\Users\Clone\Desktop\Zawadi\work

REM Copy backend files to root backend folder
robocopy school-erp\backend backend /E /XD .git node_modules

REM List result
if exist "backend\src\main.py" (
    echo Backend move successful!
    echo.
    echo Current structure:
    echo - work/src - Frontend React
    echo - work/backend/src - FastAPI Backend
    echo.
) else (
    echo Warning: Backend files may not have copied correctly
)

pause
