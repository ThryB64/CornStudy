# Guide utilisateur — score de vente CBOT

Version : `cbot_sale_score_v1`. Date : 2026-06-13.

## 1. Lancer le score
```bash
# dernier signal seulement (rapide)
python -m mais.cli sale-score --latest

# régénérer tous les artefacts (timeseries, coefficients, dictionnaire)
python -m mais.cli sale-score

# + validation holdout 2024+ et backtest décisionnel (une fois)
python -m mais.cli sale-score --holdout
# ou
make sale-score
```
Sorties dans `artefacts/final_cbot_sale_score/` (voir `FINAL_CBOT_SALE_SCORE_TECHNICAL_SUMMARY.md`).

## 2. Lire le score
Le fichier `final_score_latest.json` (ou la sortie `--latest`) donne :
| champ | sens |
|---|---|
| `recommendation` | SELL_PARTIAL / WAIT / WATCH / RISK_HIGH / NO_SIGNAL |
| `prob_up_h90` | probabilité de **hausse** à ~90 séances (≈ 4-5 mois) |
| `p_down_h90` | probabilité de **baisse** à H90 (= 1 − prob_up_h90) |
| `prob_up_h40` | probabilité de hausse à ~40 séances (≈ 2 mois) |
| `pred_vol_h90` | volatilité prévue (risque) |
| `vol_high_decile` | vrai = période très volatile, signal peu fiable |
| `confidence` | 0-1, fiabilité du signal (régime, cohérence, vol) |

## 3. Signification des décisions
| Décision | Sens pour l'agriculteur |
|---|---|
| **SELL_PARTIAL** | risque de baisse à H90 + confiance correcte → **vendre une partie** (ex. 1/3) pour sécuriser |
| **WAIT** | pas de risque baissier détecté (hausse probable) → **attendre** avant de vendre |
| **WATCH** | signal faible ou contradictoire → **surveiller**, pas d'action forte |
| **RISK_HIGH** | volatilité prévue très élevée → **prudence** ; le signal directionnel n'est pas fiable ici |
| **NO_SIGNAL** | données insuffisantes → **pas de signal**, ne rien déduire |

## 4. Exemples d'interprétation
- `SELL_PARTIAL`, `p_down_h90=0.64`, `confidence=0.6` → forte probabilité de baisse d'ici
  ~4 mois avec confiance correcte : envisager de vendre une fraction.
- `WATCH`, `prob_up_h90=0.51`, `confidence=0.35` (cas du 2025-07-25) → marché indécis, pas de
  raison forte d'agir ; surveiller.
- `RISK_HIGH` → période agitée ; reporter la décision directionnelle, gérer le risque.

## 5. Précautions (important)
- C'est une **aide à la décision**, **pas un ordre** ni une garantie. Verdict global :
  **FRAGILE** (voir `FINAL_CBOT_SALE_SCORE_LIMITS.md`).
- Ne jamais l'utiliser comme **unique** déclencheur ; le croiser avec votre situation
  (trésorerie, stockage, base locale) et d'autres repères.
- Sur le holdout, le score **n'a pas battu une simple saisonnalité** → le considérer comme un
  repère parmi d'autres, à reconfirmer dans le temps.
- En `RISK_HIGH` / `NO_SIGNAL` : ne pas se fier à la direction.
