# META MODEL PREMIUM V6

> Meta-model premium utilisant uniquement des meta-features OOF.

- Best target : `y_rel_outperform_h90`
- Best set : `classic_plus_meta`
- Best n : 503
- Best AUC : 0.9372401888254773
- Best top20 : 0.97
- Best contexte étroit : `y_rel_outperform_when_basis_extreme_h90` (n=29, AUC=1.0)
- Meilleur gain meta vs classic : `y_rel_outperform_h40` +0.020863847931517077 AUC
- Lecture : OOF meta-features materially improve at least one premium target.

## Results

| Target | Set | n | AUC | dAUC | BA | Top20 | ECE |
|---|---|---:|---:|---:|---:|---:|---:|
| `y_rel_outperform_h40` | `classic` | 503 | 0.768 | 0.000 | 0.754 | 0.800 | 0.190 |
| `y_rel_outperform_h40` | `meta_only` | 503 | 0.789 | 0.021 | 0.702 | 0.860 | 0.121 |
| `y_rel_outperform_h40` | `classic_plus_meta` | 503 | 0.783 | 0.015 | 0.725 | 0.840 | 0.175 |
| `y_rel_outperform_h40` | `meta_plus_basis` | 503 | 0.769 | 0.001 | 0.686 | 0.830 | 0.147 |
| `y_rel_outperform_h40` | `full_stack` | 503 | 0.783 | 0.015 | 0.725 | 0.840 | 0.175 |
| `y_rel_outperform_h90` | `classic` | 503 | 0.928 | 0.000 | 0.832 | 0.850 | 0.192 |
| `y_rel_outperform_h90` | `meta_only` | 503 | 0.902 | -0.026 | 0.863 | 0.850 | 0.144 |
| `y_rel_outperform_h90` | `classic_plus_meta` | 503 | 0.937 | 0.010 | 0.854 | 0.970 | 0.121 |
| `y_rel_outperform_h90` | `meta_plus_basis` | 503 | 0.914 | -0.013 | 0.828 | 0.950 | 0.154 |
| `y_rel_outperform_h90` | `full_stack` | 503 | 0.937 | 0.010 | 0.854 | 0.970 | 0.121 |
| `y_rel_outperform_when_basis_extreme_h40` | `classic` | 65 | 0.940 | 0.000 | 0.717 | 1.000 | 0.349 |
| `y_rel_outperform_when_basis_extreme_h40` | `meta_only` | 65 | 0.734 | -0.206 | 0.750 | 1.000 | 0.093 |
| `y_rel_outperform_when_basis_extreme_h40` | `classic_plus_meta` | 65 | 0.954 | 0.014 | 0.833 | 1.000 | 0.050 |
| `y_rel_outperform_when_basis_extreme_h40` | `meta_plus_basis` | 65 | 0.728 | -0.212 | 0.750 | 1.000 | 0.093 |
| `y_rel_outperform_when_basis_extreme_h40` | `full_stack` | 65 | 0.954 | 0.014 | 0.833 | 1.000 | 0.050 |
| `y_rel_outperform_when_basis_extreme_h90` | `classic` | 29 | 1.000 | 0.000 | 1.000 | 1.000 | 0.012 |
| `y_rel_outperform_when_basis_extreme_h90` | `meta_only` | 29 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| `y_rel_outperform_when_basis_extreme_h90` | `classic_plus_meta` | 29 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| `y_rel_outperform_when_basis_extreme_h90` | `meta_plus_basis` | 29 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| `y_rel_outperform_when_basis_extreme_h90` | `full_stack` | 29 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |

## Abstention best model

| Policy | n | Coverage | DA | AUC | BA |
|---|---:|---:|---:|---:|---:|
| `all` | 503 | 1.000 | 0.837 | 0.937 | 0.854 |
| `top40_confidence` | 201 | 0.400 | 0.970 | 0.977 | 0.970 |
| `top20_confidence` | 101 | 0.201 | 0.970 | 0.971 | 0.965 |
| `avoid_roll_proxy_months` | 322 | 0.640 | 0.776 | 0.889 | 0.799 |