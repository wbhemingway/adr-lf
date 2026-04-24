@echo off
echo =======================================
echo ADR Leave Parser - Windows Nuitka Build
echo =======================================
echo.

REM Ensure we are in the project root
cd %~dp0

REM Check if bin folder exists
if not exist "bin\tesseract\tesseract.exe" (
    echo [WARNING] bin\tesseract\tesseract.exe not found!
    echo Ensure you download Tesseract OCR and place it in the bin folder before distributing.
    echo The executable will still build, but OCR will fail on target machines.
    echo.
)

if not exist "bin\poppler\Library\bin\pdftoppm.exe" (
    echo [WARNING] bin\poppler\Library\bin\pdftoppm.exe not found!
    echo Ensure you download Poppler for Windows and place it in the bin folder.
    echo.
)

echo Installing requirements...
uv sync

echo.
echo Starting Nuitka Compilation...
echo This may take 5-10 minutes depending on your CPU.
echo.

REM Run Nuitka
REM --standalone: Creates a self-contained folder
REM --windows-console-mode=disable: Hides the command prompt when running the app
REM --enable-plugin=tk-inter: Bundles Tkinter dependencies
REM --include-data-dir: Bundles customtkinter assets
uv run python -m nuitka --standalone --windows-console-mode=disable --enable-plugin=tk-inter --include-data-dir=.venv\Lib\site-packages\customtkinter=customtkinter src/main.py

echo.
echo =======================================
echo Build Complete!
echo You can find your compiled application in the 'main.dist' folder.
echo NOTE: Make sure to copy the 'bin' folder into 'main.dist' before zipping it for distribution.
echo =======================================
pause
