@echo off
REM Create and activate the Python virtual environment (Windows)
cd /d "%~dp0"

if exist venv (
    echo Virtual environment already exists at environment\venv
) else (
    python -m venv venv
    echo Created virtual environment at environment\venv
)

echo.
echo Next steps:
echo   1. Activate:  environment\venv\Scripts\activate
echo   2. Install:   pip install -r environment\requirements.txt
echo   3. Run app:   python manage.py runserver
