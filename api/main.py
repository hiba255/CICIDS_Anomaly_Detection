from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from fastapi import Request

sys.path.append(str(Path(__file__).parent.parent))

from utils.predictor import predict
from api.auth import create_access_token, get_current_user, verify_password, USERS_DB
from api.database import SessionLocal, Prediction, init_db

# Initialize database
init_db()

app = FastAPI(
    title="CICIDS2017 - Network Attack Detection API",
    description="Detects network attacks using XGBoost + SHAP explanations",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "message": "Network Attack Detection API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/model-info")
def model_info():
    return {
        "model": "XGBoost",
        "dataset": "CICIDS2017",
        "accuracy": 99.88,
        "classes": ["Bots", "Brute Force", "DDoS", "DoS", "Normal Traffic", "Port Scanning", "Web Attacks"]
    }

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = USERS_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}

class PredictRequest(BaseModel):
    data: list[dict]

@app.post("/predict")
def predict_endpoint(
    request: PredictRequest,
    current_user: dict = Depends(get_current_user)
):
    df = pd.DataFrame(request.data)
    result = predict(df)
    result["requested_by"] = current_user["username"]

    # Save to database
    db = SessionLocal()
    for r in result["results"]:
        prediction = Prediction(
            timestamp=datetime.utcnow(),
            username=current_user["username"],
            attack_type=r["attack_type"],
            confidence=r["confidence"],
            is_anomaly=str(r["is_anomaly"]),
            top_features=r["top_features"]
        )
        db.add(prediction)
    db.commit()
    db.close()

    return result

@app.get("/history")
def get_history(current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    predictions = db.query(Prediction).order_by(
        Prediction.timestamp.desc()
    ).limit(50).all()
    db.close()

    return {
        "total": len(predictions),
        "predictions": [
            {
                "id": p.id,
                "timestamp": p.timestamp,
                "username": p.username,
                "attack_type": p.attack_type,
                "confidence": p.confidence,
                "is_anomaly": p.is_anomaly,
                "top_features": p.top_features
            }
            for p in predictions
        ]
    }
@app.post("/predict-live")
async def predict_live(request: Request):
    """
    Receives NFStream flow data and maps it to CICIDS2017 feature names
    """
    data = await request.json()

    # Map NFStream fields -> CICIDS2017 feature names (best-effort mapping)
    mapped = {
        "Destination Port": data.get("dst_port", 0),
        "Flow Duration": data.get("bidirectional_duration_ms", 0) * 1000,  # ms -> microsec approx
        "Total Fwd Packets": data.get("src2dst_packets", 0),
        "Total Length of Fwd Packets": data.get("src2dst_bytes", 0),
        "Fwd Packet Length Max": data.get("src2dst_max_ps", 0),
        "Fwd Packet Length Min": data.get("src2dst_min_ps", 0),
        "Fwd Packet Length Mean": data.get("src2dst_mean_ps", 0),
        "Fwd Packet Length Std": data.get("src2dst_stddev_ps", 0),
        "Bwd Packet Length Max": data.get("dst2src_max_ps", 0),
        "Bwd Packet Length Min": data.get("dst2src_min_ps", 0),
        "Bwd Packet Length Mean": data.get("dst2src_mean_ps", 0),
        "Bwd Packet Length Std": data.get("dst2src_stddev_ps", 0),
        "Flow Bytes/s": data.get("bidirectional_bytes", 0) / max(data.get("bidirectional_duration_ms", 1)/1000, 0.001),
        "Flow Packets/s": data.get("bidirectional_packets", 0) / max(data.get("bidirectional_duration_ms", 1)/1000, 0.001),
        "Flow IAT Mean": data.get("bidirectional_mean_piat_ms", 0),
        "Flow IAT Std": data.get("bidirectional_stddev_piat_ms", 0),
        "Flow IAT Max": data.get("bidirectional_max_piat_ms", 0),
        "Flow IAT Min": data.get("bidirectional_min_piat_ms", 0),
        "Fwd IAT Total": data.get("src2dst_duration_ms", 0),
        "Fwd IAT Mean": data.get("src2dst_mean_piat_ms", 0),
        "Fwd IAT Std": data.get("src2dst_stddev_piat_ms", 0),
        "Fwd IAT Max": data.get("src2dst_max_piat_ms", 0),
        "Fwd IAT Min": data.get("src2dst_min_piat_ms", 0),
        "Bwd IAT Total": data.get("dst2src_duration_ms", 0),
        "Bwd IAT Mean": data.get("dst2src_mean_piat_ms", 0),
        "Bwd IAT Std": data.get("dst2src_stddev_piat_ms", 0),
        "Bwd IAT Max": data.get("dst2src_max_piat_ms", 0),
        "Bwd IAT Min": data.get("dst2src_min_piat_ms", 0),
        "Fwd Header Length": 0,
        "Bwd Header Length": 0,
        "Fwd Packets/s": data.get("src2dst_packets", 0) / max(data.get("src2dst_duration_ms", 1)/1000, 0.001),
        "Bwd Packets/s": data.get("dst2src_packets", 0) / max(data.get("dst2src_duration_ms", 1)/1000, 0.001),
        "Min Packet Length": data.get("bidirectional_min_ps", 0),
        "Max Packet Length": data.get("bidirectional_max_ps", 0),
        "Packet Length Mean": data.get("bidirectional_mean_ps", 0),
        "Packet Length Std": data.get("bidirectional_stddev_ps", 0),
        "Packet Length Variance": data.get("bidirectional_stddev_ps", 0) ** 2,
        "FIN Flag Count": data.get("bidirectional_fin_packets", 0),
        "PSH Flag Count": data.get("bidirectional_psh_packets", 0),
        "ACK Flag Count": data.get("bidirectional_ack_packets", 0),
        "Average Packet Size": data.get("bidirectional_mean_ps", 0),
        "Subflow Fwd Bytes": data.get("src2dst_bytes", 0),
        "Init_Win_bytes_forward": 0,
        "Init_Win_bytes_backward": 0,
        "act_data_pkt_fwd": data.get("src2dst_packets", 0),
        "min_seg_size_forward": data.get("src2dst_min_ps", 0),
        "Active Mean": 0,
        "Active Max": 0,
        "Active Min": 0,
        "Idle Mean": 0,
        "Idle Max": 0,
        "Idle Min": 0,
    }

    df = pd.DataFrame([mapped])

    try:
        result = predict(df)

        db = SessionLocal()
        for r in result["results"]:
            prediction = Prediction(
                timestamp=datetime.utcnow(),
                username="live-nfstream",
                attack_type=r["attack_type"],
                confidence=r["confidence"],
                is_anomaly=str(r["is_anomaly"]),
                top_features=r["top_features"]
            )
            db.add(prediction)
        db.commit()
        db.close()

        return result

    except Exception as e:
        return {"error": str(e)}