

This project is a machine learning-based network intrusion detection system built around the CICIDS2017 dataset. It combines a trained XGBoost model, a FastAPI backend, a Streamlit dashboard, and real-time detection logic to classify network traffic and highlight suspicious behavior.

## Project Overview

The goal of this project is to demonstrate how machine learning can support cybersecurity monitoring by identifying abnormal traffic patterns such as:

- port scanning
- distributed denial-of-service (DDoS)
- brute-force attempts
- normal traffic versus suspicious activity

The solution is designed as both a technical demo and a practical internship project showing how ML models can be exposed through an API and visualized in a dashboard.

## Main Features

- Network traffic classification using a trained machine learning model
- REST API for batch prediction and prediction history
- Secure authentication for API access
- Interactive dashboard for monitoring recent detections
- SHAP-based feature explanations for the most influential features
- PostgreSQL storage for prediction history
- Redis-based real-time rule checks for multi-flow attack patterns
- Docker support for easier deployment

## Tech Stack

- Backend: FastAPI
- Frontend: Streamlit
- Machine Learning: XGBoost, scikit-learn, SHAP
- Database: PostgreSQL
- Cache / streaming logic: Redis
- Containerization: Docker Compose

## Project Structure

```text
api/            # FastAPI backend and authentication
ashboard/      # Streamlit dashboard
utils/          # Prediction logic and model inference
models/        # Trained model artifacts
notebooks/      # Analysis and experimentation notebooks
data/           # Dataset files
scripts/        # Traffic-related helper scripts
```

## Requirements

- Python 3.11
- Docker and Docker Compose (recommended)
- Git

## Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd cicids-project
```

### 2. Create environment variables

Create a `.env` file in the project root with values such as:

```env
SECRET_KEY=change-me
APP_USERNAME=your-username
APP_PASSWORD=your-strong-password
DATABASE_URL=postgresql://postgres:your-password@db:5432/cicids_db
POSTGRES_PASSWORD=your-password
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Run the Project

### Option 1: With Docker

```bash
docker compose up --build
```

Once running, the services are available at:

- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Option 2: Locally

Start the API:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Start the dashboard:

```bash
streamlit run dashboard/app.py
```

## Usage

### Authentication

Obtain an access token:

```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your-username&password=your-strong-password"
```

### Make a prediction

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {
        "Destination Port": 80,
        "Flow Duration": 1000,
        "Total Fwd Packets": 10,
        "Total Length of Fwd Packets": 2000,
        "Fwd Packet Length Max": 100,
        "Fwd Packet Length Min": 50,
        "Fwd Packet Length Mean": 75,
        "Fwd Packet Length Std": 10
      }
    ]
  }'
```

### View prediction history

```bash
curl -X GET "http://localhost:8000/history" \
  -H "Authorization: Bearer <token>"
```

## Notes

- The trained model is expected to be available in the models directory.
- Prediction history is stored in PostgreSQL.
- Real-time attack-pattern detection uses Redis and rule-based logic for certain multi-flow scenarios.

## License

This project was developed during my summer internship. It is intended for educational, demonstration, and internal-use purposes. All rights are reserved unless explicit written authorization is granted for reuse, redistribution, or commercial use.

## Development

For local development without Docker:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Then start the API and the dashboard as described above.
" 
