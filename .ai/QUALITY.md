# Qualité — Etude Mais

Un ticket n'est pas terminé tant que ses critères de réussite ne sont pas vérifiés.

## Règles

- L'agent lance les vérifications listées dans le ticket quand c'est possible.
- Si une vérification ne peut pas être lancée, l'agent l'indique clairement.
- Un ticket exécuté passe en `NEEDS_REVIEW`, jamais directement en `DONE`.
- Un ticket passe en `DONE` seulement après review.
- La review lit le ticket, le diff git et les fichiers modifiés.

## Vérifications standard Python

```bash
# Lint
ruff check src/mais/

# Import smoke test
python -c "from mais.study.professional import build_professional_study"
python -c "from mais.meta.cqr import CQRModel, walk_forward_cqr"
python -c "from mais.features import build_features"

# Tests unitaires
python -m pytest tests/ -x -q

# Vérification anti-leakage
python -m mais.leakage.audit
```

## Règles spécifiques au projet

- Tout ajout de source de données → vérifier `shift(1)` anti-leakage.
- Tout ajout de modèle → vérifier qu'il est dans `_model_specs()`.
- Tout ajout de colonne dans `_build_regimes()` → vérifier le schéma de retour.
- Tout changement dans `professional.py` → vérifier que `build_professional_study()` ne lève pas d'exception.
- Le rapport ne doit jamais marquer ✅ ce qui n'est pas réellement implémenté.

## Code Review Graph

Utiliser Code Review Graph pour les tickets moyens, complexes ou critiques afin d'identifier les fichiers réellement liés. Ne pas l'utiliser pour remplacer une review.

## Caveman

Utiliser Caveman pour une validation courte, une synthèse ou une mise à jour de `STATE.md`. Ne pas l'utiliser comme unique review d'un ticket risqué.
