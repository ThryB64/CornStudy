# V120 — Économétrie du basis EMA/CBOT : bruit blanc ou signal ?

Session 2026-06-02. Réponse rigoureuse à « le basis a-t-il une structure prédictible ou est-ce du bruit
blanc ? » via ARMA/ARIMA/ARIMAX + tests de Portmanteau (Ljung-Box) et stationnarité (ADF). statsmodels en
import optionnel. Descriptif (structure in-sample), pas un modèle de trading. `RESEARCH_ONLY_NOT_TRADING`.

## Résultats
| Test | Résultat | Lecture |
|---|---|---|
| ADF niveau basis_z | stat −6.12, p≈0 → **stationnaire** | le NIVEAU mean-reverte = **signal robuste** |
| AR(1) φ | **0.96** → demi-vie **≈17.1 j** | vitesse de réversion (≈ la demi-vie ~17j déjà trouvée) |
| Ljung-Box Δbasis_z (lag10) | LB 46.2, p≈0 → **pas bruit blanc** | il y a une STRUCTURE dans les variations |
| ARIMAX (CBOT, wheat/corn laggés) | AIC 2012 → **1814** (exog_adds_signal=True) | CBOT/blé-maïs ajoutent de l'info |
| Résidus du meilleur ARIMA | non-blancs (p<0.01) | un ARMA simple ne capte pas tout |

**Verdict** : `LEVEL_MEAN_REVERTS_CHANGES_HAVE_WEAK_STRUCTURE`.

## Changement de comportement autour du retournement (n=41)
- Variance de Δbasis_z **AVANT** le turn = **0.191** > **APRÈS** = **0.099** → le basis est **plus agité
  pendant le blow-off** (l'overshoot), puis se calme en compression. La variance ne MONTE pas au turn, elle
  RETOMBE après — signature : le pic est volatil, la descente plus régulière.
- Autocorrélation lag-1 de Δbasis_z : pré −0.08, post **−0.20** → réversion quotidienne plus marquée
  (saccadée) pendant la compression.

## Synthèse (réconcilie V120 et V106)
- **Signal FORT** : la réversion du NIVEAU (ADF stationnaire, demi-vie 17 j) — c'est ce qu'exploite la
  baseline `basis_z>1`.
- **Signal FAIBLE** : les variations quotidiennes ont une structure statistique réelle (Ljung-Box rejette le
  bruit blanc, l'ARIMAX améliore via CBOT/wheat-corn) MAIS elle est trop ténue pour timer proprement le
  retournement (V106 OOF AUC ~0.58, trigger inversé).
- **Conclusion** : on exploite la réversion du niveau, pas la prédiction des variations. Le « déclencheur
  précis » reste hors de portée des variables daily — cohérent avec V105/V106. Pour un vrai déclencheur
  *leading*, il faut des données qui précèdent le prix (intraday, courbe officielle, MATIF, révisions météo).

Module `v120_basis_econometrics.py` (`run_v120_all`), tests 2 PASS, ruff PASS. Artefact `artefacts/v120/`.
