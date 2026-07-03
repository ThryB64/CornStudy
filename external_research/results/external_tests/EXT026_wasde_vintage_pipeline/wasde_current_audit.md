# Audit anti-fuite — WASDE quotidien interne (`data/interim/wasde.parquet`)

Rapports croisés : 160 (publication réelle ↔ date de changement de la série quotidienne).

- lag médian (changement − publication) : **-8 jours**
- lag moyen : -5.0 jours
- rapports dont les valeurs apparaissent AVANT la publication réelle : **143/160**
- pire avance (fuite) : -39 jours
- distribution des lags : p10=-8, p50=-8, p90=20

## FUITE DÉTECTÉE

Les valeurs WASDE de la série quotidienne interne sont visibles avant
leur date de publication réelle pour les rapports ci-dessous (extrait) :

     filename publication_date series_change_date  lag_days
wasde0204.txt       2002-04-10         2002-04-02        -8
wasde0205.txt       2002-05-10         2002-05-02        -8
wasde0206.txt       2002-06-10         2002-06-03        -7
wasde0207.txt       2002-07-10         2002-07-02        -8
wasde0208.txt       2002-08-12         2002-08-02       -10
wasde0209.txt       2002-09-12         2002-09-03        -9
wasde0210.txt       2002-10-11         2002-10-02        -9
wasde0211.txt       2002-11-12         2002-11-04        -8
wasde0212.txt       2002-12-10         2002-12-02        -8
wasde0301.txt       2003-01-10         2003-01-02        -8
wasde0302.txt       2003-02-10         2003-02-03        -7
wasde0303.txt       2003-03-10         2003-03-03        -7
wasde0304.txt       2003-04-10         2003-04-02        -8
wasde0306.txt       2003-06-10         2003-06-02        -8
wasde0307.txt       2003-07-10         2003-07-02        -8

Cause vraisemblable : expansion quotidienne calée sur `report_date`
(1er du mois dans le parse) au lieu de la date de publication réelle
(~8-12 du mois). Correction à proposer via ticket projet séparé :
recaler l'expansion sur `publication_date` + 1 jour ouvré.
