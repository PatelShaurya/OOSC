"""
Document chunking module.

MVP Version: Naive chunking (every N tokens)
Future: Structure-aware chunking (respect legal sections)

Preserves: chunk boundaries, overlaps for context

Classes:
- NaiveChunker: Simple token-based chunking
- LegalDocumentChunker: Structure-aware chunking (Phase 2)

Functions:
- chunk(): Main chunking function
- extract_sections(): Detect legal sections
- chunk_section(): Split section into logical chunks
"""
