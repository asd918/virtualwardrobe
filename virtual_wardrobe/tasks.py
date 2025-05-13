import os
import logging
from celery import shared_task
from django.core.files.storage import default_storage
from .ai_utils import (
    preprocess_image,
    extract_features,
    classify_style,
    extract_color_palette,
    get_style_embedding,
    calculate_trend_score
)

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def process_clothing_item(self, item_id):
    """
    Process a clothing item's image and extract AI features.
    This task runs asynchronously to prevent blocking the main thread.
    """
    from .models import ClothingItem
    
    try:
        item = ClothingItem.objects.get(id=item_id)
        item.processing_status = 'processing'
        item.save()

        # Get the image path
        image_path = item.image.path if item.image else None
        if not image_path or not os.path.exists(image_path):
            raise ValueError("Image file not found")

        # Process the image
        processed_image = preprocess_image(image_path)
        if processed_image is None:
            raise ValueError("Image preprocessing failed")

        # Extract features
        features = extract_features(processed_image)
        if features is None:
            raise ValueError("Feature extraction failed")

        # Classify style
        style = classify_style(features)
        if style is None:
            raise ValueError("Style classification failed")

        # Extract color palette
        color_palette = extract_color_palette(processed_image)
        if color_palette is None:
            raise ValueError("Color palette extraction failed")

        # Get style embedding
        style_embedding = get_style_embedding(processed_image)
        if style_embedding is None:
            raise ValueError("Style embedding extraction failed")

        # Calculate trend score
        trend_score = calculate_trend_score(style_embedding)
        if trend_score is None:
            raise ValueError("Trend score calculation failed")

        # Update the item with all extracted features
        item.style = style
        item.color_palette = color_palette
        item.style_embedding = style_embedding
        item.trend_score = trend_score
        item.features = features
        item.processing_status = 'completed'
        item.save()

        logger.info(f"Successfully processed clothing item {item_id}")
        return True

    except Exception as e:
        logger.error(f"Error processing clothing item {item_id}: {str(e)}")
        if item:
            item.processing_status = 'failed'
            item.processing_error = str(e)
            item.save()
        raise 