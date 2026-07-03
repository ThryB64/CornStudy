# Indicateur selectif V1 - fusion et signal unique

Un seul signal BEARISH_RISK / NEUTRAL / UNCERTAIN, par seuils figes a priori ancres sur la base rate (~0.37) : BEARISH si p>0.5, NEUTRAL si p<0.3, UNCERTAIN entre les deux. Module par le regime de volatilite. Anti-leakage : memes regles que la validation walk-forward.

## Backtest du signal fusionne (OOS 2014-2025)

Base rate de baisse > 3 % a H60 : 0.37.

| signal | n | couverture | P(baisse) realisee | lift vs base |
|---|---|---|---|---|
| BEARISH_RISK | 376 | 13% | 0.58 | +0.21 |
| NEUTRAL | 1527 | 54% | 0.28 | -0.09 |
| UNCERTAIN | 942 | 33% | 0.43 | +0.06 |

Lecture : quand le signal dit BEARISH_RISK, la baisse arrive nettement plus souvent que la base ; NEUTRAL est sous la base ; UNCERTAIN (abstention) reste proche du hasard.

## Backlog termine

- Placebo etendu (permutation des labels) : AUC = **0.498** (proche de 0.5 = le signal reel n'est pas du hasard).
- M3 calibration : R2 (vol predite vs realisee) = **0.06**.
- M3 seuils de regime figes sur 2014-2018 (CALME / NORMAL / VOLATIL / EXTREME).
- M4 couts reels (vendre la prime haute, H90, research-only) :

| cout/jambe (EUR/t) | PnL brut | PnL net |
|---|---|---|
| 0 | +15.7 | +15.7 |
| 2 | +15.7 | +11.7 |
| 5 | +15.7 | +5.7 |

## Snapshot live (lecture du jour)

```json
{
  "date": "2025-07-25",
  "signal_cbot_h60": "NEUTRAL",
  "prob_baisse_3pct_h60": 0.28,
  "confiance": 0.55,
  "regime_volatilite": "NORMAL",
  "vol_attendue_pct": 24.2,
  "basis_z_euronext": 1.7,
  "premium_status": "prime normale",
  "note": "research-only ; M4 prix EMA ~97 % proxy ; aucune action si confiance faible"
}
```

## Statut final

L'indicateur est un detecteur de CONTEXTE de risque, pas un predicteur de prix : il dit BEARISH_RISK, NEUTRAL ou UNCERTAIN, et s'abstient quand la confiance est faible. Module M4 reste research-only (prix EMA proxy, couts qui rongent l'edge). Prochaine etape naturelle : validation forward en conditions reelles (paper) avant tout usage.
