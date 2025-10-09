"""
ot_bench: Observer-Time Evaluation

Tests the diagnostic claim that LLMs register anchors but cannot constitute intervals.

Key experiments:
- Self-initiation test: Can model alert at 60s without tools?
- Temporal drift: Estimation error after distractor tasks
- Elasticity: Error difference under attention load

Predicted results:
- Self-initiation rate ≈ 0% (models cannot spontaneously alert)
- High estimation error (no interval constitution)
- No elasticity (no attention-load modulation)
"""

__version__ = "0.1.0"
