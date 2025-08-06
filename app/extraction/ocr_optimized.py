import concurrent.futures
from pytesseract import image_to_string
from PIL import Image

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

def run_ocr_on_frames_optimized(frame_paths: list[str], max_workers: int = 4) -> str:
    """
    Optimized OCR processing that runs in parallel
    """
    if not frame_paths:
        return ""
    
    # Process frames in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all OCR tasks
        future_to_path = {executor.submit(process_single_frame_ocr, path): path for path in frame_paths}
        
        # Collect results
        texts = []
        for future in concurrent.futures.as_completed(future_to_path):
            text = future.result()
            if text:  # Only add non-empty results
                texts.append(text)
    
    return "\n".join(texts)

def run_ocr_on_frames(frame_paths: list[str]) -> str:
    """
    Original OCR method (kept for compatibility)
    """
    texts = []
    for path in frame_paths:
        text = image_to_string(Image.open(path))
        texts.append(text)
    return "\n".join(texts) 