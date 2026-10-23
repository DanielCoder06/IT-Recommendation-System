@echo off

:: Load virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [LOI] venv
    pause
    exit /b 1
)

echo [OK] venv loaded
echo    http://127.0.0.1:8000
echo    http://172.22.5.135:8000
echo.

:: Open browser
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000"

:: Run FastAPI server
uvicorn server:app --host 0.0.0.0 --port 8000
