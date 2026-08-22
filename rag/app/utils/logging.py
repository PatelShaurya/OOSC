"""
Logging configuration for RAG service.

Logs:
- Query processing start/end
- Retrieval statistics (chunks found, scores)
- LLM calls (model, tokens, latency)
- Errors and exceptions
- Performance metrics

Functions:
- setup_logging(): Initialize logging configuration
- log_query(): Log incoming query
- log_retrieval(): Log retrieval results
- log_generation(): Log generation statistics
- log_error(): Log errors with context
"""
