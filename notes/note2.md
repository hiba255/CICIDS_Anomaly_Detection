#  Summary - Model Training & Comparison

## Models Trained
- Decision Tree
- Random Forest
- XGBoost
- LightGBM

## SMOTE
- Applied on full X_train (2,016,472 rows)
- Balanced shape: 11,731,419 rows
- SMOTE time: 1 minute

## Results

| Model | Train Acc | Test Acc | Diff | Time |
|-------|-----------|----------|------|------|
| Decision Tree | 99.51% | 98.71% | 0.8% | 9 min |
| Random Forest | 100% | 99.87% | 0.13% | 36 min |
| XGBoost | 99.98% | 99.88% | 0.1% | 9 min |
| LightGBM | 98.91% | 97.29% | 1.62% | 8 min |

## Winner : XGBoost 
- Best accuracy: 99.88%
- Lowest overfitting: 0.1%
- Fast training: 9 minutes

## Observations
- SMOTE improved minority classes significantly
- Bots class remains hardest to detect (only 1,948 samples)
- No serious overfitting detected in any model

## Saved Files
- `models/decision_tree.pkl`
- `models/random_forest.pkl`
- `models/xgboost.pkl`
- `models/lightgbm.pkl`
- `models/best_model.pkl`