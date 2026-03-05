@echo off
setlocal EnableDelayedExpansion
title Basudev's Custom Sky Maker
color 0A
cd /d "%~dp0"

echo.
echo  ============================================================
echo    Basudev's Custom Sky Maker - Smart Launcher
echo  ============================================================
echo.

echo  [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  [!] Python is NOT installed.
    set /p DLPY="  Download and install Python now? (yes/no): "
    if /i "!DLPY!"=="yes" (
        echo  Downloading Python 3.11...
        curl -L --progress-bar -o "%TEMP%\python_setup.exe" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
        if errorlevel 1 ( echo  Download failed. Get Python from python.org & pause & exit /b )
        "%TEMP%\python_setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
        del "%TEMP%\python_setup.exe" >nul 2>&1
        echo  [OK] Python installed! Please close and re-open START.bat
        pause
        exit /b
    ) else (
        echo  Please install Python from python.org
        pause
        exit /b
    )
)
for /f "tokens=*" %%V in ('python --version 2^>^&1') do set PYVER=%%V
echo  [OK] !PYVER!

echo  [2/4] Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 ( python -m ensurepip --upgrade >nul 2>&1 )
echo  [OK] pip ready.

echo  [3/4] Checking Pillow...
python -c "from PIL import Image" >nul 2>&1
if errorlevel 1 (
    set /p ANS3="  [!] Pillow not found. Install? (yes/no): "
    if /i "!ANS3!"=="yes" (
        python -m pip install pillow --quiet
        echo  [OK] Pillow installed.
    ) else ( pause & exit /b )
) else ( echo  [OK] Pillow found. )

echo  [4/4] Checking NumPy...
python -c "import numpy" >nul 2>&1
if errorlevel 1 (
    set /p ANS4="  [!] NumPy not found. Install? (yes/no): "
    if /i "!ANS4!"=="yes" (
        python -m pip install numpy --quiet
        echo  [OK] NumPy installed.
    ) else ( pause & exit /b )
) else ( echo  [OK] NumPy found. )

if not exist "SkyMaker.pyw" ( echo  [!] SkyMaker.pyw missing! & pause & exit /b )
if not exist "overlays\" ( echo  [!] overlays folder missing! & pause & exit /b )

echo.
echo  All requirements met! Launching Sky Maker...
echo.
timeout /t 1 /nobreak >nul

python "SkyMaker.pyw"

if errorlevel 1 (
    echo.
    echo  [!] An error occurred while running SkyMaker.
    pause
)
