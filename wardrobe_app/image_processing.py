import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)

def preprocess_image(image_path):
    """
    Preprocess an image for feature extraction.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        numpy.ndarray: Preprocessed image
    """
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Failed to load image: {image_path}")
            return None
        
        # Resize to a standard size
        img = cv2.resize(img, (224, 224))
        
        # Convert to RGB if it's in BGR
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        return img
    
    except Exception as e:
        logger.exception(f"Error preprocessing image: {e}")
        return None

def extract_features(img):
    """
    Extract features from an image.
    
    Args:
        img (numpy.ndarray): Preprocessed image
        
    Returns:
        dict: Extracted features
    """
    if img is None:
        return {}
    
    try:
        # Simple feature extraction (can be replaced with more advanced methods)
        # Calculate average color
        avg_color = np.mean(img, axis=(0, 1)).tolist()
        
        # Calculate dominant colors (simplified)
        pixels = img.reshape(-1, 3)
        pixels = np.float32(pixels)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
        k = 5  # Number of clusters (dominant colors)
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Convert to uint8 and to python list
        dominant_colors = centers.astype(np.uint8).tolist()
        
        # Extract histogram features
        hist_features = []
        for i in range(3):  # For each channel
            hist = cv2.calcHist([img], [i], None, [8], [0, 256])
            hist = cv2.normalize(hist, hist).flatten().tolist()
            hist_features.extend(hist)
        
        features = {
            'avg_color': avg_color,
            'dominant_colors': dominant_colors,
            'histogram': hist_features
        }
        
        return features
    
    except Exception as e:
        logger.exception(f"Error extracting features: {e}")
        return {}

def classify_style(features):
    """
    Classify the style of clothing based on extracted features.
    
    Args:
        features (dict): Extracted features from an image
        
    Returns:
        str: Classified style
    """
    if not features:
        return None
    
    try:
        # This is a simplified style classification
        # In a real application, this would be done with a proper machine learning model
        
        # Extract dominant colors
        dominant_colors = features.get('dominant_colors', [])
        if not dominant_colors:
            return None
        
        # Simple rule-based classification based on dominant colors
        # These are very simplified rules for example purposes
        bright_colors = 0
        dark_colors = 0
        neutral_colors = 0
        
        for color in dominant_colors:
            r, g, b = color
            
            brightness = (0.299 * r + 0.587 * g + 0.114 * b)
            
            if brightness > 200:  # Bright
                bright_colors += 1
            elif brightness < 100:  # Dark
                dark_colors += 1
            else:  # Neutral
                neutral_colors += 1
                
            # Check if color is close to certain predefined colors
            
        # Determine style based on color distribution
        if bright_colors > max(dark_colors, neutral_colors):
            return 'Casual'
        elif dark_colors > max(bright_colors, neutral_colors):
            return 'Formal'
        else:
            return 'Business Casual'
            
    except Exception as e:
        logger.exception(f"Error classifying style: {e}")
        return None 