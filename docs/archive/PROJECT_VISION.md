# Vision du projet — Mais AutoML + Étude Professionnelle

## Résumé en une phrase

Construire une plateforme AutoML générique pour séries temporelles financières et agricoles, puis l'utiliser pour produire une étude professionnelle complète du prix du maïs CBOT, aboutissant à un indicateur de décision économique pour les agriculteurs français.

---

## Structure à deux piliers

Le projet repose sur deux ensembles distincts mais connectés. La confusion entre les deux est la source principale de désorganisation passée.

```
Projet global
│
├── Pilier 1 — Plateforme AutoML / AutoForecast
│   ├── Objectif : outil générique, réutilisable, testé
│   ├── Input : n'importe quel CSV propre
│   └── Output : benchmark, métamodèle, rapport automatique
│
└── Pilier 2 — Étude professionnelle du prix du maïs
    ├── Objectif : cas d'usage métier complet et défendable
    ├── Input : données CBOT + USDA + météo + macro + COT
    └── Output : prédiction + incertitude + décision agriculteur
```

**La plateforme est le moteur général.**
**L'étude du maïs est le cas d'application principal.**

L'étude du maïs doit utiliser la plateforme pour être construite. Mais la plateforme doit pouvoir tourner sur d'autres datasets. Les deux se développent en parallèle mais ne se mélangent pas dans le code.

---

## Philosophie du projet

> "Rendre l'étude honnête, pas impressionnante."

Ce principe s'applique partout :

- La table d'implémentation dans le rapport reflète l'état réel, avec ✅ / ❌ / ⚠️ exacts.
- Un modèle n'est utile que s'il bat une baseline simple et testée.
- Une feature n'est gardée que si elle améliore la prédiction out-of-sample.
- Une décision agriculteur n'est proposée que si le backtest la valide sur au moins 10 ans.
- Toute limite est documentée dans le rapport.

Le projet ne cherche pas à impressionner. Il cherche à être :
- reproductible (tout se rebuild depuis le code)
- honnête (aucun claim non vérifié)
- utile (le backtest mesure un vrai gain économique)
- traçable (chaque expérience est documentée)

---

## Contexte du marché du maïs

Le prix du maïs CBOT n'est ni un prix "technique" ni un pur prix "macro". C'est un prix d'équilibre entre plusieurs forces simultanées :

| Force | Horizon de pertinence | Fréquence de mise à jour |
|---|---|---|
| Bilan offre/demande US | J+10 à J+30 | Mensuel (WASDE) |
| Météo Corn Belt | J+5 à J+20 | Quotidien |
| Demand éthanol | J+5 à J+20 | Hebdomadaire |
| Compétitivité export | J+10 à J+30 | Hebdomadaire |
| Positionnement spéculatif | J+5 à J+10 | Hebdomadaire |
| Macro / Dollar | J+10 à J+30 | Quotidien/mensuel |
| Production Brésil/Argentine | J+20 à J+30 | Mensuel |

Ce tableau justifie pourquoi un seul modèle générique ne suffit pas. Les facteurs dominants changent selon l'horizon. Le système doit le capturer.

---

## Objectif final mesurable

Le projet est un succès si on peut dire :

> "J'ai construit une plateforme AutoML générique pour séries temporelles. Je l'ai appliquée au marché du maïs CBOT sur 15 ans de données. Le système identifie les facteurs explicatifs du prix, prédit l'évolution à J+5, J+10, J+20 et J+30 avec des intervalles calibrés à 90 %, et produit une recommandation de vente agricole qui améliore le revenu de X % par rapport à la vente à la récolte, en capturant en moyenne Y % du prix maximum annuel."

Les métriques X et Y restent à remplir par le backtest. Mais la phrase doit être vraie.

---

## Ce qui existe aujourd'hui

### Implémenté et fonctionnel

| Composant | Fichier | État |
|---|---|---|
| Pipeline de collecte (11 collecteurs) | `src/mais/collect/` | ✅ |
| Features brutes (marché, météo, WASDE, FRED, NASS) | `src/mais/features/__init__.py` | ✅ |
| Facteurs synthétiques (32 facteurs, 9 familles) | `src/mais/features/factors.py` | ✅ |
| Anti-leakage audit automatisé | `src/mais/leakage/audit.py` | ✅ |
| Walk-forward avec embargo | `src/mais/study/professional.py` | ✅ |
| Benchmarks (Ridge, RF, HGB, ElasticNet) | `src/mais/study/professional.py` | ✅ |
| LightGBM + XGBoost dans benchmarks | `src/mais/study/professional.py` | ✅ |
| SHAP via TreeExplainer | `src/mais/study/professional.py` | ✅ |
| CQR (Conformalized Quantile Regression) | `src/mais/meta/cqr.py` | ✅ |
| Markov-switching 3 états | `src/mais/study/professional.py` | ✅ |
| Stacking Ridge sur meta-database | `src/mais/meta/stacking.py` | ✅ |
| Décision agriculteur SELL/STORE/WAIT | `src/mais/decision/` | ✅ |
| CFTC COT collecteur | `src/mais/collect/cftc_cot_collector.py` | ✅ |
| Daily ops pipeline | `src/mais/ops/daily.py` | ✅ |
| Streamlit UI | `src/mais/ui/app.py` | ✅ |

### Présent mais incomplet

| Composant | Problème | Priorité |
|---|---|---|
| EIA éthanol | Nécessite clé API réelle — proxy actif | Haute |
| Rebuild post-paliers | Code OK, data pas encore rebuiltée | Critique |
| Crop Progress / Drought Monitor | Collecteurs présents mais pas dans features | Haute |
| Basis locale | Pas de collecteur | Moyenne |
| Export FAS | Collecteur présent | Moyenne |
| Rapport quotidien | ops/daily.py existe mais pas intégré | Moyenne |

### Non implémenté

| Composant | Où en est-on |
|---|---|
| Plateforme AutoML générique | Vision définie, code spécifique maïs uniquement |
| Backtest agriculteur complet | Partiel dans decision/backtest.py |
| Optimisation Optuna | optimize/ existe, non câblé dans study |
| Prix cash / basis | Pas de données |
| Profiler CSV automatique | optimize/profiler.py existe, non testé |

---

## Prochaines décisions à prendre

1. **Séparation physique du code** : doit-on séparer `automl_platform/` et `maize_study/` dans l'arborescence, ou garder `src/mais/` unifié avec une logique `platform/` vs `study/` ?

2. **Périmètre AutoML v1** : quels types de problèmes la v1 doit-elle couvrir ? Régression tabulaire + série temporelle univariée uniquement, ou déjà multi-classe ?

3. **Backtest économique** : travailler sur prix CBOT ou intégrer basis locale dès maintenant ?

4. **Optuna** : activer l'optimisation dans l'étude maïs dès le prochain rebuild, ou attendre la plateforme générique ?
