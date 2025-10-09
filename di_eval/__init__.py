"""
di_eval: Delegated Introspection Evaluation

Tests the three-stage absorption model:
  1. Prompt Substitution
  2. Synthetic Reflection
  3. Reintegration

Key metrics:
- Absorption Rate: overlap between model reasons and user restatements
- Style Convergence: embedding similarity over turns
- Turn Curve: absorption by turn count (tests 3-5 turn peak prediction)
"""

__version__ = "0.1.0"
