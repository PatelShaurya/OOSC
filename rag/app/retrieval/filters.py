"""
Metadata filtering module.

Service-specific filters:

Rights Navigator:
  - document_type: [law, rule, guideline]

Form Assistant:
  - document_type: [form, procedure, guideline]

Complaint Generator:
  - document_type: [law, procedure, form]

Constants:
- SERVICE_FILTERS: Dictionary mapping services to filter conditions

Functions:
- get_filter_for_service(): Get metadata filter for a service
- apply_filter(): Apply filter to vector search query
"""
