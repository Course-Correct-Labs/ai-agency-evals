"""
Mirror Loop Analysis Demo (Analysis-Only)

Reproduces the canonical curves from The Mirror Loop paper using cached results.
No API calls. No provider prompts. Manuscript excluded during review.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA = Path(__file__).parent / "data" / "mirror_loop_results_all.csv"
FIGS = Path(__file__).parent / "figures"
FIGS.mkdir(exist_ok=True, parents=True)

if not DATA.exists():
    raise FileNotFoundError(
        f"Expected data at {DATA}. "
        "Place 'mirror_loop_results_all.csv' in mirror_loop/data/ (analysis-only)."
    )

df = pd.read_csv(DATA)

# Expect columns: iteration, edit_change (ΔI), ngram_novelty (and optionally model, condition)
# Aggregate across providers for the canonical pooled curve
pooled = df.groupby('iteration', as_index=False).agg(
    delta_I=('edit_change', 'mean'),
    ngram_novelty=('ngram_novelty', 'mean')
)

# ΔI curve
ax = pooled.plot(x='iteration', y='delta_I', marker='o', legend=False)
ax.axvline(3, linestyle='--', color='gray', alpha=0.7)  # minimal grounding at iteration 3
ax.set_title("Mirror Loop: Informational Decay and Grounding Rebound (ΔI)")
ax.set_xlabel("Iteration")
ax.set_ylabel("ΔI (normalized edit distance)")
fig_path = FIGS / "fig_mirrorloop_curve.png"
ax.figure.savefig(fig_path, bbox_inches='tight', dpi=150)
plt.close(ax.figure)

# Novelty curve
ax2 = pooled.plot(x='iteration', y='ngram_novelty', marker='o', legend=False, color='coral')
ax2.set_title("Surface Novelty Decline Across Iterations")
ax2.set_xlabel("Iteration")
ax2.set_ylabel("3-gram Novelty Ratio")
fig2_path = FIGS / "fig_novelty_curve.png"
ax2.figure.savefig(fig2_path, bbox_inches='tight', dpi=150)
plt.close(ax2.figure)

# Console summary for resume bullets
early = pooled.loc[pooled['iteration'].isin([1,2]), 'delta_I'].mean()
late  = pooled.loc[pooled['iteration'].isin([6,7]), 'delta_I'].mean()
print(f"Mean ΔI early (1–2): {early:.3f}")
print(f"Mean ΔI late  (6–7): {late:.3f}")
print(f"Reduction: {((late - early)/early)*-100:.1f}%")
print(f"Wrote figures to: {fig_path.name}, {fig2_path.name}")
