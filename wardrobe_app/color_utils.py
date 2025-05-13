import numpy as np
import cv2
import logging
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

def generate_color_palette(img, n_colors=5):
    """
    Generate a color palette from an image.
    
    Args:
        img (numpy.ndarray): Preprocessed image
        n_colors (int): Number of colors in the palette
        
    Returns:
        list: List of RGB colors in the palette
    """
    if img is None:
        return []
    
    try:
        # Reshape the image to be a list of pixels
        pixels = img.reshape(-1, 3)
        
        # Cluster the pixel intensities
        clt = KMeans(n_clusters=n_colors)
        clt.fit(pixels)
        
        # Get the colors that are the centroids
        colors = clt.cluster_centers_
        
        # Convert to integers (0-255)
        colors = colors.astype(int).tolist()
        
        return colors
    
    except Exception as e:
        logger.exception(f"Error generating color palette: {e}")
        return []

def is_color_similar(color1, color2, threshold=30):
    """
    Determine if two colors are similar.
    
    Args:
        color1 (list): RGB color 1
        color2 (list): RGB color 2
        threshold (int): Similarity threshold
        
    Returns:
        bool: True if colors are similar, False otherwise
    """
    try:
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        
        distance = np.sqrt((r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2)
        
        return distance < threshold
    
    except Exception as e:
        logger.exception(f"Error comparing colors: {e}")
        return False

def get_color_name(rgb):
    """
    Get the name of a color based on its RGB value.
    This is a simplified implementation with basic color names.
    
    Args:
        rgb (list): RGB color value
        
    Returns:
        str: Name of the color
    """
    try:
        r, g, b = rgb
        
        # Define color ranges (simplified)
        if max(r, g, b) < 50:
            return "Black"
        if min(r, g, b) > 200:
            return "White"
        if r > 200 and g < 100 and b < 100:
            return "Red"
        if r < 100 and g > 200 and b < 100:
            return "Green"
        if r < 100 and g < 100 and b > 200:
            return "Blue"
        if r > 200 and g > 200 and b < 100:
            return "Yellow"
        if r > 200 and g < 100 and b > 200:
            return "Magenta"
        if r < 100 and g > 200 and b > 200:
            return "Cyan"
        if r > 200 and g > 100 and b < 100:
            return "Orange"
        if r > 100 and g < 100 and b > 100:
            return "Purple"
        if r > 100 and g > 100 and b < 100:
            return "Brown"
        
        return "Unknown"
    
    except Exception as e:
        logger.exception(f"Error getting color name: {e}")
        return "Unknown" 