"""
Scribbly Sketch Preprocessing Module

Image preprocessing functions for converting sketches to ControlNet conditioning images.
Includes edge detection (Canny, HED), background removal, contrast enhancement, and normalization.
"""

import logging
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def to_canny(
    image: Image.Image,
    low_threshold: int = 50,
    high_threshold: int = 200,
) -> Image.Image:
    """
    Apply Canny edge detection to convert sketch to edge map.
    
    Args:
        image: Input PIL Image
        low_threshold: Lower threshold for Canny edge detection
        high_threshold: Upper threshold for Canny edge detection
        
    Returns:
        PIL Image with edge map (white edges on black background)
    """
    # Convert PIL to numpy
    img_array = np.array(image)
    
    # Convert to grayscale if needed
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply Canny edge detection
    edges = cv2.Canny(blurred, low_threshold, high_threshold)
    
    # Invert: white edges on black background for ControlNet
    edges = 255 - edges
    
    logger.debug(f"Canny edge detection: {image.size} -> {edges.shape}")
    
    return Image.fromarray(edges)


def to_scribble(image: Image.Image) -> Image.Image:
    """
    Apply HED (Holistically-Nested Edge Detection) for soft edge detection.
    Best for child drawings - captures rough, sketchy lines.
    
    Args:
        image: Input PIL Image
        
    Returns:
        PIL Image with soft edge map
    """
    try:
        from controlnet_aux import HEDdetector
        
        hed = HEDdetector.from_pretrained("lllyasviel/Annotators")
        result = hed(image)
        
        logger.debug(f"HED scribble detection: {image.size} -> {result.size}")
        return result
        
    except ImportError:
        logger.warning("controlnet_aux not installed, falling back to Canny")
        return to_canny(image)


def to_hed(image: Image.Image) -> Image.Image:
    """
    Alias for to_scribble - HED-based edge detection.
    
    Args:
        image: Input PIL Image
        
    Returns:
        PIL Image with HED edge map
    """
    return to_scribble(image)


def remove_background(
    image: Image.Image,
    alpha_matting: bool = True,
    alpha_matting_foreground_threshold: int = 240,
    alpha_matting_background_threshold: int = 10,
) -> Image.Image:
    """
    Remove background from image using rembg library.
    
    Args:
        image: Input PIL Image
        alpha_matting: Enable foreground/background separation
        alpha_matting_foreground_threshold: Threshold for foreground
        alpha_matting_background_threshold: Threshold for background
        
    Returns:
        PIL Image with transparent background
    """
    try:
        from rembg import remove
        
        result = remove(
            image,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
            alpha_matting_background_threshold=alpha_matting_background_threshold,
        )
        
        logger.debug(f"Background removal: {image.size} -> {result.size}")
        return result
        
    except ImportError:
        logger.warning("rembg not installed, returning original image")
        return image


def normalize_size(
    image: Image.Image,
    max_size: int = 512,
    maintain_aspect: bool = True,
) -> Image.Image:
    """
    Resize image while maintaining aspect ratio.
    
    Args:
        image: Input PIL Image
        max_size: Maximum width or height
        maintain_aspect: If True, maintain aspect ratio; otherwise, resize to exact max_size x max_size
        
    Returns:
        Resized PIL Image
    """
    width, height = image.size
    
    if maintain_aspect:
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
    else:
        new_width = max_size
        new_height = max_size
    
    # Resize with high-quality resampling
    result = image.resize((new_width, new_height), Image.LANCZOS)
    
    logger.debug(f"Normalize size: {width}x{height} -> {new_width}x{new_height}")
    
    return result


def auto_enhance_contrast(image: Image.Image) -> Image.Image:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to enhance
    faint pencil lines in drawings.
    
    Args:
        image: Input PIL Image
        
    Returns:
        PIL Image with enhanced contrast
    """
    # Convert PIL to numpy
    img_array = np.array(image)
    
    # Convert to LAB color space
    lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
    
    # Apply CLAHE to the L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    
    # Convert back to RGB
    result_array = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    
    result = Image.fromarray(result_array)
    
    logger.debug(f"Contrast enhancement: {image.size}")
    
    return result


def denoise(image: Image.Image, kernel_size: int = 3) -> Image.Image:
    """
    Apply denoising to clean up noisy sketches.
    
    Args:
        image: Input PIL Image
        kernel_size: Size of the Gaussian kernel (must be odd)
        
    Returns:
        Denoised PIL Image
    """
    # Ensure kernel size is odd
    if kernel_size % 2 == 0:
        kernel_size += 1
    
    # Convert PIL to numpy
    img_array = np.array(image)
    
    # Apply denoising
    if len(img_array.shape) == 3:
        # Color image
        result = cv2.fastNlMeansDenoisingColored(img_array, None, 10, 10, 7, 21)
    else:
        # Grayscale
        result = cv2.fastNlMeansDenoising(img_array, None, 10, 7, 21)
    
    logger.debug(f"Denoising: {image.size}")
    
    return Image.fromarray(result)


def binarize(
    image: Image.Image,
    threshold: int = 128,
    method: str = "otsu",
) -> Image.Image:
    """
    Convert image to binary (black and white).
    
    Args:
        image: Input PIL Image
        threshold: Fixed threshold value (used if method is 'fixed')
        method: Binarization method - 'fixed', 'otsu', or 'adaptive'
        
    Returns:
        Binary PIL Image
    """
    # Convert PIL to numpy
    img_array = np.array(image)
    
    # Convert to grayscale if needed
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Apply binarization
    if method == "otsu":
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif method == "adaptive":
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
    else:  # fixed
        _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    
    logger.debug(f"Binarization ({method}): {image.size}")
    
    return Image.fromarray(binary)


def preprocess_sketch(
    image: Image.Image,
    method: str = "scribble",
    enhance_contrast: bool = True,
    normalize: bool = True,
    max_size: int = 512,
) -> Image.Image:
    """
    Complete preprocessing pipeline for sketches.
    
    Applies enhancement, edge detection, and normalization in sequence.
    
    Args:
        image: Input PIL Image
        method: Edge detection method - 'scribble', 'canny', or 'hed'
        enhance_contrast: Whether to apply CLAHE enhancement
        normalize: Whether to normalize image size
        max_size: Maximum image dimension
        
    Returns:
        Preprocessed PIL Image ready for ControlNet
    """
    logger.info(f"Preprocessing sketch with method: {method}")
    
    # Step 1: Enhance contrast if enabled
    if enhance_contrast:
        image = auto_enhance_contrast(image)
    
    # Step 2: Apply edge detection
    if method == "canny":
        result = to_canny(image)
    elif method in ("hed", "scribble"):
        result = to_scribble(image)
    else:
        raise ValueError(f"Unknown preprocessing method: {method}")
    
    # Step 3: Normalize size if enabled
    if normalize:
        result = normalize_size(result, max_size=max_size)
    
    logger.info(f"Preprocessing complete: {image.size} -> {result.size}")
    
    return result


def get_preprocessor(method: str = "scribble"):
    """
    Get a preprocessor function by name.
    
    Args:
        method: Preprocessing method name
        
    Returns:
        Preprocessor function
    """
    methods = {
        "scribble": to_scribble,
        "hed": to_hed,
        "canny": to_canny,
        "contrast": auto_enhance_contrast,
        "normalize": normalize_size,
        "denoise": denoise,
        "binarize": binarize,
    }
    
    if method not in methods:
        raise ValueError(f"Unknown method: {method}. Available: {list(methods.keys())}")
    
    return methods[method]
