# V24 — Audit forensique des données (verdict)

**Date** : 2026-05-31 · **Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Module** : `src/mais/research/v24_data_forensic.py` · runner `run_v24.py` · tests (4 PASS)
**Artefacts** : `artefacts/v24/` (data_inventory, ema_source_audit, ema_contract_audit, conversion_audit,
target_leakage_audit, minimal_rebuild, forensic_summary).

Avant tout nouveau modèle : vérifier que toute l'étude repose sur les **bonnes données**. Verdict global :
**`DATA_AUDIT_PASS_RESEARCH_ONLY`** — aucune erreur invalidant les résultats. Une réserve permanente
(proxy) et une correction cosmétique (étiquette eurusd).

---

## Verdicts par axe

| Axe | Verdict | Détail |
|---|---|---|
| Inventaire | DONE | Datasets clés catalogués (lignes, dates, source). |
| **Source EMA** | `RESEARCH_ONLY_PROXY_DOMINANT` | `ema_close` = **97% proxy exploratoire**, 3% officiel/manuel. |
| **Contrats** | `CONTRACTS_CLEAN_HMQX_NO_F` | month_code = **H/M/Q/X uniquement**, F/Janvier ABSENT, DTE≥15, 69 rolls. |
| **Conversion** | `CONVERSION_CORRECT_MINOR_ROLL_ALIGN` | formule correcte ; médiane d'écart 1.5 €/t (alignement roll). |
| **Leakage** | `LEAKAGE_AUDIT_CLEAN` | basis_z causal (rolling 260 trailing), pas de fillna(0), targets futurs alignés. |
| **Rebuild minimal** | `consistent_with_master = True` | reconstruit de zéro : 47 trades, hit 0.851 ≈ master (42, 0.81). |

---

## V24-02 — Source EMA : 97% proxy (research-only confirmé)

`ema_close` (utilisé par V9/V13/V14/V15/V17/V21/V23) provient de
`data/processed/euronext/ema_front_continuous_raw.parquet` :
- **3275 lignes `barchart_proxy_exploratory`** + 102 `euronext_chart_history/ajax` (officiel/manuel).
- **proxy_share = 0.97**.
- L'ancien `data/raw/euronext_ema/euronext_ema.csv` (proxy CBOT pur, open=high=low=close, vol=0) **n'est
  PAS utilisé** par `load_master_dataset`. ✓

→ Toute conclusion EMA reste **research-only** tant que la source officielle Euronext n'est pas intégrée.

## V24-03 — Contrats : H/M/Q/X, pas de F/Janvier (contradiction doc résolue)

Les données processed (`ema_contract_daily.parquet`) sont **strictement H/M/Q/X** (Mars/Juin/Août/Nov ;
`contract_month ∈ {3,6,8,11}`). **F/Janvier est absent.** La mention « F » dans
`docs/euronext_endpoint.md` est de la **documentation périmée**, pas la donnée réelle. DTE front : min 15,
**0 contrat avec DTE < 15**, 69 rolls documentés. → construction de la série continue **propre**.

## V24-05 — Conversion CBOT→EUR/t : formule correcte

Formule pipeline (`euronext_curve.py`) : `cbot_eur_t = cents/100 / eurusd_rate × 39.3679`.
- **Vérifiée** : la formule inverse (×eurusd) donne une erreur ~21 000 €/t (absurde) → le sens est bon.
- Vrai `eurusd_rate` (eu_cross_assets) : range 0.96–1.60, médiane 1.20 → **vrai taux FX**.
- Reconstruction vs `cbot_eur_t` stocké : **médiane 1.5 €/t** (~1%), p95 6.5, max 49. Les pires écarts
  tombent tous **mi-juillet** (dates de roll) → **artefact d'alignement de roll/contrat**, pas un bug de
  formule.

## V24-06 — Leakage : propre

- `basis_z` construit par `rolling(260, min_periods=20)` **trailing** → **causal**, pas de futur.
- Pas de `fillna(0)` suspect sur basis_z (part de zéros exacts négligeable).
- Targets (`y_rel_outperform_h40`, etc.) ont des NaN en fin de série (futur indisponible) → alignement correct.

## V24-07 — Rebuild minimal : la chaîne centrale est cohérente (résultat clé)

Reconstruction **de zéro** : `ema_front` brut + `corn_close` brut + vrai `eurusd_rate` → `cbot_eur_t` →
`basis = ema_front − cbot_eur_t` → `basis_z` (rolling 260) → trades short basis_z>1, sortie z→0 max90.

| | Rebuild de zéro | Référence master (V23) |
|---|---:|---:|
| n trades short | 47 | ~42 |
| hit rate | 0.851 | ~0.81 |
| PnL moyen €/t | 16.2 | ~14-16 |

**Cohérent.** Le signal short basis-haut **n'est pas un artefact de pipeline cassé** : il se reproduit en
repartant des séries brutes. C'est la validation la plus importante de l'audit.

---

## Conclusions

1. **Aucune erreur invalidant les résultats.** Conversion correcte, contrats propres (H/M/Q/X, pas de F),
   basis_z causal, rebuild cohérent. Le signal central est réel et reproductible.
2. **Réserve permanente** : EMA = 97% proxy exploratoire → **research-only** jusqu'à la source officielle.
3. **Correction cosmétique recommandée** : la colonne `eurusd` du master est **dérivée** (`corn_close ×
   36.744 / cbot_eur_t` ≈ 93×taux réel) et donc **mal étiquetée**. Étant un **transform linéaire** du vrai
   taux, elle est **inoffensive comme feature standardisée** (les modèles z-scorent) → **les résultats
   V9-V23 ne sont pas affectés**. À relabéliser proprement en chargeant `eurusd_rate` réel (amélioration
   propre, sans revalidation nécessaire).

## Classement des résultats (cœur du rapport final)

- **Solides** : EMA brut pas la cible ; basis = cible ; mean-reversion ; short basis-haut > long basis-bas ;
  sortie au niveau > H40 ; simple > complexe ; CBOT drawdown > direction ; compression CBOT-driven.
- **Prometteurs à valider** : météo warning, forecast live, paliers strong/extreme, drawdown CBOT 0.74.
- **Rejetés** : meta-model V6, EMA up/down, H90, COT×météo, WASDE prédicteur, fair value macro, ML complexe.
- **Bloqués data** : EMA officiel, courbe multi-échéances, météo prévue historique, options/IV, physiques EU.

## Suite

- **V25** : relabéliser `eurusd` (réel) — cosmétique, résultats inchangés ; sinon revalidation non requise.
- **V26** : source EMA officielle (déblocage n°1) → re-tester proxy vs officiel.
- Indicateur research **figé** (basis_z + saison + sortie z→0/0.5 + warnings + gate de fraîcheur).

---

*V24 — 2026-05-31. Audit forensique : chaîne centrale validée (rebuild cohérent), pas d'erreur critique.*
*Réserve proxy (research-only) et étiquette eurusd à corriger (sans impact résultats). Research-only.*
