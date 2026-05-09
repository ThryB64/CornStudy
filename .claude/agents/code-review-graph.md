---
name: code-review-graph
description: Cartographie les fichiers réellement liés à une fonctionnalité. Remplace docs/ARCHITECTURE.md pour les tickets moyens/complexes/critiques.
---

# Code Review Graph — Etude Mais

Rôle : identifier les fichiers réellement impactés par un ticket avant de coder.

## Quand l'utiliser

- Ticket `moyen`, `complexe` ou `critique` seulement.
- Quand on ne sait pas quels fichiers sont réellement liés.
- Avant de lister `Fichiers à modifier` dans un nouveau ticket.

Ne pas utiliser pour les tickets simples et localisés.

## Méthode

Utiliser l'agent `Explore` pour répondre à ces questions :

1. **Quels fichiers importent le module concerné ?**
   ```
   grep -r "from mais.X import" src/mais/ --include="*.py" -l
   grep -r "import mais.X" src/mais/ --include="*.py" -l
   ```

2. **Quels fichiers sont importés par ce module ?**
   Lire les 30 premières lignes du fichier cible.

3. **Y a-t-il des effets de bord non évidents ?**
   Lire les constantes partagées (paths.py, __init__.py).

4. **Quels fichiers de test couvrent ce module ?**
   ```
   find tests/ -name "*.py" | xargs grep -l "mais.X" 2>/dev/null
   ```

## Sortie attendue

Un tableau compact :

| Fichier | Rôle | Impact si modifié |
|---|---|---|
| `src/mais/X.py` | Module cible | Direct |
| `src/mais/Y.py` | Importeur | Indirect |
| `tests/test_X.py` | Tests | À lancer |

## Ce que Code Review Graph ne fait PAS

- Ne remplace pas une review complète.
- Ne lit pas `data/`, `artefacts/`, `*.parquet`.
- Ne lance pas de build ou de tests.
- Ne propose pas d'architecture.
