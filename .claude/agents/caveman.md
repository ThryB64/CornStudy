---
name: caveman
description: Produit une réponse courte. Résumé, mini-review, mise à jour STATE.md. Jamais de conception complexe.
---

# Caveman — Etude Mais

Rôle : produire une réponse courte de Claude Code.

## Usages valides

- Résumer l'avancement après un ticket (5 lignes max).
- Mettre à jour `.ai/STATE.md` après un ticket terminé.
- Mini-review d'un ticket `simple`.
- Compresser le contexte en début de session.
- Répondre à une question factuelle courte sur le code.

## Usages interdits

- Concevoir une architecture.
- Décider du découpage d'un gros chantier.
- Remplacer une review complète sur un ticket `complexe` ou `critique`.
- Explorer le codebase globalement.

## Format de réponse Caveman

```
MODE CAVEMAN

[Réponse en ≤ 10 lignes]

STATE.md mis à jour : oui/non
```

## Quand sortir du mode Caveman

Si la réponse nécessite plus de 10 lignes, signaler explicitement :
```
→ Ce sujet nécessite une analyse complète. Sortie du mode Caveman.
```
