@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

:KEY_MENU
cls
echo ================================
echo Private Key Configuration
echo ================================
echo.
echo 1. Use private key from .env file
echo 2. Enter private key manually
echo 3. Exit
echo.
set /p KEY_CHOICE="Enter your choice (1, 2, or 3): "

if "%KEY_CHOICE%"=="" goto KEY_MENU
if "%KEY_CHOICE%"=="1" (
    if not exist ".env" (
        echo Error: .env file not found!
        echo Please create a .env file with PRIVATE_KEY or enter it manually.
        pause
        goto KEY_MENU
    )
    findstr /C:"PRIVATE_KEY" .env >nul
    if errorlevel 1 (
        echo Error: PRIVATE_KEY not found in .env file!
        echo Please add PRIVATE_KEY to .env or enter it manually.
        pause
        goto KEY_MENU
    )
    goto MENU
)
if "%KEY_CHOICE%"=="2" goto ENTER_KEY
if "%KEY_CHOICE%"=="3" exit /b 0
echo Invalid choice. Please enter 1, 2, or 3.
pause
goto KEY_MENU

:ENTER_KEY
cls
echo ================================
echo Enter Private Key
echo ================================
echo.
echo Please enter your private key
echo (without 0x prefix)
echo.
echo Press Enter with no input to return to previous menu
echo.
set /p PRIVATE_KEY="> "

if "%PRIVATE_KEY%"=="" (
    echo Returning to previous menu...
    timeout /t 2 >nul
    goto KEY_MENU
)

echo PRIVATE_KEY=0x%PRIVATE_KEY%> .env.tmp
type .env >> .env.tmp 2>nul
move /y .env.tmp .env >nul
goto MENU

:MENU
cls
echo ================================
echo HYB Distribution Configuration
echo ================================
echo.
echo 1. Use defaults (0.001 HYB, every 1 minute, run forever)
echo 2. Custom configuration
echo 3. Back to Private Key menu
echo.
set /p CHOICE="Enter your choice (1, 2, or 3): "

if "%CHOICE%"=="" goto MENU
if "%CHOICE%"=="1" goto DEFAULT
if "%CHOICE%"=="2" goto CUSTOM
if "%CHOICE%"=="3" goto KEY_MENU
echo Invalid choice. Please enter 1, 2, or 3.
pause
goto MENU

:DEFAULT
echo.
echo Using default configuration:
echo - Amount per transfer: 0.001 HYB
echo - Interval: Every 1 minute
echo - Duration: Run until stopped (Ctrl+C)
echo.
echo Press any key to start...
pause >nul
python tx_scheduler.py
goto END

:CUSTOM
cls
echo ================================
echo Custom Configuration
echo ================================
echo.

set /p HYB_AMOUNT="Enter HYB amount to send (e.g., 0.001): "
if "%HYB_AMOUNT%"=="" goto CUSTOM

set /p INTERVAL="Enter interval in minutes between sends (e.g., 30): "
if "%INTERVAL%"=="" goto CUSTOM

set /p DURATION="Enter how long to run in hours (e.g., 24): "
if "%DURATION%"=="" goto CUSTOM

echo.
echo Review your settings:
echo - Amount per transfer: %HYB_AMOUNT% HYB
echo - Interval: Every %INTERVAL% minutes
echo - Duration: %DURATION% hours
echo.
set /p CONFIRM="Is this correct? (Y/N): "

if /i "%CONFIRM%" neq "Y" goto CUSTOM

echo.
echo Starting HYB distribution script...
echo Press Ctrl+C to stop the script at any time
echo.

:: Calculate end time in minutes (current time + duration in hours * 60)
set /a END_TIME=%DURATION% * 60
python tx_scheduler.py %HYB_AMOUNT% %INTERVAL% %END_TIME%

:END
echo.
echo Script completed!
pause 