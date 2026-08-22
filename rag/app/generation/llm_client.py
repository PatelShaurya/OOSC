"""
LLM (Claude) client wrapper.

Handles: Calls to Anthropic Claude API
Configuration: API key, model, temperature, max_tokens
Timeouts: Handle model timeouts gracefully

Classes:
- LLMClient: Claude API wrapper

Functions:
- generate(): Generate text response
- generate_json(): Generate JSON-formatted response
- get_model_info(): Return current model info
"""
