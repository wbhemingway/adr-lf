@echo off
setlocal enabledelayedexpansion

echo =======================================
echo ADR Leave Parser - Windows Build
echo =======================================
echo.

REM Define project variables
set VERSION=v1
set DIST_NAME=ADR_Leave_Parser_%VERSION%
set FINAL_EXE=adr_lf.exe

REM Ensure we are in the project root
cd %~dp0

REM Check if bin folder exists
if not exist "bin\tesseract\tesseract.exe" (
    echo [WARNING] bin\tesseract\tesseract.exe not found!
    echo Ensure you download Tesseract OCR and place it in the bin folder.
)

if not exist "bin\poppler\Library\bin\pdftoppm.exe" (
    echo [WARNING] bin\poppler\Library\bin\pdftoppm.exe not found!
    echo Ensure you download Poppler for Windows and place it in the bin folder.
)

echo Installing requirements...
uv sync

echo.
echo Starting Nuitka Compilation...
echo This may take 5-10 minutes depending on your CPU.
echo.

REM Run Nuitka
uv run python -m nuitka --standalone --windows-console-mode=disable --enable-plugin=tk-inter --include-data-dir=.venv\Lib\site-packages\customtkinter=customtkinter src/main.py

echo.
echo =======================================
echo Post-Build Automation
echo =======================================

REM 1. Clean up old build folder if it exists
if exist "%DIST_NAME%" rd /s /q "%DIST_NAME%"

REM 2. Rename the distribution folder
ren main.dist "%DIST_NAME%"

REM 3. Rename the executable
ren "%DIST_NAME%\main.exe" "%FINAL_EXE%"

REM 4. Copy the bin folder (OCR/PDF binaries)
echo Copying binaries...
xcopy "bin" "%DIST_NAME%\bin" /E /I /Y

REM 5. Copy Documentation and License files
echo Copying documentation...
if exist "LICENSE" copy "LICENSE" "%DIST_NAME%\"
if exist "README.txt" copy "README.txt" "%DIST_NAME%\"
if exist "SECURITY.txt" copy "SECURITY.txt" "%DIST_NAME%\"

echo.
echo =======================================
echo Build Complete!
echo Folder: %DIST_NAME%
echo Executable: %FINAL_EXE%
echo =======================================
pause
