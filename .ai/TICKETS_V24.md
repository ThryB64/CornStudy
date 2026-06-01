# Tickets — V24 Audit forensique des données

Demande utilisateur : avant tout nouveau modèle, auditer intégralement les données (EMA, CBOT, FX, contrats,
rolls, targets, conversion) et reconstruire la chaîne centrale. Doc `docs/V24_FORENSIC_AUDIT.md`.

## Exécuté (verdict global : DATA_AUDIT_PASS_RESEARCH_ONLY)

- **V24-01** — `DONE` — Inventaire datasets (`data_inventory.json`).
- **V24-02** — `DONE` — Source EMA : `ema_close` = 97% proxy exploratoire (ema_front_continuous_raw) ;
  ancien euronext_ema.csv NON utilisé. Verdict RESEARCH_ONLY_PROXY_DOMINANT.
- **V24-03** — `DONE` — Contrats : H/M/Q/X uniquement, **F/Janvier absent**, DTE≥15, 69 rolls. CLEAN.
  La mention F dans docs/euronext_endpoint.md = doc périmée, pas la donnée.
- **V24-05** — `DONE` — Conversion correcte (cents/100/eurusd×39.3679 ; inverse = err absurde). Écart médian
  1.5 €/t = alignement de roll (pics mi-juillet). Verdict CONVERSION_CORRECT_MINOR_ROLL_ALIGN.
- **V24-06** — `DONE` — Leakage propre : basis_z causal (rolling 260 trailing), pas de fillna(0), targets futurs alignés.
- **V24-07** — `DONE` — **Rebuild de zéro cohérent** : 47 trades, hit 0.851 ≈ master (42, 0.81). Le signal
  n'est pas un artefact de pipeline. RÉSULTAT CLÉ.

## Trouvailles

1. Aucune erreur invalidant les résultats — chaîne centrale validée.
2. Réserve permanente : EMA 97% proxy → research-only.
3. Cosmétique : colonne `eurusd` du master mal étiquetée (dérivée ×36.744 ≈ 93×taux réel) — inoffensive
   comme feature standardisée, résultats inchangés. À relabéliser (V25).

## Suite

- **V25-EURUSD-RELABEL** — charger le vrai eurusd_rate dans load_master (cosmétique, sans revalidation).
- **V26-EMA-OFFICIAL** `WAITING_DATA` — source Euronext officielle (déblocage n°1).
- Indicateur figé (basis_z + saison + sortie z→0/0.5 + warnings + gate fraîcheur).
