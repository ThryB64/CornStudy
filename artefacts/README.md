# Artefacts Directory

Generated model and study outputs are written here locally.

Important generated paths:

- `artefacts/predictions/`
- `artefacts/meta_database.parquet`
- `artefacts/meta_predictions.parquet`
- `artefacts/professional_study/model_benchmarks.parquet`
- `artefacts/professional_study/calibrated_predictions.parquet`
- `artefacts/professional_study/decision_snapshot.json`

These files are intentionally ignored by Git. Rebuild them with:

```bash
make train
make stack
make study
```
