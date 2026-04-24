from PIL import Image, ImageDraw
import img2pdf
import io
import random

def create_dummy():
    pdf_pages = []
    names = ["JONATHAN DOE", "SARAH SMITH", "ROBERT BROWN", "EMILY DAVIS", "MICHAEL WILSON", "LINDA JONES", "STEVEN CLARK", "KAREN WHITE", "UNKNOWN", "PETER PARKER"]
    leave_types = ["Paid Sick", "Paid Vacational", "Unpaid Sick", "Family Responsibility", "Unpaid Vacational", "Paid compassionate"]
    
    width, height = 800, 1000

    print("Generating 10 pages...")
    for i in range(10):
        # Create a white image
        img = Image.new('RGB', (width, height), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((width//2 - 100, 50), "ADR-UNIVERSAL LEAVE FORM", fill=(50, 50, 50))
        
        name = names[i]
        date = f"2026.04.{24 - i:02d}"
        lt = random.choice(leave_types)
        
        # Vary layout slightly
        if i % 2 == 0:
            d.text((100, 150), f"FULL NAME: {name}", fill=(0, 0, 0))
        else:
            d.text((100, 150), "FULL NAME:", fill=(0, 0, 0))
            d.text((100, 180), name, fill=(0, 0, 0))
            
        d.text((100, 250), f"DATE: {date}", fill=(0, 0, 0))
        
        y_offset = 350
        for choice in leave_types:
            mark = "[X]" if choice == lt else "[ ]"
            d.text((120, y_offset), f"{mark} {choice}", fill=(0, 0, 0))
            y_offset += 40

        # Save page image to a bytes buffer as PNG (no JPEG dependency)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        pdf_pages.append(img_byte_arr.getvalue())

    # Combine all PNGs into one PDF
    with open("dummy_test.pdf", "wb") as f:
        f.write(img2pdf.convert(pdf_pages))
    
    print("Successfully created dummy_test.pdf with 10 pages using img2pdf.")

if __name__ == "__main__":
    create_dummy()
