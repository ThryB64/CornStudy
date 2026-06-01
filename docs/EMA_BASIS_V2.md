# EMA BASIS V2

> Résultat principal EMA Phase 2. Source exploratoire/proxy, validation OOF stricte.

## Verdict

- Basis moyen : 37.25 €/t.
- Basis positif : 98.9% du temps.
- AR(1) phi : 0.970, demi-vie : 22.8 jours.
- Meilleur signal OOF daily : H60 z>2.0 hit-rate 79.2%.

## Règle anti-confusion

Le basis peut revenir vers sa moyenne de 3 façons : EMA baisse, CBOT monte, ou les deux évoluent ensemble. basis_reversion ≠ EMA up.

## Validation OOF

| Fréquence | Horizon | Seuil | n | DA | IC95 | q BH | Verdict |
|---|---:|---:|---:|---:|---|---:|---|
| daily | 20 | 1.0 | 791 | 60.3% | [58.7%; 61.5%] | 0.000 | GO |
| daily | 20 | 1.5 | 303 | 61.4% | [58.3%; 64.5%] | 0.000 | GO |
| daily | 20 | 2.0 | 107 | 73.8% | [67.6%; 80.2%] | 0.000 | GO |
| daily | 20 | 2.5 | 26 | 65.4% | [48.1%; 83.7%] | 0.092 | NO_GO |
| daily | 40 | 1.0 | 688 | 59.2% | [58.1%; 60.3%] | 0.000 | GO |
| daily | 40 | 1.5 | 259 | 61.4% | [58.8%; 64.1%] | 0.000 | GO |
| daily | 40 | 2.0 | 74 | 74.3% | [65.8%; 81.1%] | 0.000 | GO |
| daily | 40 | 2.5 | 15 | 60.0% | [40.8%; 79.2%] | 0.304 | NO_GO |
| daily | 60 | 1.0 | 575 | 58.6% | [56.8%; 60.4%] | 0.000 | GO |
| daily | 60 | 1.5 | 198 | 64.6% | [61.1%; 68.2%] | 0.000 | GO |
| daily | 60 | 2.0 | 48 | 79.2% | [69.4%; 88.0%] | 0.000 | GO |
| daily | 60 | 2.5 | 13 | 76.9% | [53.8%; 100.0%] | 0.055 | GO |