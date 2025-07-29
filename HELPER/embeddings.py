import logging
import os
import json
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


load_dotenv()

class NOMIC_EMBEDDINGS:
    def __init__(self):
        self.embed_model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)
        self.target_dim = 768
        self.project_metadata = []

    def embed_text(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.target_dim), dtype="float32")
        embs = self.embed_model.encode(texts, normalize_embeddings=True)
        return np.array(embs, dtype="float32")



# retriever = NOMIC_EMBEDDINGS()


# news_item = "Government announces new infrastructure project in Gujarat."


# embedding = retriever.embed_text([news_item]) 
# embedding = embedding[0]


# print("Embedding preview:", embedding)