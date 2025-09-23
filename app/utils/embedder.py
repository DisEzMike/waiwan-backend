from sentence_transformers import SentenceTransformer
from .config import MODEL_NAME

model = SentenceTransformer(MODEL_NAME)

def embed_query(text: str):
    return model.encode([text], normalize_embeddings=True)[0].tolist()