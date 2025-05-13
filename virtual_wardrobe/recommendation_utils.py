from .models import ClothingItem, Outfit, UserProfile
from django.db.models import F
import random
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def calculate_compatibility_score(outfit):
    """
    Calculates a compatibility score for an outfit based on item attributes.
    (This is a placeholder - replace with your compatibility scoring algorithm)
    """
    # Example: Award points for matching categories and seasons
    score = 0
    items = outfit.items.all()
    if not items:
        return 0  # No score if no items in the outfit

    # Get the first item's category and season for comparison
    first_item = items.first()
    category = first_item.category
    season = first_item.season

    for item in items:
        if item.category == category:
            score += 1
        if item.season == season:
            score += 1

    # Normalize the score based on the number of items
    score /= len(items)
    return score

def generate_outfit_combinations(user, occasion=None):
    """
    Generates outfit combinations based on user's wardrobe and occasion.
    (This is a placeholder - replace with your outfit generation algorithm)
    """
    # Get all clothing items for the user
    items = list(ClothingItem.objects.filter(user=user))
    if not items:
        return []  # No outfits if no items in the wardrobe

    # Filter items by occasion if provided
    if occasion:
        items = [item for item in items if occasion in item.occasions]

    # Generate a random outfit combination (for demonstration purposes)
    num_items = len(items)
    if num_items < 3:
        return []  # Need at least 3 items for an outfit

    # Select 3 random items
    outfit_items = random.sample(items, 3)

    # Create a new outfit
    outfit = Outfit.objects.create(user=user, name="Suggested Outfit")
    outfit.items.set(outfit_items)

    return outfit

def personalize_recommendations(user, outfits):
    """
    Personalizes outfit recommendations based on user preferences.
    (This is a placeholder - replace with your personalization algorithm)
    """
    # Example: Boost score for outfits with preferred colors
    try:
        user_profile = user.profile
        preferred_colors = user_profile.preferred_colors.split(',') if user_profile.preferred_colors else []
    except UserProfile.DoesNotExist:
        return outfits  # No personalization if no profile

    for outfit in outfits:
        score_boost = 0
        for item in outfit.items.all():
            if item.color in preferred_colors:
                score_boost += 0.1  # Small boost for preferred color
        outfit.compatibility_score = F('compatibility_score') + score_boost
        outfit.save()

    return outfits

def match_occasion(outfits, occasion):
    """
    Suggests outfits suitable for a specific occasion.
    (This is a placeholder - replace with your occasion matching algorithm)
    """
    # Filter outfits by occasion
    suitable_outfits = []
    for outfit in outfits:
        for item in outfit.items.all():
            if occasion in item.occasions:
                suitable_outfits.append(outfit)
                break  # Avoid adding the same outfit multiple times

    return suitable_outfits


def get_similar_items_for_item(target_item, user, n=5):
    """
    Recommends similar items based on category, color, season, and occasions using a pandas DataFrame and cosine similarity.
    Incorporates user preferences.
    """
    items = ClothingItem.objects.filter(user=user)

    # Get user preferences
    try:
        user_profile = user.profile
        preferred_colors = user_profile.preferred_colors.split(',') if user_profile.preferred_colors else []
        preferred_occasions = user_profile.preferred_occasions.split(',') if user_profile.preferred_occasions else []
    except UserProfile.DoesNotExist:
        preferred_colors = []
        preferred_occasions = []

    # Create a list of dictionaries, where each dictionary represents an item's features
    item_features = []
    item_list = list(items) # Convert queryset to list for indexing
    for item in item_list:
        features = {
            'id': item.id, # Keep track of item id
            'category': item.category.name if item.category else 'None',
            'color': item.color,
            'season': item.season,
            'occasions': ' '.join(item.occasions),
        }
        item_features.append(features)

    # Create a pandas DataFrame from the list of item features
    df = pd.DataFrame(item_features)

    # If the DataFrame is empty or has only one item, return an empty list
    if df.empty or len(df) < 2:
        return []

    # One-hot encode categorical features
    df_encoded = pd.get_dummies(df.drop(columns=['id']), columns=['category', 'color', 'season', 'occasions'])

    # Calculate cosine similarity
    cosine_sim = cosine_similarity(df_encoded)

    # Get the index of the current item in the DataFrame
    try:
        current_item_index = df[df['id'] == target_item.id].index[0]
    except IndexError:
        # If the current item is not in the DataFrame (shouldn't happen if target_item belongs to user), return empty list
        return []

    # Get the similarity scores for the current item
    sim_scores = list(enumerate(cosine_sim[current_item_index]))

    # Sort the items by similarity score
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get the top n most similar items (excluding the current item)
    sim_scores = sim_scores[1:n+1]

    # Get the indices of the similar items in the original item_list
    similar_item_indices = [i[0] for i in sim_scores]

    # Retrieve the actual ClothingItem objects using the original list
    similar_items = [item_list[i] for i in similar_item_indices]

    # Apply user preferences (color filtering)
    # Note: Occasion preference filtering might be better integrated into the similarity calculation or as a separate step
    filtered_items = []
    for item in similar_items:
        # Check if preferred_colors is empty OR item's color is in preferred_colors
        if not preferred_colors or item.color in preferred_colors:
            filtered_items.append(item)

    return filtered_items
