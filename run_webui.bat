@echo off
echo Starting HYB Distribution Web Interface...
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the web interface
python webui.py

REM If there was an error, pause
if errorlevel 1 (
    echo.
    echo An error occurred while running the web interface.
    pause
)

REM Deactivate virtual environment
if exist "venv\Scripts\deactivate.bat" (
    call venv\Scripts\deactivate.bat
) 