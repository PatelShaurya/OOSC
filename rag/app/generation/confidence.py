"""
Confidence scoring module.

Methods:

1. RETRIEVAL_BASED (MVP): Max chunk similarity score
2. ENHANCED (Phase 2): 
   - 50% retrieval quality
   - 30% source authority
   - 20% citation presence

Functions:
- calculate_confidence(): Calculate response confidence
- calculate_retrieval_confidence(): Simple retrieval-based score
- calculate_enhanced_confidence(): Multi-factor scoring
"""
