"""
Response schema definitions for RAG API.

Schemas:

1. Source
   - id (str): Source identifier
   - title (str): Document title
   - type (str): law, rule, guideline, form, procedure, faq, other
   - section (str, optional): Section number/title
   - page (int, optional): Page number
   - url (str, optional): Source URL

2. GenerateData (base response)
   - answer (str): Generated answer
   - sources (List[Source]): Supporting sources
   - confidence (float, optional): 0.0-1.0 confidence score

3. RightsResponse
   - Inherits GenerateData
   - Always includes sources and confidence

4. FormResponse
   - answer (str): Next question for user
   - extracted_fields (Dict): Fields extracted so far
   - missing_fields (List[str]): Still-needed fields
   - sources (List[Source]): Empty for form

5. ComplaintResponse
   - answer (str): Formal complaint draft
   - sources (List[Source]): Legal citations

6. RetrieveData
   - chunks (List): Retrieved chunks with scores
   - metadata: Chunk metadata

7. ErrorResponse
   - success (bool): False
   - error (Dict): Code and message

8. SuccessResponse (wrapper)
   - success (bool): True
   - data (Union[GenerateData, ErrorResponse])

Classes: Pydantic models for validation
"""
