"# CICIDS Network Attack Detection

Ce projet fournit un système de détection d'attaques réseau basé sur l'ensemble de données CICIDS2017. Il combine un modèle d'apprentissage automatique (XGBoost) avec une API FastAPI, un tableau de bord Streamlit et des détections en temps réel basées sur des règles pour identifier des comportements suspects tels que les analyses de ports, les DDoS et les attaques par force brute.

## Fonctionnalités

- Détection d'anomalies réseau à partir de features de flux réseau
- Prédictions via une API REST sécurisée
- Tableau de bord interactif pour visualiser les prédictions historiques
- Détection en temps réel à partir de données de type NFStream
- Explications SHAP sur les features les plus influentes
- Persistance des prédictions dans une base PostgreSQL
- Détection multi-flux avec Redis pour les motifs d'attaque

## Architecture

- API : FastAPI
- Tableau de bord : Streamlit
- Modèle ML : XGBoost + preprocessing + SHAP
- Base de données : PostgreSQL
- Cache / détection en temps réel : Redis
- Conteneurisation : Docker Compose

## Prérequis

- Python 3.11
- Docker et Docker Compose (optionnel, recommandé)
- Git

## Installation

### 1. Cloner le projet

```bash
git clone <url-du-repo>
cd cicids-project
```

### 2. Créer le fichier d'environnement

Créer un fichier `.env` à la racine du projet avec les variables suivantes :

```env
SECRET_KEY=change-me
APP_USERNAME=your-username
APP_PASSWORD=your-strong-password
DATABASE_URL=postgresql://postgres:your-password@db:5432/cicids_db
POSTGRES_PASSWORD=your-password
```

### 3. Installer les dépendances

Avec Python :

```bash
pip install -r requirements.txt
```

## Lancement avec Docker

```bash
docker compose up --build
```

Services disponibles :
- API : http://localhost:8000
- Documentation Swagger : http://localhost:8000/docs
- Tableau de bord : http://localhost:8501
- PostgreSQL : localhost:5432
- Redis : localhost:6379

## Lancement local

### API

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Tableau de bord

```bash
streamlit run dashboard/app.py
```

## Utilisation

### Authentification

Obtenir un jeton d'accès :

```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your-username&password=your-strong-password"
```

### Prédiction sur un lot de flux

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
        "Fwd Packet Length Std": 10,
        "Bwd Packet Length Max": 80,
        "Bwd Packet Length Min": 20,
        "Bwd Packet Length Mean": 40,
        "Bwd Packet Length Std": 5
      }
    ]
  }'
```

### Historique des prédictions

```bash
curl -X GET "http://localhost:8000/history" \
  -H "Authorization: Bearer <token>"
```

## Structure du projet

```text
api/                # API FastAPI et authentification
ashboard/           # Interface Streamlit
data/               # Jeux de données CICIDS2017
models/             # Modèles entraînés et artefacts
notebooks/          # Notebooks d'analyse et de modélisation
scripts/            # Scripts utilitaires pour le trafic
utils/              # Logique de prédiction
```

## Notes importantes

- Le modèle attendu est chargé depuis le dossier `models/` via `utils/predictor.py`.
- Les prédictions sont enregistrées dans la base PostgreSQL.
- Les routes `/predict-live` et les règles Redis permettent d'identifier certains motifs d'attaque à partir de multiples flux.

## Licence

Ce projet a été développé dans le cadre de mon stage d'été. Il est fourni à des fins d'apprentissage, de démonstration et d'utilisation interne. Tous droits réservés à l'auteur, sauf autorisation explicite écrite pour une réutilisation, redistribution ou utilisation commerciale.

## Développement

Pour travailler en local sans Docker :

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Ensuite, démarrez l'API et le tableau de bord comme décrit ci-dessus.
" 
