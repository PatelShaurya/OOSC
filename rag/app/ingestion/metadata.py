"""
Metadata extraction and tagging module.

Adds metadata to each chunk:
- document_id: Unique document identifier
- title: Document title
- document_type: law, rule, guideline, form, procedure, faq, other
- section: Section number/title
- page: Page number
- source_url: Original source URL
- language: Document language
- authority: Document authority (government, etc.)
- date_added: When added to knowledge base

Classes:
- MetadataExtractor: Extract metadata from documents
- ChunkMetadata: Dataclass for chunk metadata

Functions:
- add_metadata_to_chunk(): Attach metadata to chunk
- validate_metadata(): Ensure all required fields present
"""
