@echo off
chcp 65001 >nul
title AntiScam Installer

echo ============================================
echo   AntiScam - Discord Bot Installer
echo ============================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo [2/3] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo [3/3] Setting up configuration...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo   Created .env from .env.example
        echo   [IMPORTANT] Edit .env and set your Discord bot TOKEN!
    )
) else (
    echo   .env already exists, skipping.
)

echo.
echo ============================================
echo   Installation complete!
echo ============================================
echo.
echo   Next steps:
echo   1. Edit .env and paste your bot token:  TOKEN=your_token_here
echo   2. Add reference scam images to the img/ folder
echo   3. Run the bot:  venv\Scripts\python bot.py
echo.
pause
