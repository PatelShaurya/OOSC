"""
Configurability settings for Stage 2 structure-aware chunking.
"""
import os
from dataclasses import dataclass


@dataclass
class ChunkingConfig:
    # Target chunk token estimate (~4 chars per token)
    target_tokens: int = 1000
    max_tokens: int = 1500
    overlap_tokens: int = 100

    @property
    def target_chars(self) -> int:
        return self.target_tokens * 4

    @property
    def max_chars(self) -> int:
        return self.max_tokens * 4

    @property
    def overlap_chars(self) -> int:
        return self.overlap_tokens * 4


DEFAULT_CHUNKING_CONFIG = ChunkingConfig(
    target_tokens=int(os.getenv("RAG_TARGET_TOKENS", "1000")),
    max_tokens=int(os.getenv("RAG_MAX_TOKENS", "1500")),
    overlap_tokens=int(os.getenv("RAG_OVERLAP_TOKENS", "100")),
)
