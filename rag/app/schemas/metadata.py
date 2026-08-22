"""
Metadata schema definitions.

Schemas:

1. ChunkMetadata
   - document_id (str): Unique document ID
   - title (str): Document title
   - document_type (str): law, rule, form, procedure, faq, other
   - section (str, optional): Section number
   - page (int, optional): Page number
   - source_url (str, optional): Original URL
   - language (str): en, hi, hinglish
   - authority (str): Government, etc.
   - date_added (datetime): When added to KB

2. DocumentMetadata
   - id (str): Document ID
   - title (str): Document title
   - source_type (str): Indicates source category
   - jurisdiction (str): national, state, local
   - domain (str): labor, tenant, consumer, rti, etc.
   - effective_date (datetime): When law became effective
   - expiry_date (datetime, optional): If expired
   - authority (str): Issuing authority

3. RetrievedChunk
   - id (str): Chunk ID
   - document_id (str): Parent document ID
   - content (str): Chunk text
   - embedding (List[float]): Vector embedding
   - metadata (ChunkMetadata): Full metadata
   - similarity_score (float): Search relevance score

Classes: Pydantic models for validation
"""
