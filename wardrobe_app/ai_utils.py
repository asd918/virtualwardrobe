import logging
import numpy as np

logger = logging.getLogger(__name__)

def calculate_trend_score(item_features, trend_features):
    """
    Calculate similarity score between an item and current trends.
    
    Args:
        item_features (dict): Features of the clothing item
        trend_features (dict): Features representing current trends
        
    Returns:
        float: Trend score between 0 and 1
    """
    try:
        if not item_features or not trend_features:
            return 0.5  # Neutral score if no features
            
        # Calculate similarity based on available features
        # This is a simplified implementation
        score = 0
        weight_sum = 0
        
        # Compare colors if available
        if 'colors' in trend_features and 'avg_color' in item_features:
            color_score = _color_similarity(item_features['avg_color'], trend_features['colors'])
            score += color_score * 0.4  # Color has high weight
            weight_sum += 0.4
        
        # Compare style if available
        if 'styles' in trend_features and 'style' in item_features:
            style_score = _style_similarity(item_features['style'], trend_features['styles'])
            score += style_score * 0.3  # Style has medium-high weight
            weight_sum += 0.3
        
        # Compare patterns if available
        if 'patterns' in trend_features and 'pattern' in item_features:
            pattern_score = _pattern_similarity(item_features['pattern'], trend_features['patterns'])
            score += pattern_score * 0.2  # Pattern has medium weight
            weight_sum += 0.2
            
        # Compare other features
        if 'fabric_types' in trend_features and 'fabric_type' in item_features:
            fabric_score = _fabric_similarity(item_features['fabric_type'], trend_features['fabric_types'])
            score += fabric_score * 0.1  # Fabric has lower weight
            weight_sum += 0.1
        
        # Normalize score
        return score / weight_sum if weight_sum > 0 else 0.5
    
    except Exception as e:
        logger.exception(f"Error calculating trend score: {e}")
        return 0.5

def _color_similarity(item_color, trend_colors):
    """
    Calculate color similarity between an item and trending colors.
    
    Args:
        item_color (list): RGB color of the item
        trend_colors (list): List of trending RGB colors
        
    Returns:
        float: Similarity score between 0 and 1
    """
    try:
        # If no colors to compare, return neutral score
        if not item_color or not trend_colors:
            return 0.5
        
        # Calculate closest distance to a trending color
        min_distance = float('inf')
        for trend_color in trend_colors:
            # Calculate Euclidean distance in RGB space
            distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(item_color, trend_color)))
            min_distance = min(min_distance, distance)
        
        # Convert distance to similarity score (0 to 1)
        # Maximum reasonable distance in RGB space is 255*sqrt(3) ≈ 442
        max_distance = 442
        similarity = 1 - (min_distance / max_distance)
        
        return max(0, min(1, similarity))
    
    except Exception as e:
        logger.exception(f"Error calculating color similarity: {e}")
        return 0.5

def _style_similarity(item_style, trend_styles):
    """
    Calculate style similarity between an item and trending styles.
    
    Args:
        item_style (str): Style of the item
        trend_styles (list): List of trending styles with weights
        
    Returns:
        float: Similarity score between 0 and 1
    """
    try:
        # If no style information, return neutral score
        if not item_style or not trend_styles:
            return 0.5
        
        # Check if item style matches a trending style
        for trend_style, weight in trend_styles:
            if item_style.lower() == trend_style.lower():
                return weight  # Return the trend weight as score
            
        # Check for partial matches or similar styles
        for trend_style, weight in trend_styles:
            if trend_style.lower() in item_style.lower() or item_style.lower() in trend_style.lower():
                return weight * 0.7  # Partial match gets 70% of weight
                
        # No match found
        return 0.3  # Low score but not zero for non-trending styles
    
    except Exception as e:
        logger.exception(f"Error calculating style similarity: {e}")
        return 0.5

def _pattern_similarity(item_pattern, trend_patterns):
    """
    Calculate pattern similarity between an item and trending patterns.
    
    Args:
        item_pattern (str): Pattern of the item
        trend_patterns (list): List of trending patterns with weights
        
    Returns:
        float: Similarity score between 0 and 1
    """
    try:
        # If no pattern information, return neutral score
        if not item_pattern or not trend_patterns:
            return 0.5
        
        # Check if item pattern matches a trending pattern
        for trend_pattern, weight in trend_patterns:
            if item_pattern.lower() == trend_pattern.lower():
                return weight  # Return the trend weight as score
                
        # Check for partial matches
        for trend_pattern, weight in trend_patterns:
            if trend_pattern.lower() in item_pattern.lower() or item_pattern.lower() in trend_pattern.lower():
                return weight * 0.7  # Partial match gets 70% of weight
                
        # No match found
        return 0.3  # Low score but not zero for non-trending patterns
    
    except Exception as e:
        logger.exception(f"Error calculating pattern similarity: {e}")
        return 0.5

def _fabric_similarity(item_fabric, trend_fabrics):
    """
    Calculate fabric similarity between an item and trending fabrics.
    
    Args:
        item_fabric (str): Fabric of the item
        trend_fabrics (list): List of trending fabrics with weights
        
    Returns:
        float: Similarity score between 0 and 1
    """
    try:
        # If no fabric information, return neutral score
        if not item_fabric or not trend_fabrics:
            return 0.5
        
        # Check if item fabric matches a trending fabric
        for trend_fabric, weight in trend_fabrics:
            if item_fabric.lower() == trend_fabric.lower():
                return weight  # Return the trend weight as score
                
        # Check for partial matches
        for trend_fabric, weight in trend_fabrics:
            if trend_fabric.lower() in item_fabric.lower() or item_fabric.lower() in trend_fabric.lower():
                return weight * 0.7  # Partial match gets 70% of weight
                
        # No match found
        return 0.3  # Low score but not zero for non-trending fabrics
    
    except Exception as e:
        logger.exception(f"Error calculating fabric similarity: {e}")
        return 0.5

def get_style_embedding(style_text):
    """
    Generate a simple vector embedding for a style description.
    This is a simplified implementation - in a real application,
    you would use a proper NLP model or word embeddings.
    
    Args:
        style_text (str): Style description text
        
    Returns:
        list: Numerical embedding vector
    """
    try:
        if not style_text:
            return [0.0] * 10  # Default zero embedding
            
        # Simple implementation - count occurrences of key style terms
        style_terms = {
            'casual': 0,
            'formal': 1,
            'business': 2,
            'sporty': 3,
            'athletic': 3,  # Map to same dimension as sporty
            'vintage': 4,
            'retro': 4,  # Map to same dimension as vintage
            'bohemian': 5,
            'boho': 5,  # Map to same dimension as bohemian
            'minimalist': 6,
            'clean': 6,  # Map to same dimension as minimalist
            'streetwear': 7,
            'urban': 7,  # Map to same dimension as streetwear
            'elegant': 8,
            'luxury': 8,  # Map to same dimension as elegant
            'trendy': 9,
            'modern': 9   # Map to same dimension as trendy
        }
        
        # Initialize embedding vector
        embedding = [0.0] * 10
        
        # Tokenize text (simplified)
        tokens = style_text.lower().split()
        
        # Update embedding based on terms
        for token in tokens:
            for term, index in style_terms.items():
                if term in token:  # Check if term is part of token
                    embedding[index] += 1.0
        
        # Normalize to unit length if not zero
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = [e / norm for e in embedding]
            
        return embedding
    
    except Exception as e:
        logger.exception(f"Error generating style embedding: {e}")
        return [0.0] * 10 