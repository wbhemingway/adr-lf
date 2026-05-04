import sys
import os
import platform
import shutil
from gui import LeaveSorterApp
from logger import app_logger

app_logger.info("Starting ADR-Universal Leave Sorter...")

def resolve_binaries():
    """
    Resolves absolute paths for Tesseract and Poppler binaries.
    On Windows (compiled or dev), it strictly relies on the bundled bin/ directory.
    On Linux/WSL, it relies on system-installed binaries.
    """
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if platform.system() == "Windows":
        tesseract_path = os.path.join(base_path, 'bin', 'tesseract', 'tesseract.exe')
        tessdata_path = os.path.join(base_path, 'bin', 'tesseract', 'tessdata')
        poppler_path = os.path.join(base_path, 'bin', 'poppler', 'Library', 'bin')
    else:
        tesseract_path = shutil.which("tesseract")
        tessdata_path = os.getenv("TESSDATA_PREFIX", "")
        poppler_bin = shutil.which("pdftoppm")
        poppler_path = os.path.dirname(poppler_bin) if poppler_bin else None

    # Validation
    errors = []
    if not tesseract_path or not os.path.exists(tesseract_path):
        errors.append(f"Tesseract binary not found at: {tesseract_path}")
    if not poppler_path or not os.path.exists(poppler_path):
        errors.append(f"Poppler bin folder not found at: {poppler_path}")
    if platform.system() == "Windows" and tessdata_path and not os.path.exists(tessdata_path):
        errors.append(f"Tessdata folder not found at: {tessdata_path}")
    
    if platform.system() == "Windows" and tessdata_path and os.path.exists(tessdata_path):
        if not os.path.exists(os.path.join(tessdata_path, "eng.traineddata")):
            errors.append(f"eng.traineddata not found in tessdata folder at: {tessdata_path}")
            
    if errors:
        error_msg = "Failed to resolve critical dependencies:\n\n" + "\n".join(errors)
        for err in errors:
            app_logger.critical(err)
        app_logger.critical("Failed to resolve critical dependencies. Exiting.")
        
        # Show explicit popup to the user
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw() # Hide the main window
            messagebox.showerror("Initialization Error", error_msg)
            root.destroy()
        except Exception as e:
            app_logger.error(f"Could not display error popup: {e}")
            
        sys.exit(1)

    if tessdata_path:
        os.environ["TESSDATA_PREFIX"] = tessdata_path

    return tesseract_path, poppler_path

if __name__ == "__main__":
    tesseract_path, poppler_path = resolve_binaries()
    app = LeaveSorterApp(tesseract_path=tesseract_path, poppler_path=poppler_path)
    app.mainloop()
