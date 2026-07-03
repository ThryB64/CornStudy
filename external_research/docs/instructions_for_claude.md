# Instructions for Claude

This folder is an external research library. It is not part of the production model and must not modify the main dataset, model code or existing study artefacts.

## Where things are

- Seed repositories: `external_research/sources/seed_repositories.yml`
- Discovered repositories: `external_research/sources/discovered_repositories.yml`
- Cloned repositories: `external_research/github_repos/`
- Seed papers: `external_research/sources/seed_papers.yml`
- Discovered papers: `external_research/sources/discovered_papers.yml`
- Seed patents: `external_research/sources/seed_patents.yml`
- Discovered patents: `external_research/sources/discovered_patents.yml`
- Source cards: `external_research/source_cards/`
- Ideas matrix: `external_research/matrices/ideas_matrix.csv`
- External experiment workspace: `external_research/experiments/external_tests/`
- External results workspace: `external_research/results/external_tests/`

## How to fill source cards

Read one source at a time. Fill only the corresponding card in:

- `source_cards/repositories/`
- `source_cards/papers/`
- `source_cards/patents/`

For repositories, identify data, features, target, horizon, models, evaluation method, metrics, strengths, weaknesses, leakage risks, reusable code and testable ideas.

For papers and patents, extract the economic idea, feature idea, model idea, evaluation idea, limits, leakage risk and possible EXT experiment.

## How to turn a source into a testable hypothesis

Each source should produce zero or more hypotheses in `matrices/ideas_matrix.csv`.

A good hypothesis has:

- a clear economic mechanism;
- data that is available at the prediction date;
- a target and horizon;
- a baseline comparison;
- an expected benefit;
- a leakage-risk assessment;
- a verdict rule: keep, improve, reject or data-blocked.

## External versus internal tests

External tests live under `external_research/experiments/external_tests/EXTxxx/`.

They must not import changes into the main model. If a test needs project loaders, it may read public project APIs, but results remain in `external_research/results/external_tests/`.

Only after a source card and EXT test are reviewed can a separate project ticket propose integration.

## Naming EXT experiments

Use `EXT###_short_name`.

Examples:

- `EXT001_weather_crop_windows`
- `EXT006_roll_method_volume_based`
- `EXT025_random_walk_and_futures_price_benchmark`

Every EXT folder should contain:

- `README.md`
- a feature-engineering script if needed;
- an evaluation script if needed;
- an output folder or explicit result path;
- a conclusion: keep, improve, reject or data-blocked.

## Anti-leakage reminders

Follow `external_research/docs/anti_leak_rules.md` strictly.

The most common traps are random splits, global normalization, selecting variables on all data, using revised WASDE values too early, using COT Tuesday position dates instead of Friday publication dates, and treating realized future weather as if it were a forecast.

## Conclusion format

For each source and experiment, end with one of:

- `KEEP`: robust OOF value and plausible economics;
- `IMPROVE`: promising but needs better data or protocol;
- `REJECT`: no value versus baseline or too fragile;
- `DATA_BLOCKED`: idea is relevant but data is missing or not timestamp-safe.
