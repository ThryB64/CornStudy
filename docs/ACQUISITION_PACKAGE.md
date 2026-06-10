# V158 — Package d'acquisition de données (officielles & proxy)

> Prêt à envoyer. Objectif : obtenir un historique EMA officiel (sanctifier le backtest) + enrichir la
> jambe CBOT, en restant non-commercial / recherche étudiante. Voir aussi `.ai/REFLEXION_SUITE_ETUDE.md`
> Partie 6 (sources gratuites) et 8bis.3 (table vendeurs).

## 1. Ordre de bataille

1. **Gratuit d'abord** (aucun e-mail, à brancher tout de suite) : Open‑Meteo (Historical Forecast +
   Previous Runs), NOAA NOMADS, CFTC COT, FranceAgriMer Céré'Obs, JRC MARS / observatoire céréales CE,
   BCE (EUR/USD référence).
2. **Euronext Data Solutions** (sanctifier EMA) : formulaire Web Services + e-mail ci-dessous.
3. **CME DataMine** (jambe CBOT officielle) si besoin avant Euronext.
4. **Barchart** (proxy/intraday exploratoire) en dernier recours low-cost.

## 2. Contacts

| Vendeur | Contact | Produit visé | Coût attendu |
|---|---|---|---|
| Euronext | formulaire Web Services (vérifié) ; `datasolutions@euronext.com` (à reconfirmer) | export historique EMA/EBM (settlement/OHLC/volume/OI) | devis, non public |
| CME Group | `CMEDataSales@cmegroup.com` | DataMine — settlements CBOT corn, profondeur historique | one-off ou abo |
| Barchart | `solutions@barchart.com` | OnDemand getHistory (tick/minute/EOD) | devis ; Premier ~29.95 USD/mois |

## 3. Champs demandés (CSV/Excel)

```
contract_code, expiry, price_date, settlement, open, high, low, close, volume, open_interest, currency
Période : 2014 -> aujourd'hui (au minimum). Toutes échéances listées + expirées si possible.
Produits : Euronext Corn (EMA/DPAR) ; si possible Euronext Milling Wheat (EBM) ; CBOT Corn (ZC).
```

## 4. E-mail Euronext — FR

```
Objet : Demande de données historiques Euronext Corn Futures pour projet étudiant de recherche

Bonjour,

Je mène un projet étudiant de fin d'année consacré à l'étude de la prime entre le contrat maïs
Euronext Paris (Corn Futures / EMA) et le contrat corn CBOT. L'objectif est strictement académique
et non commercial : recherche statistique et économétrique, visualisations, event studies. Aucune
redistribution des données, aucun usage de trading réel.

Je cherche idéalement un export historique quotidien (CSV/Excel) couvrant :
- Euronext Corn Futures (EMA / DPAR), toutes échéances listées et expirées si possible,
- champs : settlement, open, high, low, volume, open interest,
- période : au minimum 2014 à aujourd'hui,
- si disponible, Euronext Milling Wheat (EBM) sur la même période.

Si un accès standard n'est pas adapté à un usage étudiant, un export ponctuel « one-off » ou un
périmètre réduit serait déjà extrêmement utile. Je peux fournir un descriptif académique du projet,
le nom de l'établissement, et signer un engagement d'usage non commercial / non redistribution.

Merci beaucoup pour votre retour et pour toute orientation sur l'offre la plus adaptée.

Cordialement,
[Nom] — [Établissement] — [Email] — [Téléphone]
```

## 5. E-mail Euronext — EN

```
Subject: Request for historical Euronext Corn Futures data for academic research project

Hello,

I am working on a year-end student research project on the premium between Euronext Paris Corn
Futures (EMA) and CBOT corn futures. Strictly academic and non-commercial: statistical/econometric
research, visualisations, event studies. No data redistribution, no live trading.

I am ideally looking for a daily historical export (CSV/Excel) covering:
- Euronext Corn Futures (EMA / DPAR), all listed and expired maturities if possible,
- fields: settlement, open, high, low, volume, open interest,
- period: at least 2014 to present,
- and, if available, Euronext Milling Wheat (EBM) over the same window.

If a standard subscription is not suitable for a student use case, a one-off CSV/Excel extract or a
reduced academic package would already be extremely valuable. I can provide an academic project
description, university details, and sign a non-commercial / non-redistribution undertaking.

Thank you very much for your guidance on the most suitable option.

Best regards,
[Name] — [Institution] — [Email] — [Phone]
```

## 6. E-mail Barchart — EN (proxy/intraday)

```
Subject: Academic research inquiry – historical futures data for Euronext / CBOT corn

Hello,

Student research project on the premium between Euronext corn futures and CBOT corn futures. I am
looking for a strictly non-commercial, low-volume data solution for daily (and if possible minute)
history on CBOT corn and Euronext Paris corn (and milling wheat if available). Use: statistical
research, model validation, event studies. No redistribution, no live trading.

Could you please clarify:
1. whether coverage includes the relevant Euronext symbols;
2. whether end-of-day fields distinguish official settlement from close/last;
3. the lowest-cost option for a student / research-only use case;
4. whether a one-off extract or a short-duration access package is possible.

Thank you,
[Name] — [Institution] — [Email]
```

## 7. E-mail CME DataMine — EN (jambe CBOT)

```
Subject: CME DataMine – academic request for historical CBOT corn settlements

Hello,

For a student research project comparing Euronext and CBOT corn, I would like to obtain historical
daily settlement data for CBOT Corn futures (ZC), all delivery months, ideally 2010 to present.
Strictly academic and non-commercial, no redistribution. Could you advise on a one-off order or an
academic option, and the available history depth and fields (settlement, OHLC, volume, open interest)?

Thank you,
[Name] — [Institution] — [Email]
```

## 8. Engagement d'usage (à joindre si demandé)

```
J'atteste que les données obtenues seront utilisées exclusivement pour un projet étudiant de
recherche, sans usage commercial, sans redistribution à des tiers, sans usage de trading réel, et
seront supprimées sur demande du fournisseur ou à la fin du projet.
```

## 9. Après réception

- Ranger sous `data/raw/<vendor>/` avec un `metadata.json` (source, date, licence, périmètre).
- Lancer **V144** (proxy↔officiel) une fois un overlap disponible → calibrer le biais.
- Re-tester la courbe (V165/V141) et le z officiel rolling une fois l'historique suffisant.

Statut : RESEARCH_ONLY_NOT_TRADING.
