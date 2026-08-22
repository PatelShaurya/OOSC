"""
RAG service configuration.

Environment variables to set:
- SUPABASE_URL: Supabase project URL
- SUPABASE_KEY: Supabase API key
- ANTHROPIC_API_KEY: Claude API key
- EMBEDDING_MODEL: Sentence transformer model name
- LLM_MODEL: Claude model name
- CHUNK_SIZE: Size of text chunks (tokens)
- CHUNK_OVERLAP: Overlap between chunks (tokens)
- TOP_K: Default number of retrieved results
- REQUEST_TIMEOUT: API request timeout (seconds)

Classes:
- Settings: Pydantic settings with environment variable loading
"""
