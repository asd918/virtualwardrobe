import torch
from transformers import CLIPModel, CLIPTokenizer
from sklearn.cluster import KMeans
import numpy as np

class StyleProfileGenerator:
    def __init__(self):
        self.model_name = "openai/clip-base-patch32"
        self.model = CLIPModel.from_pretrained(self.model_name)
        self.tokenizer = CLIPTokenizer.from_pretrained(self.model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = self.model.to(self.device)

    def get_style_embedding(self, text):
        """
        Generates a style embedding for a given text using the CLIP model.
        """
        inputs = self.tokenizer([text], padding=True, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state[:, 0, :]  # Extract embedding for the first token
        return embeddings.cpu().numpy().flatten()

    def categorize_style(self, embeddings, n_clusters=5):
        """
        Categorizes style embeddings into style categories using K-means clustering.
        """
        kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=10)
        kmeans.fit(embeddings)
        return kmeans.labels_

    def learn_preferences(self, user_feedback, embeddings):
        """
        Adapts to user feedback to learn style preferences.
        (This is a placeholder - replace with your preference learning algorithm)
        """
        # Implement your preference learning algorithm here
        # This could involve updating weights based on user feedback
        # or using a more sophisticated machine learning model
        return None
