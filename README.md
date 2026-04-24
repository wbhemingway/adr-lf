# ADR Leave Parser

ADR Leave Parser is a secure, cross-platform desktop application designed to automate the ingestion, Optical Character Recognition (OCR), and standard renaming of Human Resources leave forms.

## Features

- **100% Offline Processing:** Completely air-gapped architecture ensures no PII (Personally Identifiable Information) leaves your local machine, guaranteeing IT compliance.
- **Smart OCR Engine:** Automatically extracts the employee's initial, last name, leave type, and normalized signature date from scanned PDFs.
- **Zero-Latency Preloading:** A silent background thread processes future pages while you review the current one, completely eliminating OCR wait times.
- **Modern Interface:** Built with CustomTkinter, featuring a clean sidebar, dark/light theme options, and interactive Canvas zooming/panning to read messy handwriting.
- **Portable Distribution:** The application can be compiled into a standalone Windows executable.

## Prerequisites (Development)

If you are running from source (e.g., WSL or Linux):

```bash
sudo apt-get update
sudo apt-get install -y poppler-utils tesseract-ocr python3-tk
uv sync
```


## How to Use

1. Launch the application via `.venv/bin/python3 src/main.py` (or the `.exe` if compiled).
2. Click **⚙ Settings** to select your target Output Directory.
3. Click **Load PDF** and select a multi-page scanned PDF containing leave forms.
4. The first page will load. The Extracted Data form will automatically populate.
5. You can use your **mouse wheel** to zoom in on the PDF, and **click-and-drag** to pan around if the handwriting is difficult to read.
6. Verify or correct the OCR text in the input fields.
7. Press `Ctrl+S` or click **Confirm & Save** to split that page into a new PDF using the strict naming convention. The next page will load instantly.

## Nuitka Build (Windows)

To distribute this application to non-technical users on Windows, you must compile it on a Windows host using the provided build script.

1. Clone this repository onto a Windows machine.
2. Ensure Python and the required dependencies are installed.
3. Place `tesseract.exe` and `poppler` binaries inside a `bin/` folder at the root of the project.
4. Run `build_windows.bat` to generate the standalone executable.
