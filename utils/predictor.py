import joblib
import pandas as pd
import numpy as np
import os

BASE_DIR = r"C:\Users\chouc\cicids-project"

model_path = os.path.join(BASE_DIR, 'models/best_model.json')
from xgboost import XGBClassifier
model = XGBClassifier()
model.load_model(model_path)

scaler = joblib.load(os.path.join(BASE_DIR, 'models/scaler.pkl'))
label_encoder = joblib.load(os.path.join(BASE_DIR, 'models/label_encoder.pkl'))

# Load feature importance
importance_dict = model.get_booster().get_score(importance_type='gain')
df_clean = pd.read_csv(os.path.join(BASE_DIR, 'data/cicids_clean.csv'))
feature_cols = [col for col in df_clean.columns if col not in ['Attack Type', 'label']]
model.get_booster().feature_names = feature_cols

importance_df = pd.DataFrame({
    'feature': list(importance_dict.keys()),
    'importance': list(importance_dict.values())
}).sort_values('importance', ascending=False)

TOP3_FEATURES = importance_df.head(3)['feature'].tolist()

def predict(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input: raw (unscaled) DataFrame
    Output: DataFrame with prediction, confidence and top 3 features
    """
    X_scaled = scaler.transform(df)
    y_pred = model.predict(X_scaled)
    y_proba = model.predict_proba(X_scaled)
    y_labels = label_encoder.inverse_transform(y_pred)
    confidence = np.max(y_proba, axis=1)

    result = pd.DataFrame({
        'prediction': y_labels,
        'confidence': confidence.round(4),
        'top_features': [TOP3_FEATURES] * len(y_labels)
    })
    return result