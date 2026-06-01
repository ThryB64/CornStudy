# Protocole de backtest agriculteur

## Question centrale

> Le système améliore-t-il réellement le revenu des agriculteurs par rapport à des stratégies simples ?

Un modèle qui bat les baselines statistiques mais ne génère pas de gain économique ne sert à rien. Ce document définit comment mesurer le gain économique de façon rigoureuse.

---

## Contexte économique

### Prix CBOT vs prix cash

Le prix CBOT est un prix de futures Chicago. Le prix réel qu'un agriculteur obtient est :

```
Prix cash local = Prix CBOT front-month + Basis locale
```

La **basis** = prix local − prix futures. Elle reflète :
- Coûts de transport vers le marché
- Offre/demande locale
- Qualité du grain
- Disponibilité de stockage

**Idéalement**, le backtest travaille sur le prix cash. En l'absence de données basis, on travaille sur le futures CBOT en conservant ce biais documenté.

### Coûts de stockage

Stocker du maïs coûte :
- **Coût financier** : immobilisation du grain → taux d'intérêt appliqué
- **Coût physique** : espace silo, électricité, assurance ≈ 0.03–0.04 $/bu/mois
- **Risque qualité** : perte d'humidité, mycotoxines si mauvaise conservation

```
Coût stockage total par mois ≈ 0.03 à 0.05 $/bu
```

Pour un horizon de 6 mois, le stockage coûte ≈ 0.20 $/bu. Si le marché ne monte pas de ce montant, stocker n'a pas de sens.

---

## Stratégies de vente à backtester

### Stratégie 0 — Vente totale à la récolte (baseline absolue)

```
Vendre 100% du grain à la récolte (octobre-novembre)
```

C'est la référence la plus simple. Un agriculteur qui ne fait rien. Le système n'est utile que s'il bat ça.

### Stratégie 1 — Vente mensuelle régulière

```
Vendre 1/12 de la production chaque mois
```

Simple, élimine le risque de timing. Capture la moyenne annuelle.

### Stratégie 2 — Vente par tiers

```
- 1/3 à la récolte
- 1/3 en janvier-février
- 1/3 en mai-juin
```

Stratégie répandue dans les coopératives françaises.

### Stratégie 3 — Vente au meilleur mois historique

```
Toujours vendre au mois historiquement le plus haut (en moyenne)
```

Exemple : si mai est en moyenne le mois le plus haut → vendre tout en mai.

### Stratégie 4 — Vente selon signal modèle

```
Si signal modèle > seuil_vente → vendre fraction_vente
Si signal modèle < seuil_stockage → stocker
Sinon → attendre
```

C'est la stratégie du système.

### Stratégie 5 — Vente selon modèle + incertitude CQR

```
Si q_lo > 0 (même le pessimiste anticipe une hausse) → stocker
Si q_hi < 0 (même l'optimiste anticipe une baisse) → vendre
Si q_lo < 0 et q_hi > 0 → attendre ou vendre fraction réduite
```

Version plus prudente qui utilise l'intervalle de confiance.

### Stratégie 6 — Perfect hindsight (référence théorique)

```
Vendre 100% au jour où le prix annuel est maximum
```

Impossible en pratique mais utile comme borne supérieure. Mesure le "regret théorique maximum".

---

## Métriques économiques

### Métriques de base

| Métrique | Formule | Interprétation |
|---|---|---|
| `price_obtained` | Prix moyen de vente pondéré par volume | Prix moyen effectif |
| `revenue_per_bu` | `price_obtained` | Revenu par boisseau |
| `revenue_per_acre` | `price_obtained × yield_bu_acre` | Revenu total par acre |

### Métriques de comparaison

| Métrique | Formule | Interprétation |
|---|---|---|
| `gain_vs_harvest` | `price_obtained - harvest_price` | Gain vs vente récolte |
| `gain_vs_monthly` | `price_obtained - monthly_avg` | Gain vs vente mensuelle |
| `gain_vs_thirds` | `price_obtained - thirds_price` | Gain vs vente par tiers |

### Métriques de qualité

| Métrique | Formule | Interprétation |
|---|---|---|
| `pct_years_winning` | % années où la stratégie bat la vente récolte | Fiabilité |
| `worst_year_gain` | Pire gain / perte en $/bu | Risque downside |
| `max_drawdown` | Max peak-to-trough du revenu | Risque de séquence |

### Métrique principale — Capture Rate

```python
# Pour chaque année
annual_max_price = prices.loc[year].max()
price_obtained = weighted_avg(prices, sell_dates, volumes)
capture_rate = price_obtained / annual_max_price

# Sur tout le backtest
mean_capture_rate = capture_rates.mean()
std_capture_rate = capture_rates.std()
```

**Interprétation :**
- Perfect hindsight : 100%
- Vente récolte : ≈ 65-75% historiquement
- Vente mensuelle : ≈ 72-80%
- Objectif système : ≈ 80-88%

**Phrase cible du projet :**
> "Notre système capture en moyenne 84% du prix maximum annuel, contre 70% pour la vente à la récolte."

### Métrique regret

```python
regret = annual_max_price - price_obtained
regret_pct = regret / annual_max_price
```

Plus le regret est faible, mieux c'est.

---

## Contraintes réalistes du modèle de backtest

Un agriculteur n'est pas libre de vendre n'importe quand. Il faut intégrer :

### Contraintes de stockage

```python
StorageConfig(
    capacity_bu: int,           # capacité silo en boisseau
    cost_per_bu_per_month: float = 0.04,   # $/bu/mois
    max_months: int = 8,        # durée max de stockage
    quality_loss_rate: float = 0.005,      # 0.5% perte/mois qualité
)
```

### Contraintes de trésorerie

```python
CashflowConfig(
    min_pct_to_sell_by_jan: float = 0.30,  # 30% minimum vendu avant janvier
    debt_service_date: list[str],           # dates de remboursement contraintes
    operating_cost_monthly: float,          # besoin mensuel de liquidités
)
```

### Paramétrage agriculteur

```python
FarmerProfile(
    risk_aversion: str = "medium",  # low / medium / high
    storage_capacity: str = "full", # full / partial / none
    typical_yield_bu: float = 170.0,
    acres: int = 500,
    selling_horizon_months: int = 8,
)
```

---

## Période du backtest

| Période | Usage |
|---|---|
| 2000–2005 | Calibration des stratégies simples |
| 2006–2012 | Supercycle des matières premières (test de robustesse) |
| 2013–2020 | Walk-forward principal |
| 2021–2025 | Validation finale out-of-sample |

**Minimum requis :** le backtest doit couvrir au moins 10 années complètes de campagnes agricoles pour être statistiquement défendable.

---

## Livrables du backtest

### Tableaux

1. **Résultats par stratégie et par année** : prix obtenu, capture rate, revenu/acre
2. **Résumé agrégé** : moyenne, std, % années gagnantes, pire/meilleure année
3. **Comparaison des stratégies** : classement par capture rate moyen

### Graphiques

1. Prix obtenus vs prix maximum annuel (scatter par année)
2. Distribution des capture rates par stratégie (violin plot)
3. Évolution du revenu cumulé par stratégie (courbes)
4. Gain/perte annuel vs vente récolte (barres)

### Rapport texte

```markdown
## Résultats du backtest agriculteur

Période : 2013–2025 (12 années complètes)

| Stratégie | Capture rate | Revenu/bu | vs Récolte |
|---|---|---|---|
| Vente récolte | 70.3% | 3.82 $/bu | référence |
| Vente mensuelle | 75.1% | 4.08 $/bu | +0.26 $/bu |
| Vente par tiers | 76.4% | 4.15 $/bu | +0.33 $/bu |
| Système modèle | 83.2% | 4.52 $/bu | +0.70 $/bu |
| Système + CQR | 81.5% | 4.43 $/bu | +0.61 $/bu |
| Perfect hindsight | 100% | 5.43 $/bu | +1.61 $/bu |
```

*(Chiffres illustratifs — à remplacer par les vrais résultats)*

---

## Ce que le backtest ne mesure pas

Il faut être honnête sur les limites :

- **Slippage** : dans la réalité, vendre 10 000 bushels déplace légèrement le prix local.
- **Basis risk** : on travaille sur CBOT, pas sur le prix cash réel de l'agriculteur.
- **Coûts de transaction** : commissions de courtage non modélisées.
- **Timing intra-journalier** : on suppose une vente au prix de clôture.
- **Opportunités non saisies** : si la capacité de stockage est pleine, impossible de profiter d'une hausse tardive.
