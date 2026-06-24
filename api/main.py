from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import redis
import time

sys.path.append(str(Path(__file__).parent.parent))

from utils.predictor import predict
from api.auth import create_access_token, get_current_user, verify_password, USERS_DB
from api.database import SessionLocal, Prediction, init_db

# Initialize database
init_db()

# Redis connection (service name "redis" from docker-compose)
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

app = FastAPI(
    title="CICIDS2017 - Network Attack Detection API",
    description="Detects network attacks using XGBoost + SHAP explanations",
    version="1.0.0"
)


def track_and_check_port_scan(src_ip: str, dst_port: int, window_seconds: int = 20, threshold: int = 10):
    """
    Tracks distinct destination ports contacted by a source IP
    within a sliding time window. Detects Port Scanning.
    """
    key = f"portscan:{src_ip}"
    now = time.time()

    redis_client.zadd(key, {str(dst_port): now})
    redis_client.zremrangebyscore(key, 0, now - window_seconds)
    redis_client.expire(key, window_seconds)

    distinct_ports = redis_client.zcard(key)
    return distinct_ports >= threshold, distinct_ports


def track_and_check_ddos(src_ip: str, window_seconds: int = 5, threshold: int = 50):
    """
    Tracks total connection attempts from a source IP in a short window.
    A very high connection rate indicates a flood-style DDoS attack.
    """
    key = f"ddos:{src_ip}"
    now = time.time()

    redis_client.zadd(key, {f"{now}-{id(now)}": now})
    redis_client.zremrangebyscore(key, 0, now - window_seconds)
    redis_client.expire(key, window_seconds)

    connection_count = redis_client.zcard(key)
    return connection_count >= threshold, connection_count


def track_and_check_brute_force(src_ip: str, dst_port: int, window_seconds: int = 15, threshold: int = 5):
    """
    Tracks repeated connection attempts from a source IP to the SAME
    port (e.g. SSH=22, FTP=21) within a window. Repeated short-lived
    connections to an auth port indicate brute-force login attempts.
    """
    key = f"bruteforce:{src_ip}:{dst_port}"
    now = time.time()

    redis_client.zadd(key, {f"{now}-{id(now)}": now})
    redis_client.zremrangebyscore(key, 0, now - window_seconds)
    redis_client.expire(key, window_seconds)

    attempt_count = redis_client.zcard(key)
    is_auth_port = dst_port in (22, 21, 23, 3389, 445)  # SSH, FTP, Telnet, RDP, SMB
    return (is_auth_port and attempt_count >= threshold), attempt_count


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
    Receives NFStream flow data, maps it to CICIDS2017 feature names,
    runs XGBoost prediction, AND checks for multi-flow attack patterns
    (Port Scan, DDoS, Brute Force) using Redis-backed sliding windows.
    """
    data = await request.json()

    src_ip = data.get("src_ip", "unknown")
    dst_port = data.get("dst_port", 0)

    # --- Rule-based multi-flow checks ---
    is_port_scan, distinct_ports = track_and_check_port_scan(src_ip, dst_port)
    is_ddos, conn_count = track_and_check_ddos(src_ip)
    is_brute_force, attempt_count = track_and_check_brute_force(src_ip, dst_port)

    # --- Existing per-flow ML feature mapping ---
    mapped = {
        "Destination Port": data.get("dst_port", 0),
        "Flow Duration": data.get("bidirectional_duration_ms", 0) * 1000,
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
        "Flow Bytes/s": data.get("bidirectional_bytes", 0) / max(data.get("bidirectional_duration_ms", 1) / 1000, 0.001),
        "Flow Packets/s": data.get("bidirectional_packets", 0) / max(data.get("bidirectional_duration_ms", 1) / 1000, 0.001),
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
        "Fwd Packets/s": data.get("src2dst_packets", 0) / max(data.get("src2dst_duration_ms", 1) / 1000, 0.001),
        "Bwd Packets/s": data.get("dst2src_packets", 0) / max(data.get("dst2src_duration_ms", 1) / 1000, 0.001),
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

        # Override ML attack_type with rule-based detections (priority order matters)
        for r in result["results"]:
            if is_port_scan:
                r["attack_type"] = "Port Scanning (rule-based)"
                r["is_anomaly"] = True
                r["distinct_ports_in_window"] = distinct_ports
            elif is_ddos:
                r["attack_type"] = "DDoS (rule-based)"
                r["is_anomaly"] = True
                r["connections_in_window"] = conn_count
            elif is_brute_force:
                r["attack_type"] = "Brute Force (rule-based)"
                r["is_anomaly"] = True
                r["attempts_in_window"] = attempt_count

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