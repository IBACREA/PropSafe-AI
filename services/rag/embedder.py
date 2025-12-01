from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
from pathlib import Path

from core.logger import get_logger
from core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class Embedder:
    """
    Document embedder using sentence transformers.
    
    Supports multilingual embeddings for Spanish text.
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize embedder with specified model.
        
        Args:
            model_name: HuggingFace model name (default from settings)
        """
        self.model_name = model_name or settings.embedding_model
        logger.info("loading_embedding_model", model=self.model_name)
        
        try:
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(
                "embedding_model_loaded",
                model=self.model_name,
                dimension=self.embedding_dim
            )
        except Exception as e:
            logger.error("embedding_model_load_error", error=str(e))
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text string
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error("embedding_error", error=str(e))
            raise
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of text strings
            batch_size: Batch size for processing
            
        Returns:
            Array of embeddings with shape (n_texts, embedding_dim)
        """
        try:
            logger.info("embedding_batch", n_texts=len(texts), batch_size=batch_size)
            
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100
            )
            
            logger.info("batch_embedding_complete", shape=embeddings.shape)
            return embeddings
            
        except Exception as e:
            logger.error("batch_embedding_error", error=str(e))
            raise
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between -1 and 1
        """
        emb1 = self.embed_text(text1)
        emb2 = self.embed_text(text2)
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        return float(similarity)
    
    def get_embedding_dimension(self) -> int:
        """Get the dimensionality of embeddings."""
        return self.embedding_dim


# Global embedder instance
_embedder_instance = None


def get_embedder() -> Embedder:
    """Get or create global embedder instance."""
    global _embedder_instance
    
    if _embedder_instance is None:
        _embedder_instance = Embedder()
    
    return _embedder_instance
