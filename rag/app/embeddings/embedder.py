"""
Embedding component using BAAI/bge-m3 producing normalized 1024-dimensional vectors.
"""
from typing import List, Union, Optional
import numpy as np
import torch
from sentence_transformers import SentenceTransformer


class BGEEmbedder:
    """
    Singleton-style embedder wrapping BAAI/bge-m3.
    Generates 1024-dimensional L2-normalized embeddings for legal text chunks and queries.
    """

    DEFAULT_MODEL_NAME = "BAAI/bge-m3"
    EMBEDDING_DIM = 1024

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        device: str = "auto",
        batch_size: int = 16,
        normalize: bool = True
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.normalize = normalize

        # Automatic CPU / CUDA detection if device is 'auto'
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"Loading embedding model '{self.model_name}' on device '{self.device}'...")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        print("Embedding model loaded successfully.")

    def encode(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """
        Generates 1024-dimensional normalized embeddings for a list of text strings in batches.
        Safely handles empty or whitespace-only strings.
        """
        if not texts:
            return []

        effective_batch_size = batch_size or self.batch_size
        
        # Preprocess texts to handle empty strings safely
        processed_texts = []
        empty_indices = set()
        for idx, text in enumerate(texts):
            clean_t = text.strip() if text else ""
            if not clean_t:
                empty_indices.add(idx)
                processed_texts.append(" ")  # Dummy non-empty string for model pass
            else:
                processed_texts.append(clean_t)

        # Generate embeddings via sentence-transformers
        raw_embeddings = self.model.encode(
            processed_texts,
            batch_size=effective_batch_size,
            show_progress_bar=False,
            normalize_embeddings=self.normalize
        )

        # Convert to numpy array if not already
        if isinstance(raw_embeddings, torch.Tensor):
            embeddings_np = raw_embeddings.cpu().numpy()
        else:
            embeddings_np = np.array(raw_embeddings, dtype=np.float32)

        # Ensure L2 normalization if required and not already normalized
        result: List[List[float]] = []
        for idx in range(len(texts)):
            if idx in empty_indices:
                # Return zero vector for empty strings
                result.append([0.0] * self.EMBEDDING_DIM)
            else:
                vec = embeddings_np[idx]
                if self.normalize:
                    norm = np.linalg.norm(vec)
                    if norm > 0:
                        vec = vec / norm
                result.append(vec.tolist())

        return result

    def encode_single(self, text: str) -> List[float]:
        """Convenience method to encode a single text string."""
        res = self.encode([text])
        return res[0] if res else [0.0] * self.EMBEDDING_DIM
