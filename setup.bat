@echo off

IF EXIST "venv" (
    echo Virtual environment already exists, skipping creation...
) ELSE (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing/Updating requirements...
pip install -r requirements.txt

echo Setup completed!
pause 