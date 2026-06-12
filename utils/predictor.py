import joblib
import pandas as pd
import numpy as np
import os

BASE_DIR = r"C:\Users\chouc\cicids-project"

model = joblib.load(os.path.join(BASE_DIR, 'models/best_model.pkl'))
scaler = joblib.load(os.path.join(BASE_DIR, 'models/scaler.pkl'))
label_encoder = joblib.load(os.path.join(BASE_DIR, 'models/label_encoder.pkl'))

def predict(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input: raw (unscaled) DataFrame
    Output: DataFrame with prediction and confidence
    """
    # Scale first
    X_scaled = scaler.transform(df)
    
    # Predict
    y_pred = model.predict(X_scaled)
    y_proba = model.predict_proba(X_scaled)
    y_labels = label_encoder.inverse_transform(y_pred)
    confidence = np.max(y_proba, axis=1)

    result = pd.DataFrame({
        'prediction': y_labels,
        'confidence': confidence.round(4)
    })
    return result