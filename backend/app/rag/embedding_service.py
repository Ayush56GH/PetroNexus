"""
PetroNexus Local Embedding Service (BAAI/bge-small-en-v1.5)
Generates 384-dimensional normalized vector embeddings locally.
Zero external API key required.
"""
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.app.config import settings
from backend.app.utils.logger import logger

class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._model = None
        return cls._instance

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info(f"Loading local embedding model: {settings.EMBEDDING_MODEL} (dim: {settings.EMBEDDING_DIMENSION})...")
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Local embedding model loaded successfully.")
        return self._model

    def embed_query(self, query: str) -> List[float]:
        """
        Generates a 384-dimensional normalized embedding for a search query.
        """
        model = self._get_model()
        vec = model.encode(query, normalize_embeddings=True)
        return vec.tolist()

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Generates 384-dimensional normalized embeddings for a list of document chunks.
        """
        if not documents:
            return []
        model = self._get_model()
        vecs = model.encode(documents, normalize_embeddings=True, show_progress_bar=False)
        return vecs.tolist()

embedding_service = EmbeddingService()
