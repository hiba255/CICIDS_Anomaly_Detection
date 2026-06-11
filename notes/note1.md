#  Summary - EDA & Preprocessing

## Dataset
- Source: CICIDS2017 (Kaggle - cleaned version)
- Shape: 2,520,751 rows x 53 columns
- Target column: `Attack Type`

## Classes (7 total)
| Class | Count | Percentage |
|-------|-------|------------|
| Normal Traffic | 2,095,057 | 83.11% |
| DoS | 193,745 | 7.69% |
| DDoS | 128,014 | 5.08% |
| Port Scanning | 90,694 | 3.60% |
| Brute Force | 9,150 | 0.36% |
| Web Attacks | 2,143 | 0.09% |
| Bots | 1,948 | 0.08% |

## Data Quality
- Missing values: 0
- Infinite values: 0
- Duplicates: 161 → removed

## Preprocessing
- Label encoding applied on `Attack Type`
- Train/test split: 80/20 stratified
- StandardScaler applied on X_train and X_test

## Observations
- Dataset is highly imbalanced (Normal Traffic = 83%)
- SMOTE will be applied in Week 2 to balance classes
- Several correlated features detected in heatmap

## Saved Files
- `data/cicids_clean.csv`
- `data/X_train.pkl`, `data/X_test.pkl`
- `data/y_train.pkl`, `data/y_test.pkl`
- `models/scaler.pkl`
- `models/label_encoder.pkl`