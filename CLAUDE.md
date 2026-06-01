# Rôle de Claude Code — Etude Mais

Claude Code est l'organisateur technique et le principal exécutant du projet.

## Entrées à lire au démarrage

Claude lit uniquement le nécessaire :

- `.ai/STATE.md`
- `.ai/TICKETS.md`
- les fichiers explicitement utiles au ticket en cours

Ne pas lire `data/`, `artefacts/`, `logs/`, `csv/`, `*.parquet`, `*.pkl`.

## Responsabilités

- Transformer les idées de `.ai/IDEAS.md` en tickets précis dans `.ai/TICKETS.md`.
- Classer les tickets : `simple`, `moyen`, `complexe`, `critique`.
- Définir les dépendances entre tickets.
- Indiquer les fichiers à modifier, à lire et interdits.
- Exécuter les tickets `complexe` et `critique`.
- Vérifier les tickets en `NEEDS_REVIEW`.
- Garder le contexte court.

## Code Review Graph

Avant tout ticket `moyen`, `complexe` ou `critique`, utiliser l'agent Explore pour tracer le graphe de dépendances réel :
- Quels fichiers importent le module concerné ?
- Quels fichiers sont importés par ce module ?
- Y a-t-il des effets de bord non listés ?

Éviter `grep -r` sur tout le projet. Cibler avec précision.

## Caveman

Utiliser Claude Code en mode Caveman (réponse courte) pour :
- Résumer l'avancement après un ticket.
- Mettre à jour `.ai/STATE.md`.
- Produire une mini-review d'un ticket simple.

Signaler explicitement « MODE CAVEMAN » dans la réponse.

## Règles de codage spécifiques au projet

- Anti-leakage obligatoire : `shift(1)` + z-scores expandants sur toutes les données fondamentales.
- Pas de claim non implémenté dans le rapport (`docs/PROFESSIONAL_STUDY_REPORT.md`).
- Table `État réel d'implémentation` ✅/❌/⚠️ maintenue à jour après chaque palier.
- Pas de commentaires évidents. Pas de docstrings multi-paragraphes.
- Imports optionnels (lightgbm, xgboost, shap, statsmodels) dans des blocs `try/except ImportError`.

## Vérifications standard

```bash
cd "src" && python -m ruff check ../src/mais/
python -m pytest tests/ -x -q
python -c "from mais.study.professional import build_professional_study"
```

## Ce qu'il ne faut pas casser

- `build_features()` dans `src/mais/features/__init__.py` — pipeline principal.
- `walk_forward_cqr()` dans `src/mais/meta/cqr.py` — CQR calibré.
- Anti-leakage (`shift(1)`) sur toutes les sources fondamentales.
- Schéma de sortie de `_build_regimes()` : colonnes `Date, corn_close, return_60d, realized_vol_60d, regime_score, regime`.
