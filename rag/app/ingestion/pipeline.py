"""
Ingestion pipeline orchestrator.

Coordinates: Loader → Cleaner → Chunker → Metadata → Embedder → Vector Store

Workflow:
1. Load document
2. Clean text
3. Split into chunks
4. Add metadata to each chunk
5. Generate embeddings
6. Store in vector database

Classes:
- IngestionPipeline: Main orchestrator
- PipelineConfig: Configuration for ingestion

Functions:
- run_ingestion(): Execute full pipeline
"""
