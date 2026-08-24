import os
import hashlib
from typing import List, Union, Optional
import numpy as np

class BGEEmbedder:
    """
    Embedder wrapping BAAI models or Gemini API / Lightweight fallback.
    Generates normalized embeddings for legal text chunks and queries.
    """

    DEFAULT_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: str = "auto",
        batch_size: int = 16,
        normalize: bool = True
    ):
        self.model_name = model_name or self.DEFAULT_MODEL_NAME
        self.batch_size = batch_size
        self.normalize = normalize
        self.model = None

        disable_local_torch = os.getenv("DISABLE_LOCAL_TORCH", "false").lower() in ("true", "1", "yes")

        if not disable_local_torch:
            try:
                import torch
                from sentence_transformers import SentenceTransformer

                if device == "auto":
                    self.device = "cuda" if torch.cuda.is_available() else "cpu"
                else:
                    self.device = device

                print(f"Loading local embedding model '{self.model_name}' on device '{self.device}'...")
                self.model = SentenceTransformer(self.model_name, device=self.device)
                print("Embedding model loaded successfully.")
            except Exception as exc:
                print(f"Warning: Could not load local PyTorch embedder ({exc}). Falling back to API/lightweight embedder.")
                self.model = None
        else:
            print("Local PyTorch embedder disabled via DISABLE_LOCAL_TORCH environment variable.")

    def _fallback_hash_encode(self, text: str) -> List[float]:
        """Generates a deterministic L2-normalized pseudo-embedding vector for low memory mode."""
        dim = self.EMBEDDING_DIM
        clean_text = text.strip().lower() if text else ""
        if not clean_text:
            return [0.0] * dim

        vec = np.zeros(dim, dtype=np.float32)
        words = clean_text.split()
        for word in words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            val = ((h >> 8) % 100) / 50.0 - 1.0
            vec[idx] += val

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def encode(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """
        Generates 1024-dimensional normalized embeddings for a list of text strings in batches.
        Safely handles empty or whitespace-only strings.
        """
        if not texts:
            return []

        if self.model is None:
            return [self._fallback_hash_encode(t) for t in texts]

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
