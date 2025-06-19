import numpy as np
import os
from PIL import Image

def is_single_color_image(image_path, threshold=20):
    """
    Check if an image is of a single color by comparing pixels to the average color.
    An image is considered single-colored if more than 50% of pixels are within threshold
    of the average color.
    
    Args:
        image_path (str): Path to the image file
        threshold (int): Threshold value for considering pixels as the same color (0-255)
        
    Returns:
        bool: True if image is not a single color, False if it is a single color
    """
    try:
        img = Image.open(image_path)
        img_array = np.array(img)
        
        if len(img_array.shape) == 3:  # Color image (RGB/RGBA)
            avg_color = np.mean(img_array[:, :, :3], axis=(0,1)).astype(int)
            color_diff = np.abs(img_array[:, :, :3] - avg_color)
            pixels_within_threshold = np.sum(np.all(color_diff <= threshold, axis=2))
            total_pixels = img_array.shape[0] * img_array.shape[1]
            percentage_within_threshold = (pixels_within_threshold / total_pixels) * 100
            return percentage_within_threshold <= 50
            
        elif len(img_array.shape) == 2:  # Grayscale image
            avg_value = np.mean(img_array).astype(int)
            differences = np.abs(img_array - avg_value)
            pixels_within_threshold = np.sum(differences <= threshold)
            total_pixels = img_array.shape[0] * img_array.shape[1]
            percentage_within_threshold = (pixels_within_threshold / total_pixels) * 100
            return percentage_within_threshold <= 50
            
        else:
            return True
            
    except Exception:
        return True 