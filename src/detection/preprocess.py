"""
SAR Preprocessing module for SagarDrishti.
Applies speckle filtering and normalizes backscatter intensities.
"""

import numpy as np
import cv2

def preprocess_sar(image: np.ndarray) -> np.ndarray:
    """
    Applies speckle denoising and normalizes backscatter intensity.
    
    Args:
        image: numpy.ndarray of shape (H, W, C) representing SAR channels
        
    Returns:
        Denoised and normalized image array of same shape
    """
    if image.size == 0:
        return image
        
    img = image.copy().astype(np.float32)
    
    # Process each band separately (usually VV and VH)
    for c in range(img.shape[-1]):
        band = img[..., c]
        
        # 1. Normalize band to [0, 255] for OpenCV operations
        min_val, max_val = band.min(), band.max()
        if max_val > min_val:
            scaled = ((band - min_val) / (max_val - min_val) * 255.0).astype(np.uint8)
        else:
            scaled = np.zeros_like(band, dtype=np.uint8)
            
        # 2. Speckle Denoising using Bilateral Filter or Gaussian Blur
        # Bilateral filter preserves edges (like oil spill boundary) while removing speckles
        denoised = cv2.bilateralFilter(scaled, d=5, sigmaColor=50, sigmaSpace=50)
        
        # 3. Convert back to float [0, 1]
        img[..., c] = denoised.astype(np.float32) / 255.0
        
    return img
