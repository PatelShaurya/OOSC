"""
Answer validation and safety module.

Checks:
1. Hallucination detection: Ensure answer is grounded in sources
2. Confidence thresholds: Return "I don't know" for low-confidence answers
3. Domain validation: Ensure question is in civic/legal scope
4. Citation validation: Every [Source X] reference is valid

Functions:
- validate_answer(): Check answer for issues
- is_hallucination(): Detect invented facts
- is_in_scope(): Check if question is civic/legal
- validate_citations(): Verify all cited sources exist
"""
