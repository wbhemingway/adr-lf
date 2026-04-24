import hashlib
import os

from pypdf import PdfReader, PdfWriter

from config import config_manager
from logger import app_logger


class PDFProcessor:
    def __init__(self):
        self.reader = None
        self.total_pages = 0
        self.current_pdf_path = ""

    def load_pdf(self, file_path: str):
        app_logger.info(f"Loading PDF: {file_path}")
        self.current_pdf_path = file_path
        self.reader = PdfReader(file_path)
        self.total_pages = len(self.reader.pages)
        app_logger.info(f"PDF loaded. Total pages: {self.total_pages}")

        # Hash the file path so PII is not saved in config.json
        path_hash = hashlib.sha256(file_path.encode('utf-8')).hexdigest()

        # Check if we have a saved session for this file hash
        last_file_hash = config_manager.get("last_processed_file_hash")
        
        if last_file_hash == path_hash:
            saved_index = config_manager.get("last_processed_index", 0)
            # If the file was already fully processed, start over at 0
            if saved_index >= self.total_pages - 1:
                return 0
            return saved_index
        else:
            config_manager.set("last_processed_file_hash", path_hash)
            config_manager.set("last_processed_index", 0)
            return 0

    def save_page(self, page_index: int, initial: str, last_name: str, leave_type: str, date_str: str) -> str:
        """
        Saves the specific page as a new PDF using the naming convention:
        I_LASTNAME_LEAVETYPE_YYYY.MM.DD.pdf
        """
        if not self.reader:
            raise ValueError("No PDF loaded")

        output_dir = config_manager.get("output_directory")
        if not output_dir:
            raise ValueError("Output directory not set")

        # Sanitize inputs
        initial = initial.strip().upper()[:1] if initial else "X"
        last_name = last_name.strip().upper()
        if not last_name:
            last_name = "UNKNOWN"
            
        # Format leave type: remove spaces, uppercase
        if leave_type:
            lt_formatted = leave_type.replace(" ", "").upper()
        else:
            lt_formatted = "UNKNOWN"

        # Format date: replace / or - with .
        if date_str:
            date_formatted = date_str.replace("/", ".").replace("-", ".")
        else:
            date_formatted = "NO.DATE"

        filename = f"{initial}_{last_name}_{lt_formatted}_{date_formatted}.pdf"
        
        # Ensure safe filename for Windows
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')

        # Ensure output_dir is absolute to prevent relative path bugs
        output_dir = os.path.abspath(output_dir)
        output_path = os.path.join(output_dir, filename)

        # Write single page
        writer = PdfWriter()
        writer.add_page(self.reader.pages[page_index])
        
        with open(output_path, "wb") as f:
            writer.write(f)

        app_logger.info(f"Page {page_index} saved successfully to output directory.")
        return output_path

    def update_session(self, page_index: int):
        config_manager.set("last_processed_index", page_index)
