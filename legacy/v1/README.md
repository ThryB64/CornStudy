# Legacy V1

The original local project contained exploratory scripts, model prototypes,
large CSV exports and raw WASDE archives.

Those files are deliberately not committed in this clean V2 repository:

- `csv/`
- `script/`
- `Models/`
- large spreadsheets / archives
- generated raw and processed data files

The active, maintained application lives in:

- `src/mais/`
- `config/`
- `scripts/`
- `docs/`
- `tests/`

If a legacy CSV export is available locally, place it back under the expected
legacy path and run:

```bash
make migrate-legacy
```

This keeps the repository professional while preserving a clear migration path.
