# Data Directory

This repository keeps the data layout, not the generated datasets.

Expected local outputs:

- `data/raw/` for immutable downloads.
- `data/interim/` for cleaned source tables.
- `data/processed/features.parquet`
- `data/processed/targets.parquet`
- `data/processed/factors.parquet`
- `data/metadata/anti_leakage_audit.parquet`

Run:

```bash
make migrate-legacy
make features
make targets
make audit
make factor-analysis
make study
```

Large public-source extracts, legacy CSVs and generated Parquet files are ignored
by Git to keep the repository light and reproducible.
