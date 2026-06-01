# Benchmark canonique V3

Statut : généré par `mais.research.canonical_benchmark`.

## Contradiction sweep / zoo

Cause primaire identifiée : `hyperparams_or_model_family`.
Features sweep : 288 ; features zoo : 288.

## Résultats canoniques

| Split | Horizon | Modèle | DA | IC95 DA | AUC | IC95 AUC | DA hebdo | Verdict |
|---|---:|---|---:|---|---:|---|---:|---|
| crop_year_walk_forward | J+28 | extratrees | 0.551 | [0.536; 0.564] | 0.573 | [0.556; 0.591] | 0.548 | CONFIRMÉ |
| crop_year_walk_forward | J+28 | gaussian_nb | 0.541 | [0.525; 0.556] | 0.558 | [0.540; 0.575] | 0.550 | CONFIRMÉ |
| crop_year_walk_forward | J+28 | histgb | 0.525 | [0.510; 0.540] | 0.554 | [0.538; 0.571] | 0.509 | CONFIRMÉ |
| crop_year_walk_forward | J+28 | lasso | 0.512 | [0.498; 0.528] | 0.520 | [0.503; 0.537] | 0.498 | NEUTRE |
| crop_year_walk_forward | J+28 | lgbm | 0.515 | [0.501; 0.531] | 0.539 | [0.523; 0.557] | 0.499 | CONFIRMÉ |
| crop_year_walk_forward | J+28 | logistic | 0.446 | [0.431; 0.460] | 0.469 | [0.452; 0.486] | 0.439 | REJETÉ |
| crop_year_walk_forward | J+28 | ridge | 0.463 | [0.449; 0.477] | 0.474 | [0.456; 0.492] | 0.454 | REJETÉ |
| crop_year_walk_forward | J+35 | extratrees | 0.573 | [0.559; 0.589] | 0.623 | [0.607; 0.640] | 0.561 | CONFIRMÉ |
| crop_year_walk_forward | J+35 | gaussian_nb | 0.564 | [0.550; 0.578] | 0.564 | [0.548; 0.581] | 0.552 | CONFIRMÉ |
| crop_year_walk_forward | J+35 | histgb | 0.509 | [0.495; 0.525] | 0.545 | [0.529; 0.562] | 0.508 | NEUTRE |
| crop_year_walk_forward | J+35 | lasso | 0.525 | [0.511; 0.540] | 0.527 | [0.509; 0.545] | 0.510 | CONFIRMÉ |
| crop_year_walk_forward | J+35 | lgbm | 0.495 | [0.480; 0.510] | 0.535 | [0.519; 0.552] | 0.498 | NEUTRE |
| crop_year_walk_forward | J+35 | logistic | 0.491 | [0.475; 0.507] | 0.507 | [0.489; 0.526] | 0.502 | NEUTRE |
| crop_year_walk_forward | J+35 | ridge | 0.473 | [0.458; 0.488] | 0.461 | [0.444; 0.479] | 0.479 | REJETÉ |
| crop_year_walk_forward | J+40 | extratrees | 0.580 | [0.565; 0.595] | 0.619 | [0.602; 0.635] | 0.564 | CONFIRMÉ |
| crop_year_walk_forward | J+40 | gaussian_nb | 0.574 | [0.559; 0.589] | 0.584 | [0.568; 0.601] | 0.567 | CONFIRMÉ |
| crop_year_walk_forward | J+40 | histgb | 0.540 | [0.525; 0.555] | 0.556 | [0.539; 0.573] | 0.535 | CONFIRMÉ |
| crop_year_walk_forward | J+40 | lasso | 0.527 | [0.513; 0.542] | 0.534 | [0.516; 0.551] | 0.513 | CONFIRMÉ |
| crop_year_walk_forward | J+40 | lgbm | 0.541 | [0.526; 0.557] | 0.561 | [0.544; 0.578] | 0.524 | CONFIRMÉ |
| crop_year_walk_forward | J+40 | logistic | 0.504 | [0.488; 0.519] | 0.520 | [0.502; 0.539] | 0.504 | NEUTRE |
| crop_year_walk_forward | J+40 | ridge | 0.489 | [0.473; 0.504] | 0.492 | [0.474; 0.509] | 0.488 | NEUTRE |
| crop_year_walk_forward | J+45 | extratrees | 0.563 | [0.548; 0.578] | 0.593 | [0.577; 0.610] | 0.568 | CONFIRMÉ |
| crop_year_walk_forward | J+45 | gaussian_nb | 0.552 | [0.537; 0.567] | 0.558 | [0.541; 0.575] | 0.544 | CONFIRMÉ |
| crop_year_walk_forward | J+45 | histgb | 0.541 | [0.527; 0.557] | 0.590 | [0.573; 0.607] | 0.539 | CONFIRMÉ |
| crop_year_walk_forward | J+45 | lasso | 0.547 | [0.532; 0.562] | 0.552 | [0.534; 0.570] | 0.539 | CONFIRMÉ |
| crop_year_walk_forward | J+45 | lgbm | 0.542 | [0.528; 0.558] | 0.571 | [0.555; 0.588] | 0.529 | CONFIRMÉ |
| crop_year_walk_forward | J+45 | logistic | 0.507 | [0.491; 0.522] | 0.523 | [0.504; 0.540] | 0.510 | NEUTRE |
| crop_year_walk_forward | J+45 | ridge | 0.504 | [0.489; 0.518] | 0.475 | [0.457; 0.493] | 0.507 | NEUTRE |
| crop_year_walk_forward | J+60 | extratrees | 0.619 | [0.605; 0.633] | 0.624 | [0.606; 0.640] | 0.616 | CONFIRMÉ |
| crop_year_walk_forward | J+60 | gaussian_nb | 0.544 | [0.529; 0.559] | 0.562 | [0.545; 0.579] | 0.546 | CONFIRMÉ |
| crop_year_walk_forward | J+60 | histgb | 0.624 | [0.609; 0.638] | 0.675 | [0.659; 0.690] | 0.616 | CONFIRMÉ |
| crop_year_walk_forward | J+60 | lasso | 0.521 | [0.506; 0.535] | 0.544 | [0.526; 0.560] | 0.508 | CONFIRMÉ |
| crop_year_walk_forward | J+60 | lgbm | 0.608 | [0.595; 0.623] | 0.653 | [0.636; 0.668] | 0.601 | CONFIRMÉ |
| crop_year_walk_forward | J+60 | logistic | 0.510 | [0.495; 0.524] | 0.537 | [0.519; 0.553] | 0.503 | NEUTRE |
| crop_year_walk_forward | J+60 | ridge | 0.512 | [0.497; 0.526] | 0.505 | [0.487; 0.523] | 0.508 | NEUTRE |
| kfold_no_shuffle | J+28 | extratrees | 0.543 | [0.529; 0.555] | 0.548 | [0.533; 0.564] | 0.540 | CONFIRMÉ |
| kfold_no_shuffle | J+28 | gaussian_nb | 0.538 | [0.524; 0.551] | 0.501 | [0.485; 0.515] | 0.545 | CONFIRMÉ |
| kfold_no_shuffle | J+28 | histgb | 0.549 | [0.536; 0.562] | 0.554 | [0.538; 0.569] | 0.545 | CONFIRMÉ |
| kfold_no_shuffle | J+28 | lasso | 0.490 | [0.477; 0.502] | 0.524 | [0.509; 0.540] | 0.501 | NEUTRE |
| kfold_no_shuffle | J+28 | lgbm | 0.523 | [0.510; 0.536] | 0.544 | [0.528; 0.559] | 0.519 | CONFIRMÉ |
| kfold_no_shuffle | J+28 | logistic | 0.528 | [0.515; 0.542] | 0.546 | [0.531; 0.561] | 0.524 | CONFIRMÉ |
| kfold_no_shuffle | J+28 | ridge | 0.563 | [0.550; 0.576] | 0.591 | [0.575; 0.606] | 0.554 | CONFIRMÉ |
| kfold_no_shuffle | J+35 | extratrees | 0.549 | [0.537; 0.562] | 0.567 | [0.552; 0.582] | 0.550 | CONFIRMÉ |
| kfold_no_shuffle | J+35 | gaussian_nb | 0.560 | [0.547; 0.572] | 0.527 | [0.512; 0.541] | 0.544 | CONFIRMÉ |
| kfold_no_shuffle | J+35 | histgb | 0.542 | [0.528; 0.554] | 0.553 | [0.536; 0.569] | 0.544 | CONFIRMÉ |
| kfold_no_shuffle | J+35 | lasso | 0.505 | [0.492; 0.518] | 0.543 | [0.529; 0.559] | 0.512 | NEUTRE |
| kfold_no_shuffle | J+35 | lgbm | 0.548 | [0.534; 0.561] | 0.566 | [0.550; 0.581] | 0.555 | CONFIRMÉ |
| kfold_no_shuffle | J+35 | logistic | 0.539 | [0.526; 0.552] | 0.565 | [0.550; 0.580] | 0.558 | CONFIRMÉ |
| kfold_no_shuffle | J+35 | ridge | 0.576 | [0.564; 0.590] | 0.610 | [0.597; 0.626] | 0.583 | CONFIRMÉ |
| kfold_no_shuffle | J+40 | extratrees | 0.555 | [0.542; 0.567] | 0.589 | [0.573; 0.603] | 0.548 | CONFIRMÉ |
| kfold_no_shuffle | J+40 | gaussian_nb | 0.566 | [0.554; 0.579] | 0.537 | [0.524; 0.551] | 0.568 | CONFIRMÉ |
| kfold_no_shuffle | J+40 | histgb | 0.514 | [0.501; 0.527] | 0.518 | [0.504; 0.533] | 0.519 | CONFIRMÉ |
| kfold_no_shuffle | J+40 | lasso | 0.497 | [0.484; 0.510] | 0.541 | [0.526; 0.555] | 0.505 | NEUTRE |
| kfold_no_shuffle | J+40 | lgbm | 0.507 | [0.493; 0.520] | 0.520 | [0.506; 0.535] | 0.518 | NEUTRE |
| kfold_no_shuffle | J+40 | logistic | 0.520 | [0.506; 0.534] | 0.551 | [0.536; 0.567] | 0.525 | CONFIRMÉ |
| kfold_no_shuffle | J+40 | ridge | 0.577 | [0.564; 0.590] | 0.615 | [0.600; 0.630] | 0.587 | CONFIRMÉ |
| kfold_no_shuffle | J+45 | extratrees | 0.528 | [0.516; 0.541] | 0.565 | [0.550; 0.579] | 0.531 | CONFIRMÉ |
| kfold_no_shuffle | J+45 | gaussian_nb | 0.560 | [0.547; 0.572] | 0.532 | [0.517; 0.547] | 0.565 | CONFIRMÉ |
| kfold_no_shuffle | J+45 | histgb | 0.570 | [0.558; 0.582] | 0.574 | [0.560; 0.588] | 0.577 | CONFIRMÉ |
| kfold_no_shuffle | J+45 | lasso | 0.500 | [0.488; 0.514] | 0.550 | [0.536; 0.565] | 0.499 | NEUTRE |
| kfold_no_shuffle | J+45 | lgbm | 0.567 | [0.554; 0.578] | 0.578 | [0.564; 0.592] | 0.576 | CONFIRMÉ |
| kfold_no_shuffle | J+45 | logistic | 0.539 | [0.526; 0.552] | 0.564 | [0.550; 0.580] | 0.542 | CONFIRMÉ |
| kfold_no_shuffle | J+45 | ridge | 0.612 | [0.600; 0.626] | 0.628 | [0.614; 0.644] | 0.619 | CONFIRMÉ |
| kfold_no_shuffle | J+60 | extratrees | 0.575 | [0.563; 0.588] | 0.590 | [0.576; 0.605] | 0.570 | CONFIRMÉ |
| kfold_no_shuffle | J+60 | gaussian_nb | 0.548 | [0.535; 0.560] | 0.542 | [0.527; 0.556] | 0.545 | CONFIRMÉ |
| kfold_no_shuffle | J+60 | histgb | 0.572 | [0.559; 0.584] | 0.571 | [0.556; 0.585] | 0.563 | CONFIRMÉ |
| kfold_no_shuffle | J+60 | lasso | 0.499 | [0.486; 0.511] | 0.561 | [0.546; 0.576] | 0.491 | NEUTRE |
| kfold_no_shuffle | J+60 | lgbm | 0.579 | [0.565; 0.591] | 0.577 | [0.563; 0.592] | 0.576 | CONFIRMÉ |
| kfold_no_shuffle | J+60 | logistic | 0.554 | [0.541; 0.567] | 0.582 | [0.568; 0.597] | 0.555 | CONFIRMÉ |
| kfold_no_shuffle | J+60 | ridge | 0.529 | [0.516; 0.542] | 0.590 | [0.576; 0.606] | 0.527 | CONFIRMÉ |
