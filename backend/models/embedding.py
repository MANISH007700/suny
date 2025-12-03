from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import logging

logger = logging.getLogger(__name__)

class EmbeddingModel:
    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        """
        Initialize embedding model
        
        Args:
            model_name: HuggingFace model name for embeddings
            
        Note: all-mpnet-base-v2 produces 768-dimensional embeddings
        """
        logger.info(f"Initializing embedding model: {model_name}")
        
        try:
            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
            self.dimension = self.model.get_sentence_embedding_dimension()
            
            logger.info(f"✅ Embedding model loaded successfully")
            logger.info(f"   Model: {model_name}")
            logger.info(f"   Dimension: {self.dimension}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text string
        
        Returns:
            List of floats representing the embedding (dimension: self.dimension)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.dimension
        
        try:
            # Log first time only to avoid spam
            if not hasattr(self, '_logged_single_embed'):
                logger.debug(f"Embedding single text (length: {len(text)} chars)")
                self._logged_single_embed = True
            
            embedding = self.model.encode(text, convert_to_numpy=True)
            result = embedding.tolist()
            
            # Validate embedding
            if len(result) != self.dimension:
                raise ValueError(f"Embedding dimension mismatch: expected {self.dimension}, got {len(result)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error embedding text: {str(e)}")
            logger.error(f"Text preview: {text[:100]}...")
            raise
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of text strings
            batch_size: Batch size for processing
        
        Returns:
            List of embeddings, each of dimension self.dimension
        """
        if not texts:
            logger.warning("Empty text list provided for batch embedding")
            return []
        
        # Filter out empty texts but keep track of indices
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(i)
            else:
                logger.warning(f"Empty text at index {i}, skipping")
        
        if not valid_texts:
            logger.error("No valid texts to embed")
            return [[0.0] * self.dimension] * len(texts)
        
        try:
            logger.info(f"Embedding batch: {len(valid_texts)} texts (batch_size={batch_size})")
            
            # Show statistics about text lengths
            text_lengths = [len(t) for t in valid_texts]
            logger.info(f"Text lengths - Min: {min(text_lengths)}, Max: {max(text_lengths)}, Avg: {sum(text_lengths)//len(text_lengths)}")
            
            # Generate embeddings
            embeddings = self.model.encode(
                valid_texts, 
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(valid_texts) > 10,  # Only show progress for large batches
                convert_to_tensor=False
            )
            
            result = embeddings.tolist()
            
            # Validate embeddings
            if len(result) != len(valid_texts):
                raise ValueError(f"Embedding count mismatch: expected {len(valid_texts)}, got {len(result)}")
            
            for i, emb in enumerate(result):
                if len(emb) != self.dimension:
                    raise ValueError(f"Embedding {i} dimension mismatch: expected {self.dimension}, got {len(emb)}")
            
            logger.info(f"✅ Successfully generated {len(result)} embeddings")
            
            # If we skipped any empty texts, insert zero vectors
            if len(valid_texts) < len(texts):
                full_result = []
                valid_idx = 0
                for i in range(len(texts)):
                    if i in valid_indices:
                        full_result.append(result[valid_idx])
                        valid_idx += 1
                    else:
                        full_result.append([0.0] * self.dimension)
                return full_result
            
            return result
            
        except Exception as e:
            logger.error(f"Error embedding batch: {str(e)}")
            logger.error(f"Batch size: {len(texts)}, Valid texts: {len(valid_texts)}")
            raise
    
    def get_dimension(self) -> int:
        """Return embedding dimension"""
        return self.dimension
    
    def get_model_name(self) -> str:
        """Return the model name being used"""
        return self.model_name
    
    def test_embedding(self, test_text: str = "This is a test sentence.") -> dict:
        """
        Test the embedding model and return diagnostic information
        
        Args:
            test_text: Text to use for testing
            
        Returns:
            Dictionary with test results
        """
        try:
            logger.info("Running embedding model test...")
            
            # Single embedding test
            embedding = self.embed_text(test_text)
            
            # Batch embedding test
            batch_embeddings = self.embed_batch([test_text, "Another test sentence."])
            
            result = {
                "status": "success",
                "model_name": self.model_name,
                "dimension": self.dimension,
                "single_embedding_length": len(embedding),
                "batch_embedding_count": len(batch_embeddings),
                "embedding_sample": embedding[:5],  # First 5 values
                "test_text": test_text
            }
            
            logger.info(f"✅ Embedding test passed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Embedding test failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }