import os


def run_ocr(image_path):
    """
    Run OCR on an image file.
    Returns extracted text or a message if OCR engine is not available.
    """
    try:
        import easyocr
        reader = easyocr.Reader(['en'])
        result = reader.readtext(image_path)
        # Extract text from EasyOCR results
        text_parts = [item[1] for item in result]
        return '\n'.join(text_parts)
    except ImportError:
        return "OCR engine not installed. Please install easyocr."
    except Exception as e:
        return f"OCR error: {str(e)}"

