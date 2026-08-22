"""
Main RAG generation endpoint.

POST /generate
Input: query, service (rights/form/complaint), language (en/hi/hinglish), conversation_id, conversation_history
Output: answer, sources, confidence

Services:
- rights: Legal advice/navigation
- form: Form-filling assistance with field extraction
- complaint: Formal complaint draft generation
"""
