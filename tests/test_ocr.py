import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ocr_engine import OCREngine


def test_ocr():
    engine = OCREngine()
    
    # Check if we have any images in the current dir or workspace to test with
    # For now, this is a placeholder that prints the logic result of a dummy string
    print("Testing OCR Parsing Logic...")
    
    dummy_text = """
    APPLICATION FOR LEAVE
    FULL NAME: J DOE
    DATE: 04/24/2026
    [X] Paid Sick
    [ ] Paid Vacational
    """
    
    parsed = engine._parse_text(dummy_text)
    print(f"Parsed Result: {parsed}")
    
    assert parsed["initial"] == "J"
    assert parsed["last_name"] == "DOE"
    assert parsed["date"] == "2026.04.24"
    assert parsed["leave_type"] == "Paid Sick"
    
    print("Test Passed!")

if __name__ == "__main__":
    test_ocr()
