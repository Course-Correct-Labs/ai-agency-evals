# Mirror Loop (analysis-only demo)

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/BentleyRolling/ai-agency-evals/blob/main/mirror_loop/mirror_loop_demo.ipynb)

This module reproduces the core figures from **The Mirror Loop: Recursive Non-Convergence in Generative Reasoning Systems** using a cached dataset only.

- **No API calls. No prompts.** This is analysis-only to protect review anonymity and keys.
- Input: `data/mirror_loop_results_all.csv`
- Outputs: `figures/fig_mirrorloop_curve.png`, `figures/fig_novelty_curve.png`

## Run (CLI)
```bash
cd mirror_loop
python mirror_loop_demo.py
```

## Run (Notebook)

Open `mirror_loop_demo.ipynb` and run all cells.

## Data Dictionary

**Expected CSV columns:**
- `iteration` (int): Iteration number (0-7 typical)
- `edit_change` (float): ΔI - normalized edit distance between iterations
- `ngram_novelty` (float): 3-gram novelty ratio (surface-level linguistic change)
- `provider` (str, optional): API provider (e.g., "openai", "anthropic")
- `model` (str, optional): Model identifier
- `condition` (str, optional): Experimental condition (e.g., "grounded", "ungrounded")

The demo aggregates across providers/models to produce pooled curves.

## Notes

- The submitted manuscript is not included in this repo. For review it is available privately: "Private Manuscript (on request)".
- When the journal decision is final, we may add a DOI and link a public release tag.


## Quick Start

Run in Colab (no setup required):

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Course-Correct-Labs/ai-agency-evals/blob/main/mirror_loop/mirror_loop_demo.ipynb)

or locally:
```bash
cd mirror_loop
python3 mirror_loop_demo.py
```

If `mirror_loop_results_all.csv` is missing, the demo automatically uses synthetic data for a working example.

## Citation and Release

Preprint: arXiv:TO-BE-ADDED  
Release: v0.2.0-mirror-loop

