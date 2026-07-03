# External Research Protocol

## Step A - Inventory

Run the discovery scripts and build the source inventory. Keep seeds and discoveries separate.

## Step B - Read One Source

Read one repository, paper or patent at a time. Avoid global audits.

## Step C - Fill Source Card

Complete the matching file in `source_cards/`. Document the source's data, method, metrics, limitations and leakage risks.

## Step D - Extract Hypothesis

Translate the source into one or more rows in `matrices/ideas_matrix.csv`.

## Step E - Create EXT Experiment

Create `external_research/experiments/external_tests/EXT###_short_name/` only after the hypothesis is clear.

## Step F - Test Separately

Run feature engineering and evaluation in the external workspace. Store outputs under `external_research/results/external_tests/`.

## Step G - Compare Baseline

Every EXT test must compare against a naive baseline, a random walk or futures-price baseline when applicable, and the current project baseline relevant to the target.

## Step H - Conclude

Use one verdict: `KEEP`, `IMPROVE`, `REJECT` or `DATA_BLOCKED`.

## Step I - Integrate Later

Only after review can a new project ticket propose integration into the main model. The external research folder itself is preparation and evidence, not production code.
