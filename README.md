# AI Agency Evals · Course Correct Labs

Open, reproducible evaluations of model behavior and reasoning reliability.
Modules include Mirror Loop and Entropy Collapse Null (CCTR-001).

## Mirror Loop (analysis-only demo)
Reproduces the informational-change decay curve and the minimal-grounding rebound from the study.
- Run locally: `cd mirror_loop && python3 mirror_loop_demo.py`
- Open in Colab: badge in `mirror_loop/README.md`
- Data: expects `mirror_loop/data/mirror_loop_results_all.csv` (gitignored). Falls back to synthetic demo if missing.

## Safety and Reproducibility
- No provider keys or prompts in the repo
- Secret scanning enabled
- Deterministic figures regenerated from cached metrics
