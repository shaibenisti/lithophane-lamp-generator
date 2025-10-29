@echo off
echo ========================================
echo  Premium Lithophane Lamp Generator
echo  Professional 3D Lithophane Creator
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo Checking dependencies...
python -c "import PyQt6, cv2, numpy, trimesh, scipy, yaml" >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Some dependencies may be missing
    echo Installing/updating dependencies...
    python -m pip install --upgrade -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        echo Please run: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo.
echo Starting Premium Lithophane Lamp Generator...
echo.

REM Run the modular application
python main.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Application failed to start (Exit code: %errorlevel%)
    echo Check lamp_generator.log for details
    echo.
)

pause