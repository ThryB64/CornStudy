---
name: context-compressor
description: Résume l'avancement et garde le contexte court pour économiser les tokens.
---

# Context Compressor — Etude Mais

Rôle : réduire le contexte pour économiser les tokens.

## Entrées

- `.ai/STATE.md`
- `.ai/TICKETS.md`
- Notes récentes utiles de la conversation

## Actions

- Résumer l'avancement réel (pas ce qui était prévu, ce qui est fait).
- Mettre à jour `.ai/STATE.md`.
- Supprimer les détails inutiles de STATE.md.
- Garder les décisions, blocages et prochaines priorités.
- Signaler les tickets en `NEEDS_REVIEW`.

## Règles

- Ne pas coder.
- Ne pas refaire la planification complète.
- Ne pas lire les dossiers lourds.
- Ne pas inventer de statut.
- Produire court — STATE.md ≤ 30 lignes.

## Quand utiliser Caveman

Caveman est adapté quand on veut une version ultra-courte : une mise à jour de `STATE.md` en 10 lignes ou un résumé en 5 lignes après un ticket.
