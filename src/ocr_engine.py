import re
import pytesseract
from PIL import Image, ImageOps, ImageEnhance
from logger import app_logger
from datetime import datetime
from pdf2image import convert_from_path

class OCREngine:
    def __init__(self, tesseract_path: str):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def get_page_image(self, pdf_path: str, page_index: int, poppler_path: str):
        images = convert_from_path(
            pdf_path,
            first_page=page_index + 1,
            last_page=page_index + 1,
            dpi=150,
            poppler_path=poppler_path
        )
        if not images:
            raise ValueError(f"Could not extract page {page_index + 1}")
        image = images[0]
        ocr_data = self.process_image(image)
        return image, ocr_data

    def process_image(self, image: Image.Image) -> dict:
        """
        Runs full-page OCR on the image and attempts to extract
        Name, Date, and Leave Type using regex heuristics.
        """
        try:
            # Preprocessing for better OCR accuracy
            # 1. Convert to grayscale
            processed = image.convert('L')
            # 2. Increase contrast
            enhancer = ImageEnhance.Contrast(processed)
            processed = enhancer.enhance(2.0)
            # 3. Autocontrast (normalize)
            processed = ImageOps.autocontrast(processed)
            
            app_logger.info("Running OCR on image...")
            text = pytesseract.image_to_string(processed)
            app_logger.debug(f"Raw OCR text length: {len(text)}")
            return self._parse_text(text)
        except Exception as e:
            app_logger.error(f"OCR Error: {e}", exc_info=True)
            return {
                "initial": "",
                "last_name": "",
                "leave_type": "",
                "date": ""
            }
        
    def _normalize_date(self, raw_date: str) -> str:
        """Attempts to parse messy dates and format as YYYY.MM.DD."""
        # Clean up delimiters
        clean = raw_date.replace('-', '/').replace('.', '/')
        
        # Common formats to try
        formats = [
            "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d",
            "%m/%d/%y", "%d/%m/%y", "%y/%m/%d"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(clean, fmt)
                # If year is absurd (e.g. 200), fallback.
                if dt.year < 2000 or dt.year > 2100:
                    continue
                return dt.strftime("%Y.%m.%d")
            except ValueError:
                continue
        
        # Fallback to returning nothing if totally unparseable
        return ""

    def _parse_text(self, text: str) -> dict:
        result = {
            "initial": "",
            "last_name": "",
            "leave_type": "",
            "date": ""
        }
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Look for labels like "FULL NAME", "EMPLOYEE NAME", or just "NAME"
        for i, line in enumerate(lines):
            upper_line = line.upper()
            if any(label in upper_line for label in ["FULL NAME", "EMPLOYEE NAME", "NAME:"]):
                # Attempt to extract from same line
                name_part = re.sub(r'^.*(NAME|EMPLOYEE)[\s:;-]*', '', line, flags=re.IGNORECASE).strip()
                
                # If same line is empty or too short, check next line
                if (not name_part or len(name_part) < 2) and i + 1 < len(lines):
                    potential_name = lines[i+1].strip()
                    # Only take next line if it doesn't look like another label
                    if ":" not in potential_name and len(potential_name) > 2:
                        name_part = potential_name
                
                if name_part:
                    parts = name_part.split()
                    if len(parts) >= 2:
                        result["initial"] = parts[0][0].upper()
                        result["last_name"] = parts[-1].upper()
                        break
                    elif len(parts) == 1:
                        result["last_name"] = parts[0].upper()
                        break

        # Heuristic 2: Find Date (Signature date is usually at the bottom)
        # Look for common date patterns: MM/DD/YYYY, DD/MM/YYYY, YYYY.MM.DD
        date_pattern = r'\b(\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4})\b'
        dates = re.findall(date_pattern, text)
        if dates:
            # Prioritize the LAST match on the page, as signatures are at the bottom
            raw_date = dates[-1]
            result["date"] = self._normalize_date(raw_date)

        # Heuristic 3: Leave Type
        leave_types = [
            "Paid Vacational", "Unpaid Vacational", 
            "Paid Sick", "Unpaid Sick", 
            "Family Responsibility", "Paid compassionate"
        ]
        
        # Search for 'X' or checkmark indicators near the labels
        for lt in leave_types:
            # Look for an [X] or (X) or just X before the leave type
            # Standard Tesseract often reads checkboxes as [ ] or [x] or just 'x'
            pattern = rf'([\[\(\s][xXvV17][\]\)\s])\s*{re.escape(lt)}'
            if re.search(pattern, text, re.IGNORECASE):
                result["leave_type"] = lt
                break
            
            # Fallback: simple proximity
            if re.search(rf'[xXvV17]\s+{re.escape(lt)}', text, re.IGNORECASE):
                result["leave_type"] = lt
                break
                
        app_logger.info("OCR extraction complete.")
        return result
