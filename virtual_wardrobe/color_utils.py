import cv2
import numpy as np
from sklearn.cluster import KMeans
import webcolors

def extract_dominant_colors(image_path, k=5):
    """
    Identifies and extracts dominant colors from an image using K-means clustering.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Could not read image. Please check the file path.")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.reshape((img.shape[0] * img.shape[1], 3))

    kmeans = KMeans(n_clusters=k, random_state=0, n_init=10)
    kmeans.fit(img)

    dominant_colors = kmeans.cluster_centers_.astype(int)
    return dominant_colors

def closest_colour(requested_colour):
    min_colours = {}
    for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_colour[0]) ** 2
        gd = (g_c - requested_colour[1]) ** 2
        bd = (b_c - requested_colour[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]

def get_colour_name(requested_colour):
    try:
        closest_name = webcolors.rgb_to_name(requested_colour)
    except ValueError:
        closest_name = closest_colour(requested_colour)
    return closest_name

def generate_color_palette(image_path, k=5):
    """
    Extracts dominant colors and maps them to human-readable color names to create a color palette.
    """
    dominant_colors = extract_dominant_colors(image_path, k)
    color_palette = []
    for color in dominant_colors:
        color_name = get_colour_name(color)
        color_palette.append(color_name)
    return color_palette
