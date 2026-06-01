# Règles communes des agents — Etude Mais

Ce système organise le travail ticket par ticket sur le projet de prévision du prix du maïs.

## Règles obligatoires

- Lire `.ai/STATE.md` et `.ai/TICKETS.md` avant toute action.
- Travailler uniquement sur un ticket à la fois.
- Ne jamais lancer d'audit global sauf demande explicite.
- Prendre seulement un ticket `READY` dont toutes les dépendances sont `DONE`.
- Ne modifier que les fichiers listés dans `Fichiers à modifier`.
- Ne jamais modifier les fichiers listés dans `Fichiers interdits`.
- Ne pas lire les dossiers lourds ou générés : `data/`, `artefacts/`, `logs/`, `csv/`, `__pycache__/`, `.venv/`, `notebooks/`.
- Finir chaque ticket en `NEEDS_REVIEW`, jamais directement en `DONE`.
- Mettre à jour `.ai/STATE.md` après le travail.

## Répartition des rôles

| Rôle | Quand l'utiliser |
|---|---|
| **Claude Code** | Planification, découpe, review, compression de contexte, tickets complexes |
| **Code Review Graph** | Identifier les fichiers réellement liés à une fonctionnalité (tickets moyens/complexes/critiques) |
| **Caveman** | Résumé court, mini-review, mise à jour rapide de `STATE.md` |

## Code Review Graph

Code Review Graph remplace `docs/ARCHITECTURE.md` comme référence de navigation.

Il utilise l'agent `Explore` pour tracer le graphe de dépendances réel d'une fonctionnalité.
Il sert à éviter les lectures massives et les audits globaux.
Ne l'utiliser que pour les tickets `moyen`, `complexe` ou `critique`.
Inutile pour un ticket simple et localisé.

## Caveman

Caveman = Claude Code avec contrainte de réponse courte.

Usages : résumé, mini-review, compression de contexte, mise à jour de `STATE.md`.
Ne pas utiliser Caveman pour concevoir une architecture ou résoudre un ticket complexe.

## Dossiers interdits (lecture et modification)

```
data/
artefacts/
logs/
csv/
__pycache__/
.venv/
notebooks/
*.parquet
*.pkl
*.csv
*.xlsx
```

## Fin de ticket

Un agent qui termine l'exécution d'un ticket doit :

1. Vérifier les critères de réussite.
2. Lancer les vérifications prévues (`ruff check`, `python -m pytest`, etc.).
3. Indiquer clairement les tests non lancés.
4. Passer le ticket en `NEEDS_REVIEW`.
5. Mettre à jour `.ai/STATE.md`.
