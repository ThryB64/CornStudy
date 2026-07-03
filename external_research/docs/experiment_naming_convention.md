# Experiment Naming Convention

External research experiments use:

`EXT###_short_slug`

Rules:

- `EXT###` is stable once assigned.
- `short_slug` uses lowercase ASCII words separated by underscores.
- One experiment answers one hypothesis.
- Do not reuse an ID for a different hypothesis.
- Put scripts under `external_research/experiments/external_tests/EXT###_short_slug/`.
- Put results under `external_research/results/external_tests/EXT###_short_slug/`.

Recommended files per experiment:

- `README.md`
- `build_features.py` if new features are needed
- `evaluate.py` if a benchmark is needed
- `results.json`
- `conclusion.md`

Verdicts:

- `KEEP`
- `IMPROVE`
- `REJECT`
- `DATA_BLOCKED`
