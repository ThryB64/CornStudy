# Red-team — scan narration vs chiffres (VN-B2)

Date : 2026-06-03. EXPLANATORY_ONLY. But : repérer les artefacts dont l'`interpretation` « raconte » plus que
ce que mesurent les nombres. Scan ciblé (artefacts à interprétation longue), pas exhaustif.

## Écart CONFIRMÉ et corrigé

- **V105 — event study trigger** : l'interprétation affirmait « *si le CBOT monte … avant que le basis baisse,
  c'est le précurseur central* », alors que les chiffres mesurent **CBOT pré-start = −0.0241** (CBOT_DRIVEN
  −0.0145) → le CBOT **baisse**. **Corrigé (VN-B1)** : texte réécrit, ajout du champ
  `cbot_pre_start_direction=DOWN`, verdict inchangé (NO_CLEAR_SINGLE_PRECURSOR), cohérent avec V106 (score
  inversé). C'était l'unique contradiction franche identifiée.

## Spot-checks — pas d'écart franc

- **V106** (`COMPRESSION_TRIGGER_REFLECTS_ONGOING_NOT_LEADING`) : narration alignée aux chiffres (score
  inversé NONE 0.79 > CONFIRMED 0.60, base rate 0.65, AUC 0.578). OK.
- **V129** (catalyseurs) : counts = texte (CBOT_WEATHER 9 / EU 8 / roll 8 / UNKNOWN 3), 10.3% non attribué. OK.
- **V130** (demi-vie par tier) : 8.3/4.9/3.3 j = texte ; TAR φ cohérents. OK.
- **V131** (reco v3) : confirmés 14.14 vs marginaux 6.09 = texte. OK.
- **V138** (horizon) : NÉGATIF déjà honnête (analytique sous-prédit, corr ≈ 0, WATCHLIST). OK.
- **V108** (basis reconstruit) : erreur 0.4 €/t = texte. OK.

## Méthode et limite

Scan manuel ciblé sur les artefacts à `interpretation` riche. Une vérification automatique systématique
(parser chaque artefact et comparer signes/valeurs cités vs champs) est notée comme amélioration possible
mais non bloquante. Aucun autre écart narration/chiffres franc trouvé à ce stade.

Règle de prévention : toute `interpretation` doit citer le signe/valeur réel du champ correspondant ; les
hypothèses (« si X alors Y ») ne doivent pas être formulées comme des conclusions quand le champ mesuré dit
l'inverse.
