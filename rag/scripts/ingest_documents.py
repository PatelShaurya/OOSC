"""
Document ingestion script for RAG.

Usage:
python scripts/ingest_documents.py --input data/documents --type law

Processes documents through full pipeline:
Load → Clean → Chunk → Metadata → Embeddings → Store

Arguments:
--input: Input directory or file
--type: Document type (law, form, procedure, etc.)
--language: Document language (en, hi, etc.)
"""
