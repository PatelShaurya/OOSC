"""
Prompt templates for different services.

Prompt Templates:

1. RIGHTS_PROMPT: For legal/civic questions
   - Grounded in retrieved documents
   - Cite sources
   - Simple language
   - Actionable guidance

2. FORM_PROMPT: For form-filling interviews
   - Extract structured data
   - Identify missing fields
   - Ask next question
   - Output as JSON

3. COMPLAINT_PROMPT: For complaint drafting
   - Formal structure
   - Legal citations
   - Chronological facts
   - Relief sought

Functions:
- build_rights_prompt(): Construct rights question prompt
- build_form_prompt(): Construct form-filling prompt
- build_complaint_prompt(): Construct complaint draft prompt
"""
