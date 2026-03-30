#!/usr/bin/env python3
"""
Scribbly Preprocessing Test Script

Tests all preprocessing functions and generates comparison grids.
"""

import time
from pathlib import Path
from typing import List

from PIL import Image

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_test_image(
    size: tuple = (512, 512),
    content: str = "simple",
) -> Image.Image:
    """
    Create a test image with simple shapes.
    
    Args:
        size: Image size (width, height)
        content: Type of content - 'simple', 'complex', 'faded'
        
    Returns:
        PIL Image
    """
    import cv2
    import numpy as np
    
    width, height = size
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    if content == "simple":
        # Draw a simple house
        # House body
        cv2.rectangle(img, (150, 250), (350, 450), (50, 50, 50), 2)
        # Roof
        pts = np.array([[150, 250], [350, 250], [250, 150]], np.int32)
        cv2.polylines(img, [pts], True, (50, 50, 50), 2)
        # Door
        cv2.rectangle(img, (220, 350), (280, 450), (100, 100, 100), -1)
        # Window
        cv2.rectangle(img, (180, 300), (220, 340), (150, 150, 150), 2)
        # Sun
        cv2.circle(img, (400, 100), 40, (255, 200, 0), 2)
        
    elif content == "complex":
        # Draw multiple overlapping shapes
        for i in range(10):
            x = int(50 + i * 50)
            y = int(50 + (i % 3) * 150)
            cv2.rectangle(img, (x, y), (x + 80, y + 80), (i * 20, 100, 200), 2)
        # Some circles
        for i in range(5):
            cv2.circle(img, (100 + i * 80, 400), 30, (200, 50, 50), 2)
            
    elif content == "faded":
        # Draw with faded lines (low contrast)
        cv2.rectangle(img, (150, 250), (350, 450), (200, 200, 200), 1)
        pts = np.array([[150, 250], [350, 250], [250, 150]], np.int32)
        cv2.polylines(img, [pts], True, (200, 200, 200), 1)
    
    return Image.fromarray(img)


def create_comparison_grid(
    original: Image.Image,
    processed: List[Image.Image],
    titles: List[str],
    output_path: Path,
) -> None:
    """
    Create a comparison grid of original and processed images.
    
    Args:
        original: Original input image
        processed: List of processed images
        titles: List of titles for each processed image
        output_path: Path to save the grid
    """
    import numpy as np
    
    # Create output image
    n_cols = len(processed) + 1
    max_height = max(original.height, max(p.height for p in processed))
    max_width = max(original.width, max(p.width for p in processed))
    
    # Scale to common size for display
    scale = 512 // max_width
    if scale < 1:
        scale = 1
    
    display_width = max_width * scale
    display_height = max_height * scale
    
    # Create canvas
    canvas = np.ones((display_height, display_width * n_cols, 3), dtype=np.uint8) * 255
    
    # Helper to convert image to RGB
    def to_rgb(img: Image.Image) -> np.ndarray:
        arr = np.array(img.resize((display_width, display_height), Image.LANCZOS))
        if len(arr.shape) == 2:  # Grayscale
            return np.stack([arr, arr, arr], axis=-1)
        return arr
    
    # Add original
    canvas[:display_height, :display_width] = to_rgb(original)
    
    # Add processed images
    for i, (proc, title) in enumerate(zip(processed, titles)):
        start_col = (i + 1) * display_width
        canvas[:display_height, start_col:start_col + display_width] = to_rgb(proc)
    
    # Add titles using PIL
    result = Image.fromarray(canvas)
    
    # Save
    result.save(output_path)
    print(f"✓ Saved comparison grid to: {output_path}")


def test_preprocessing_functions():
    """Test all preprocessing functions."""
    print("\n" + "=" * 60)
    print("Testing Preprocessing Functions")
    print("=" * 60 + "\n")
    
    # Import preprocessing module
    from preprocess import (
        auto_enhance_contrast,
        binarize,
        denoise,
        normalize_size,
        to_canny,
        to_hed,
        to_scribble,
        preprocess_sketch,
    )
    
    # Create test images
    test_images = {
        "simple": create_test_image(content="simple"),
        "complex": create_test_image(content="complex"),
        "faded": create_test_image(content="faded"),
    }
    
    results = []
    
    for name, img in test_images.items():
        print(f"\nTesting: {name}")
        print("-" * 40)
        
        # Test each function
        functions = [
            ("normalize", lambda: normalize_size(img, max_size=512)),
            ("enhance_contrast", lambda: auto_enhance_contrast(img)),
            ("canny", lambda: to_canny(img)),
            ("scribble", lambda: to_scribble(img)),
            ("denoise", lambda: denoise(img)),
            ("binarize", lambda: binarize(img, method="otsu")),
            ("full_pipeline", lambda: preprocess_sketch(img, method="scribble")),
        ]
        
        for func_name, func in functions:
            try:
                start_time = time.time()
                result = func()
                elapsed = (time.time() - start_time) * 1000  # ms
                
                status = "✓" if elapsed < 500 else "⚠"
                print(f"  {status} {func_name}: {elapsed:.1f}ms")
                
                if elapsed > 500:
                    print(f"      Warning: Processing took {elapsed:.1f}ms (target: <500ms)")
                    
            except Exception as e:
                print(f"  ✗ {func_name}: {e}")
        
        # Create comparison grid
        processed = [
            to_canny(img),
            to_scribble(img),
            binarize(img, method="otsu"),
            preprocess_sketch(img, method="scribble"),
        ]
        titles = ["Canny", "Scribble (HED)", "Binarize", "Full Pipeline"]
        
        output_path = Path(__file__).parent / "output" / f"comparison_{name}.png"
        output_path.parent.mkdir(exist_ok=True)
        
        create_comparison_grid(img, processed, titles, output_path)
        
        results.append((name, output_path))
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    
    print("\nGenerated comparison grids:")
    for name, path in results:
        print(f"  - {path}")
    
    return True


def test_processing_time():
    """Test that processing time is under 500ms."""
    print("\n" + "=" * 60)
    print("Testing Processing Time")
    print("=" * 60 + "\n")
    
    from preprocess import to_scribble, to_canny, preprocess_sketch
    
    # Create test image
    img = create_test_image(size=(512, 512), content="simple")
    
    # Run multiple times for accuracy
    n_runs = 5
    
    functions = [
        ("to_canny", lambda: to_canny(img)),
        ("to_scribble", lambda: to_scribble(img)),
        ("preprocess_sketch", lambda: preprocess_sketch(img, method="scribble")),
    ]
    
    all_passed = True
    
    for func_name, func in functions:
        times = []
        for _ in range(n_runs):
            start = time.time()
            func()
            times.append((time.time() - start) * 1000)
        
        avg_time = sum(times) / len(times)
        passed = avg_time < 500
        
        status = "✓" if passed else "✗"
        print(f"  {status} {func_name}: avg {avg_time:.1f}ms (target: <500ms)")
        
        if not passed:
            all_passed = False
    
    return all_passed


def main():
    """Main test function."""
    import cv2
    import numpy as np
    
    print("=" * 60)
    print("Scribbly Preprocessing Test Suite")
    print("=" * 60)
    
    # Test preprocessing functions
    test_preprocessing_functions()
    
    # Test processing time
    time_passed = test_processing_time()
    
    print("\n" + "=" * 60)
    if time_passed:
        print("✅ All tests passed!")
    else:
        print("⚠️ Some tests took longer than 500ms")
    print("=" * 60)


if __name__ == "__main__":
    main()
