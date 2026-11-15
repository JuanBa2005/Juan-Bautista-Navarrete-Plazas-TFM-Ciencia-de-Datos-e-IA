@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
if errorlevel 1 (echo Primero sigue los pasos del README para crear .venv & pause & exit /b 1)
start http://127.0.0.1:8000
python -m uvicorn src.app:app --host 127.0.0.1 --port 8000
pause
