import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def process_clothing_item(item_id):
    """
    Process a clothing item for image analysis.
    This is a simplified version of what would normally be a Celery task.
    
    Args:
        item_id (int): ID of the ClothingItem to process
        
    Returns:
        bool: True if processing succeeded, False otherwise
    """
    try:
        # Import here to avoid circular imports
        from .models import ClothingItem
        from .image_processing import preprocess_image, extract_features, classify_style
        from .color_utils import generate_color_palette
        
        # Get the clothing item
        item = ClothingItem.objects.get(id=item_id)
        
        # Update processing status
        item.processing_status = 'processing'
        item.save(update_fields=['processing_status'])
        
        # Process image if available
        if item.image:
            # Extract features and classify style
            img = preprocess_image(item.image.path)
            if img is not None:
                features = extract_features(img)
                style = classify_style(features)
                
                # Generate color palette
                color_palette = generate_color_palette(img)
                
                # Update item with extracted information
                item.style = style
                item.color_palette = color_palette
                item.features = features
                item.processing_status = 'completed'
                item.save()
                
                logger.info(f"Successfully processed clothing item {item_id}")
                return True
            else:
                item.processing_status = 'failed'
                item.processing_error = "Failed to process image"
                item.save(update_fields=['processing_status', 'processing_error'])
                logger.error(f"Failed to process image for clothing item {item_id}")
                return False
        else:
            # No image to process
            item.processing_status = 'completed'
            item.save(update_fields=['processing_status'])
            logger.info(f"No image to process for clothing item {item_id}")
            return True
            
    except ClothingItem.DoesNotExist:
        logger.error(f"Clothing item {item_id} does not exist")
        return False
    except Exception as e:
        logger.exception(f"Error processing clothing item {item_id}: {e}")
        
        # Try to update the item status if possible
        try:
            item = ClothingItem.objects.get(id=item_id)
            item.processing_status = 'failed'
            item.processing_error = str(e)[:255]  # Limit error message length
            item.save(update_fields=['processing_status', 'processing_error'])
        except:
            pass
            
        return False 