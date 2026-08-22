"""
Main generation orchestrator.

Workflow:
1. Route by service (rights/form/complaint)
2. Construct service-specific prompt
3. Call LLM
4. Extract and format response
5. Apply service-specific post-processing

Classes:
- Generator: Main generation engine

Functions:
- generate(): Route and generate response by service
- generate_rights_response(): Generate legal advice response
- generate_form_response(): Generate form-filling response
- generate_complaint_response(): Generate complaint draft
"""
