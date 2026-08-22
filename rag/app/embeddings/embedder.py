"""
Embedding generation module.

Model: sentence-transformers/multilingual-MiniLM-L12-v2 (supports EN, HI, Hinglish)
Alternative: sentence-transformers/all-MiniLM-L6-v2 (English only)

Usage:
- Same model for documents AND queries for consistency
- Returns vector embeddings as list of floats

Classes:
- Embedder: Embedding generation wrapper

Functions:
- embed(): Generate embedding for text
- embed_batch(): Generate embeddings for multiple texts
- get_model_name(): Return current model name
"""
