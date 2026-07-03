# External Research Library

Preparation date: 2026-06-11

This folder is a separated external research workspace for the corn CBOT / Euronext EMA study. It prepares sources, source cards, discovery scripts and EXT experiment scaffolding for Claude. It does not modify the main model, production scripts, datasets or existing project artefacts.

## Structure Created

- `sources/`: seed and discovered repositories, papers and patents.
- `github_repos/`: shallow clones of seed GitHub repositories when cloning succeeded.
- `source_cards/`: empty Markdown cards for repositories, papers and patents.
- `summaries/`: reserved space for reviewed summaries.
- `matrices/`: ideas matrix, source inventories and implementation candidates.
- `scripts/`: cloning, scanning, discovery and card-generation scripts.
- `docs/`: Claude instructions, protocol, anti-leakage rules and naming convention.
- `experiments/external_tests/`: workspace for future EXT experiments.
- `results/external_tests/`: separated result workspace for future EXT experiments.

## Seed Sources

- Seed repositories: 11
- Seed papers, reports, theses or articles: 42
- Seed patents: 10
- Total seed sources: 63

## Discovery Run

Discovery scripts were run once on 2026-06-11.

- Discovered repositories: 24
- Discovered papers: 37
- Patent manual-search query records: 7
- Total discovered or follow-up records: 68

These are candidates or follow-up query records, not validated sources. Claude should review each one before promoting it to an EXT experiment. Google Patents returned `503` during the final automated patent discovery run, so `discovered_patents.yml` keeps manual Google Patents search URLs instead of pretending those are validated patent results.

## Repository Cloning

The seed clone script uses shallow `git clone --depth 1` and never overwrites an existing folder.

- Standard shallow clones: 10
- Sparse partial clones: 1
- Failed after retry: 0

Sparse partial recovery:

- `mindymallory/PriceAnalysis`: full checkout failed on a problematic asset path. It was recovered with `git clone --filter=blob:none --no-checkout` plus sparse checkout. Local path: `github_repos/mindymallory__PriceAnalysis`.
- Recovered content focuses on useful chapters for corn, ethanol, DDG, basis, hedging, storage and nearby futures: `01-PrimerforGrain.qmd`, `02-IntroductiontoCommodity.qmd`, `04-FuturesContractsandHedging.qmd`, `09-PricesSpaceTime.qmd`, `10-FundamentalAnalysisand.qmd`, `13-ForecastingUseof.qmd`, `15-EndingStocksand.qmd`, `17-EthanolMarketsand.qmd`, `22-IntroductiontoCommodityTS.qmd`, plus selected supporting assets and spreadsheets.

Clone log:

- `sources/repo_clone_log.csv`

## Catalogues and Matrices

- `sources/seed_repositories.yml`
- `sources/seed_papers.yml`
- `sources/seed_patents.yml`
- `sources/discovered_repositories.yml`
- `sources/discovered_papers.yml`
- `sources/discovered_patents.yml`
- `matrices/ideas_matrix.csv`: 37 initial EXT ideas plus header.
- `matrices/implementation_candidates.csv`: first 10 candidate priorities.
- `matrices/source_inventory.csv`: scanned local repository metadata.
- `matrices/source_inventory_catalog.csv`: 131 seed/discovered source records.

## Scripts Created

- `scripts/clone_seed_repos.py`
- `scripts/scan_repo_metadata.py`
- `scripts/search_more_github_repos.py`
- `scripts/search_more_papers.py`
- `scripts/search_more_patents.py`
- `scripts/build_source_inventory.py`
- `scripts/generate_source_card_templates.py`

Suggested refresh sequence:

```bash
python3 external_research/scripts/search_more_github_repos.py
python3 external_research/scripts/search_more_papers.py
python3 external_research/scripts/search_more_patents.py
python3 external_research/scripts/generate_source_card_templates.py
python3 external_research/scripts/build_source_inventory.py
```

## Source Cards

Generated source-card templates: 131

Folders:

- `source_cards/repositories/`
- `source_cards/papers/`
- `source_cards/patents/`

Each card is intentionally empty in the analytic sections. Claude should fill the cards one source at a time.

## Next Steps for Claude

1. Read `docs/instructions_for_claude.md`.
2. Review `docs/anti_leak_rules.md` before any source analysis.
3. Start with the top implementation candidates in `matrices/implementation_candidates.csv`.
4. Fill source cards one by one.
5. Enrich `matrices/ideas_matrix.csv`.
6. Create EXT experiments only under `experiments/external_tests/`.
7. Write results only under `results/external_tests/`.
8. Conclude each idea as `KEEP`, `IMPROVE`, `REJECT` or `DATA_BLOCKED`.

## Boundary

This library is preparation and collection only. It is not an integration ticket and does not change the current indicator.
