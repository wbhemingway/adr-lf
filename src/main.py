import sys
import os
import platform
import shutil
from gui import LeaveSorterApp
from logger import app_logger

app_logger.info("Starting ADR-Universal Leave Sorter...")

# Determine base path for bundled binaries
if getattr(sys, 'frozen', False):
    # Running as compiled binary (Nuitka/PyInstaller)
    base_path = os.path.dirname(sys.executable)
else:
    # Running from source
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def setup_binaries():
    """
    Ensures Tesseract and Poppler are available.
    On Windows (frozen), it looks for bundled binaries in bin/.
    On Linux/WSL, it relies on system-installed binaries.
    """
    if platform.system() == "Windows":
        app_logger.debug("Running on Windows, resolving bundled binaries...")
        import pytesseract
        
        # 1. Tesseract resolution
        # Check if tesseract is already in PATH (system install)
        sys_tesseract = shutil.which("tesseract")
        if sys_tesseract:
            app_logger.info(f"Using system Tesseract: {sys_tesseract}")
            pytesseract.pytesseract.tesseract_cmd = sys_tesseract
        else:
            # Fallback to bundled
            tesseract_exe = os.path.join(base_path, 'bin', 'tesseract', 'tesseract.exe')
            if os.path.exists(tesseract_exe):
                app_logger.info(f"Using bundled Tesseract: {tesseract_exe}")
                pytesseract.pytesseract.tesseract_cmd = tesseract_exe
            else:
                app_logger.error("Tesseract not found in system or bundled bin/")
        
        # 2. Poppler resolution
        # Check if pdftoppm is already in PATH
        if not shutil.which("pdftoppm"):
            # Fallback to bundled poppler
            poppler_bin = os.path.join(base_path, 'bin', 'poppler', 'Library', 'bin')
            if os.path.exists(poppler_bin):
                app_logger.info(f"Using bundled Poppler: {poppler_bin}")
                os.environ["PATH"] += os.pathsep + poppler_bin
            else:
                app_logger.error("Poppler (pdftoppm) not found in system or bundled bin/")
        else:
            app_logger.info("Using system Poppler (pdftoppm)")

setup_binaries()

if __name__ == "__main__":
    app = LeaveSorterApp()
    app.mainloop()
