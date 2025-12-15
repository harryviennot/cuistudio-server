#!/usr/bin/env python3
"""
Compare OCR engines on recipe images to find the most accurate one.

Tests:
1. Tesseract (current implementation)
2. PaddleOCR (higher accuracy, GPU optional)
3. Tesseract with different preprocessing

Usage:
    cd cuistudio-server
    source venv/bin/activate
    python scripts/compare_ocr_engines.py
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add the app to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

# Suppress PaddleOCR verbose logging
import logging
logging.getLogger("ppocr").setLevel(logging.WARNING)

# Test images
PROJECT_ROOT = Path(__file__).parent.parent
TEST_IMAGES = list((PROJECT_ROOT / "benchmark_inputs").glob("*.HEIC")) + \
              list((PROJECT_ROOT / "benchmark_inputs").glob("*.jpg")) + \
              list((PROJECT_ROOT / "benchmark_inputs").glob("*.jpeg")) + \
              list((PROJECT_ROOT / "benchmark_inputs").glob("*.png"))


def load_image(image_path: str) -> Image.Image:
    """Load image, handling HEIC format"""
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        pass
    return Image.open(image_path)


def preprocess_for_ocr_current(image: Image.Image) -> Image.Image:
    """Current preprocessing (from photo_extractor.py)"""
    if image.mode != 'RGB':
        image = image.convert('RGB')

    max_dimension = 2400
    if max(image.size) > max_dimension:
        ratio = max_dimension / max(image.size)
        new_size = tuple(int(dim * ratio) for dim in image.size)
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)

    # Increase sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.3)

    # Median filter for noise
    image = image.filter(ImageFilter.MedianFilter(size=3))

    return image


def preprocess_for_ocr_enhanced(image: Image.Image) -> Image.Image:
    """Enhanced preprocessing for better number recognition"""
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Upscale for better OCR (300 DPI equivalent)
    # Most recipe cards are small, upscaling helps
    min_dimension = 2000
    if min(image.size) < min_dimension:
        ratio = min_dimension / min(image.size)
        new_size = tuple(int(dim * ratio) for dim in image.size)
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    # Strong contrast enhancement
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)

    # Strong sharpening
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)

    # Brightness adjustment (slightly brighter helps with dark text)
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.1)

    return image


def run_tesseract_current(image: Image.Image) -> str:
    """Tesseract with current settings"""
    processed = preprocess_for_ocr_current(image)
    custom_config = r'--oem 3 --psm 6'
    return pytesseract.image_to_string(processed, config=custom_config)


def run_tesseract_enhanced(image: Image.Image) -> str:
    """Tesseract with enhanced preprocessing"""
    processed = preprocess_for_ocr_enhanced(image)
    # PSM 3 = Fully automatic page segmentation (better for mixed layouts)
    custom_config = r'--oem 3 --psm 3'
    return pytesseract.image_to_string(processed, config=custom_config)


def run_tesseract_digits_focus(image: Image.Image) -> str:
    """Tesseract optimized for digit recognition"""
    processed = preprocess_for_ocr_enhanced(image)
    # Use both legacy + LSTM and digits whitelist for numbers
    # Note: We can't use whitelist as it would miss text, so we use best number recognition settings
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_blacklist=|'
    return pytesseract.image_to_string(processed, config=custom_config)


def run_paddleocr(image: Image.Image) -> str:
    """PaddleOCR - generally higher accuracy"""
    from paddleocr import PaddleOCR

    # Initialize PaddleOCR (uses GPU if available, falls back to CPU)
    # lang='en' for English, or 'multilingual' for mixed
    ocr = PaddleOCR(
        use_angle_cls=True,  # Handles rotated text
        lang='en',  # Change to 'multilingual' if recipes have non-English text
        show_log=False,
        use_gpu=False,  # Set to True if GPU available
    )

    # Convert PIL to numpy array
    import numpy as np
    img_array = np.array(image.convert('RGB'))

    # Run OCR
    result = ocr.ocr(img_array, cls=True)

    # Extract text from results
    texts = []
    if result and result[0]:
        for line in result[0]:
            if line and len(line) > 1:
                text = line[1][0]  # Get the text
                texts.append(text)

    return '\n'.join(texts)


def run_paddleocr_multilingual(image: Image.Image) -> str:
    """PaddleOCR with multilingual support (for French recipes)"""
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(
        use_angle_cls=True,
        lang='fr',  # French for French recipes
        show_log=False,
        use_gpu=False,
    )

    import numpy as np
    img_array = np.array(image.convert('RGB'))

    result = ocr.ocr(img_array, cls=True)

    texts = []
    if result and result[0]:
        for line in result[0]:
            if line and len(line) > 1:
                text = line[1][0]
                texts.append(text)

    return '\n'.join(texts)


def run_easyocr(image: Image.Image) -> str:
    """EasyOCR - easy to use, good accuracy"""
    import easyocr
    import numpy as np

    # Initialize reader (downloads models on first run)
    # Support both English and French
    reader = easyocr.Reader(['en', 'fr'], gpu=False, verbose=False)

    img_array = np.array(image.convert('RGB'))

    # Run OCR
    results = reader.readtext(img_array)

    # Extract text from results
    texts = [result[1] for result in results]

    return '\n'.join(texts)


def run_easyocr_enhanced(image: Image.Image) -> str:
    """EasyOCR with enhanced preprocessing"""
    import easyocr
    import numpy as np

    # Apply enhanced preprocessing
    processed = preprocess_for_ocr_enhanced(image)

    reader = easyocr.Reader(['en', 'fr'], gpu=False, verbose=False)

    img_array = np.array(processed)

    results = reader.readtext(img_array)
    texts = [result[1] for result in results]

    return '\n'.join(texts)


def analyze_numbers_in_text(text: str) -> Dict[str, Any]:
    """Extract and analyze numbers found in text"""
    import re
    numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
    return {
        "numbers_found": numbers,
        "count": len(numbers),
        "has_double_digits": any(len(n) >= 2 for n in numbers)
    }


def main():
    print("=" * 70)
    print("OCR Engine Comparison for Recipe Images")
    print("=" * 70)

    if not TEST_IMAGES:
        print("No test images found in benchmark_inputs/")
        return

    print(f"Found {len(TEST_IMAGES)} test images")
    print()

    engines = [
        ("Tesseract (current)", run_tesseract_current),
        ("Tesseract (enhanced)", run_tesseract_enhanced),
        ("EasyOCR", run_easyocr),
        ("EasyOCR (enhanced)", run_easyocr_enhanced),
    ]

    results = []

    # Test only first 2 images to keep output manageable
    for image_path in TEST_IMAGES[:2]:
        print(f"\n{'='*70}")
        print(f"Image: {image_path.name}")
        print("=" * 70)

        image = load_image(str(image_path))
        print(f"Size: {image.size}")
        print()

        image_results = {"image": image_path.name, "engines": {}}

        for engine_name, engine_func in engines:
            print(f"\n--- {engine_name} ---")

            try:
                start = time.time()
                text = engine_func(image)
                elapsed = time.time() - start

                # Analyze the extracted text
                numbers = analyze_numbers_in_text(text)

                print(f"Time: {elapsed:.2f}s")
                print(f"Characters: {len(text)}")
                print(f"Numbers found: {numbers['numbers_found'][:20]}...")  # First 20 numbers
                print()
                print("Text preview (first 500 chars):")
                print("-" * 40)
                print(text[:500])
                print("-" * 40)

                image_results["engines"][engine_name] = {
                    "time": elapsed,
                    "char_count": len(text),
                    "numbers": numbers,
                    "text": text
                }

            except Exception as e:
                print(f"ERROR: {e}")
                image_results["engines"][engine_name] = {"error": str(e)}

        results.append(image_results)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for img_result in results:
        print(f"\n{img_result['image']}:")
        for engine_name, data in img_result["engines"].items():
            if "error" in data:
                print(f"  {engine_name}: ERROR - {data['error']}")
            else:
                print(f"  {engine_name}: {data['time']:.2f}s, {data['char_count']} chars, {data['numbers']['count']} numbers")


if __name__ == "__main__":
    main()
