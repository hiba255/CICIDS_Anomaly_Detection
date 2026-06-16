from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import sys
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.predictor import predict
from api.auth import create_access_token, get_current_user, verify_password, USERS_DB

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
    return result