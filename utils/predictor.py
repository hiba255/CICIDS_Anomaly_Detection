import joblib
import numpy as np
import pandas as pd
import shap

from pathlib import Path

# Chemin absolu vers les modèles
BASE_DIR = Path(__file__).parent.parent

model = joblib.load(BASE_DIR / 'models/best_model.pkl')
scaler = joblib.load(BASE_DIR / 'models/scaler.pkl')
le = joblib.load(BASE_DIR / 'models/label_encoder.pkl')
# SHAP explainer
explainer = shap.TreeExplainer(model)

def predict(df: pd.DataFrame):
    """
    Prédit le type d'attaque et retourne les top features SHAP
    """
    # Prétraitement
    X = scaler.transform(df.values)
    
    # Prédiction
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)
    
    # SHAP values
    shap_values = explainer.shap_values(X)
    
    results = []
    for i in range(len(predictions)):
        # Label prédit
        attack_type = le.inverse_transform([predictions[i]])[0]
        confidence = float(probabilities[i].max())
        
        # Top 3 features SHAP pour cette prédiction
        class_idx = predictions[i]
        shap_row = shap_values[i, :, class_idx]
        top_indices = np.argsort(np.abs(shap_row))[-3:][::-1]
        
        top_features = [
            {
                "feature": df.columns[j] if hasattr(df, 'columns') else f"feature_{j}",
                "shap_value": round(float(shap_row[j]), 4)
            }
            for j in top_indices
        ]
        
        results.append({
            "attack_type": attack_type,
            "confidence": round(confidence, 4),
            "is_anomaly": attack_type != "Normal Traffic",
            "top_features": top_features
        })
    
    return {
        "total": len(results),
        "anomalies": sum(1 for r in results if r['is_anomaly']),
        "normal": sum(1 for r in results if not r['is_anomaly']),
        "results": results
    }