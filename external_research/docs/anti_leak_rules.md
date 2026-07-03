# Anti-Leak Rules

These rules apply to every external source review and every EXT experiment.

1. Never use random splits for time-series evaluation.
2. Use walk-forward, expanding, rolling or purged time-series splits.
3. Every feature must be available at the prediction date.
4. WASDE variables must use the real publication date, not a later revised table.
5. COT variables must use the Friday publication date, not the Tuesday position date.
6. Forecast weather must be separated from realized historical weather.
7. Rolling windows must use past observations only.
8. Monthly and annual releases must respect their real publication lag.
9. Do not normalize on the full dataset before splitting.
10. Do not select variables on the full dataset before splitting.
11. Do not tune thresholds on test years.
12. Do not use the locked holdout unless a separate human-approved project ticket explicitly opens it.
13. Keep source timestamps in the raw extracted data when possible.
14. If a timestamp cannot be proven, mark the source `DATA_BLOCKED` or `RESEARCH_ONLY`.

Special lags:

- WASDE/NASS: use release calendar and release-day availability.
- COT: positions are Tuesday, but the public information date is Friday.
- Weather: realized weather is explanatory; forecast weather is predictive.
- Satellite/NDVI: use acquisition and publication timestamps, not image period alone.
- Financial data revisions: use the first available value where possible.
