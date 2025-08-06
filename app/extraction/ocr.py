from pytesseract import image_to_string
from PIL import Image
import concurrent.futures
from app.config import Settings

def process_single_frame_ocr(frame_path: str) -> str:
    """
    Process a single frame with optimized OCR settings
    """
    try:
        # Use faster OCR configuration
        config = '--oem 1 --psm 6'
        text = image_to_string(Image.open(frame_path), config=config)
        return text.strip()
    except Exception as e:
        print(f"OCR error on {frame_path}: {e}")
        return ""

def run_ocr_on_frames(frame_paths: list[str]) -> str:
    """
    Optimized OCR processing that runs in parallel
    """
    if not frame_paths:
        return ""
    
    # Process frames in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=Settings.MAX_WORKERS) as executor:
        # Submit all OCR tasks
        future_to_path = {executor.submit(process_single_frame_ocr, path): path for path in frame_paths}
        
        # Collect results
        texts = []
        for future in concurrent.futures.as_completed(future_to_path):
            text = future.result()
            if text:  # Only add non-empty results
                texts.append(text)
    
    return "\n".join(texts)