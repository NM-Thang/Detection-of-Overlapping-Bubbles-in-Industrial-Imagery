"""
Image Preprocessing Utilities for Bubble Detection.
Copied from research/startdist-data-preprocess.ipynb
"""
import cv2
import numpy as np
from PIL import Image


def load_image(path):
    """Load image as grayscale."""
    return cv2.imread(path, cv2.IMREAD_GRAYSCALE)


def load_flat_frame(path):
    """Load flatfield reference image."""
    return load_image(path)


def upscale_nearest(img, scale_factor=2):
    """Upscale image using Nearest Neighbor interpolation."""
    width = int(img.shape[1] * scale_factor)
    height = int(img.shape[0] * scale_factor)
    return cv2.resize(img, (width, height), interpolation=cv2.INTER_NEAREST)


def upscale_lanczos(img, scale_factor=2):
    """Upscale image using Lanczos interpolation."""
    width = int(img.shape[1] * scale_factor)
    height = int(img.shape[0] * scale_factor)
    return cv2.resize(img, (width, height), interpolation=cv2.INTER_LANCZOS4)


def downscale_nearest(img, scale_factor):
    """Downscale image using Nearest Neighbor interpolation."""
    width = int(img.shape[1] / scale_factor)
    height = int(img.shape[0] / scale_factor)
    return cv2.resize(img, (width, height), interpolation=cv2.INTER_NEAREST)


def apply_dog_cl(img, sigma1=1.0, sigma2=20.0, clahe_clip=None):
    """Apply Difference of Gaussians with optional CLAHE."""
    img_float = img.astype(np.float32)
    g1 = cv2.GaussianBlur(img_float, (0, 0), sigma1)
    g2 = cv2.GaussianBlur(img_float, (0, 0), sigma2)
    dog = g1 - g2
    dog_norm = cv2.normalize(dog, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    if clahe_clip is not None and clahe_clip > 0:
        clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=(8, 8))
        return clahe.apply(dog_norm)
    return dog_norm


def apply_flatfield(img, flat):
    """Apply flatfield correction."""
    flat_float = flat.astype(np.float32)
    flat_mean = np.mean(flat_float)
    flat_float[flat_float == 0] = 0.0001  # Avoid div by zero

    img_float = img.astype(np.float32)
    corrected = (img_float / flat_float) * flat_mean
    return np.clip(corrected, 0, 255).astype(np.uint8)


def create_master_flat(image_paths, min_frames=100, progress_callback=None):
    """
    Generate master flat frame from multiple images using median.
    
    Args:
        image_paths: List of image file paths
        min_frames: Minimum number of frames required (default 10)
        progress_callback: Optional callback(current, total) for progress updates
    
    Returns:
        Master flat frame as numpy array (uint8)
    """
    if len(image_paths) < min_frames:
        raise ValueError(f"Need at least {min_frames} images, got {len(image_paths)}")
    
    images = []
    first_img = load_image(image_paths[0])
    if first_img is None:
        raise ValueError(f"Cannot load first image: {image_paths[0]}")
    h, w = first_img.shape
    
    total = len(image_paths)
    for i, path in enumerate(image_paths):
        img = load_image(path)
        if img is None:
            continue
        if img.shape != (h, w):
            img = cv2.resize(img, (w, h))
        images.append(img)
        
        if progress_callback:
            progress_callback(i + 1, total)
    
    stack = np.array(images, dtype=np.uint8)
    flat = np.median(stack, axis=0).astype(np.uint8)
    return flat


def smooth_flat_blur(flat, kernel_size=151):
    """
    Smooth flat frame using strong Gaussian blur.
    Removes residual bubble artifacts from median calculation.
    
    Args:
        flat: Raw flat frame from create_master_flat
        kernel_size: Blur kernel size (should be ~10-20% of image width)
                     Larger = smoother. Must be odd number.
    
    Returns:
        Smoothed flat frame
    """
    # Ensure kernel size is odd
    if kernel_size % 2 == 0:
        kernel_size += 1
    
    return cv2.GaussianBlur(flat, (kernel_size, kernel_size), 0)


def smooth_flat_resize(flat, shrink_factor=30):
    """
    Smooth flat frame using resize trick.
    Shrink to tiny size then upscale back - removes all fine details.
    Preserves aspect ratio to avoid vignetting distortion.
    
    Args:
        flat: Raw flat frame from create_master_flat
        shrink_factor: Factor to divide dimensions by (e.g., 30 → 1920x1080 becomes 64x36)
    
    Returns:
        Smoothed flat frame
    """
    h, w = flat.shape
    # Calculate small size preserving aspect ratio
    small_w = max(w // shrink_factor, 1)
    small_h = max(h // shrink_factor, 1)
    # Shrink (destroys all fine detail like bubbles)
    small = cv2.resize(flat, (small_w, small_h), interpolation=cv2.INTER_AREA)
    # Upscale back with smooth interpolation
    smoothed = cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)
    return smoothed


def generate_flat_frame(image_paths, smooth_method='blur', blur_kernel=151, 
                        shrink_factor=30, progress_callback=None):
    """
    Full pipeline: create master flat and apply smoothing.
    
    Args:
        image_paths: List of image file paths
        smooth_method: 'blur', 'resize', or 'none'
        blur_kernel: Kernel size for blur method
        shrink_factor: Factor to divide dimensions by for resize method
        progress_callback: Optional callback for progress
    
    Returns:
        Smoothed flat frame ready for flatfield correction
    """
    # Step 1: Create raw flat from median
    raw_flat = create_master_flat(image_paths, progress_callback=progress_callback)
    
    # Step 2: Apply smoothing
    if smooth_method == 'blur':
        return smooth_flat_blur(raw_flat, blur_kernel)
    elif smooth_method == 'resize':
        return smooth_flat_resize(raw_flat, shrink_factor)
    else:
        return raw_flat


def scale_stardist_results(labels, details, scale):
    """
    Scale StarDist results back to original image dimensions.
    Called AFTER StarDist prediction, BEFORE RDC.
    """
    if scale <= 1:
        return labels, details
    
    # 1. Scale labels (mask) using Nearest Neighbor
    scaled_labels = downscale_nearest(labels, scale)
    
    # 2. Scale details
    scaled_details = details.copy()
    
    # Scale 'coord' - shape is typically list of (2, N) arrays
    if 'coord' in scaled_details and scaled_details['coord'] is not None:
        scaled_coords = []
        for coord in scaled_details['coord']:
            if coord is not None:
                coord_arr = np.array(coord)
                scaled_coords.append(coord_arr / scale)
            else:
                scaled_coords.append(None)
        scaled_details['coord'] = scaled_coords
    
    # Scale 'points' - shape is typically list of [y, x] pairs
    if 'points' in scaled_details and scaled_details['points'] is not None:
        scaled_points = []
        for pt in scaled_details['points']:
            if pt is not None:
                pt_arr = np.array(pt)
                scaled_points.append(pt_arr / scale)
            else:
                scaled_points.append(None)
        scaled_details['points'] = scaled_points
    
    return scaled_labels, scaled_details


def preprocess_pipeline(img_gray, config):
    """
    Apply preprocessing pipeline in order: Flatfield -> DoG -> Lanczos.
    
    Returns:
        (processed_image, scale_factor)
    """
    result = img_gray.copy()
    scale_factor = 1
    
    # 1. Flatfield Correction
    if config.get('use_flatfield') and config.get('flat_frame') is not None:
        result = apply_flatfield(result, config['flat_frame'])
    
    # 2. Difference of Gaussians
    if config.get('use_dog'):
        sigma1 = config.get('dog_sigma1', 2.0)
        sigma2 = config.get('dog_sigma2', 20.0)
        result = apply_dog_cl(result, sigma1, sigma2)
    
    # 3. Lanczos Upscale
    if config.get('use_lanczos'):
        scale_factor = config.get('lanczos_scale', 2)
        result = upscale_lanczos(result, scale_factor)
    
    return result, scale_factor
