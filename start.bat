@echo off
echo Checking dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing dependencies!
    pause
    exit /b %errorlevel%
)

echo.
echo Starting FreeTranscriber...
cd /d "%~dp0"
python src/main.py
pause