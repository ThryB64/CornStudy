# EXT016 — NBEATSx exogène

**Verdict : NOT_WORTH_YET** (décision disciplinée, non lancé).

## Décision
Le plan autorise NBEATSx uniquement si (a) données suffisantes, (b) protocole walk-forward
clair, (c) temps de calcul raisonnable, (d) comparaison stricte aux modèles simples, et
interdit d'accepter un modèle complexe qui ne bat pas les simples. Trois constats de
l'étape 5 conduisent à NE PAS le lancer maintenant :

1. **Dépendances absentes** : `torch`, `neuralforecast`, `pytorch_lightning` ne sont pas
   installés (vérifié). Installer une stack DL lourde pour un verdict attendu négatif n'est
   pas justifié.
2. **Trop peu d'observations indépendantes** : à H90, les fenêtres de retour se chevauchent
   massivement (~40-60 blocs réellement indépendants sur 2008-2023). Un modèle à forte
   capacité sur-apprendrait — risque déjà matérialisé dans l'étape 5 :
   - EXT050 (stacking, pourtant trivial) **sur-apprend** (DA 1re moitié < 0.5) ;
   - EXT015 : le RandomForest « toutes variables » est **battu** par un logit top-6
     parcimonieux (0.577 vs 0.656 à H90).
3. **Edge faible** : le signal directionnel est de 3-6 pts de DA. La parcimonie gagne
   systématiquement ; rien n'indique qu'un DL exogène ferait mieux que le logit 4-6 variables.

## Condition de réouverture
Rouvrir seulement si : (a) un flux de données plus riche et à plus haute fréquence devient
disponible (intraday, options, courbe — actuellement DATA_BLOCKED), augmentant le nombre
d'observations indépendantes ; (b) les modèles simples (EXT024) sont validés en forward et
qu'on cherche un complément marginal ; (c) avec régularisation forte et comparaison
Giacomini-White stricte à EXT025/EXT024/EXT011. Tant que ce n'est pas le cas : NOT_WORTH_YET.

## Conclusion
Le deep learning n'est pas justifié à ce stade. L'étape 5 montre que **les modèles simples
et interprétables dominent** ; ajouter de la capacité a sur-appris à chaque essai. Reporté.
