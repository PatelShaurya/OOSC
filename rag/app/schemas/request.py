"""
Request schema definitions for RAG API.

Schemas:

1. GenerateRequest
   - query (str, required): User question
   - service (str, required): rights | form | complaint
   - language (str, required): en | hi | hinglish
   - conversation_id (str, optional): Conversation identifier
   - conversation_history (List, optional): Recent conversation messages

2. RetrieveRequest (debug endpoint)
   - query (str, required): User question
   - service (str, required): Service type
   - language (str, required): Language
   - top_k (int, optional): Number of results to return

3. IngestRequest
   - document (file or text)
   - document_type (str): law, form, procedure, etc.
   - metadata (dict): Additional metadata

4. ConversationMessage
   - role (str): user | assistant
   - content (str): Message text

Classes: Pydantic models for validation
"""
