import os
import uvicorn
import pandas as pd

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from typing import Optional

import joblib
from src.pipeline.prediction_pipeline import PredictPipeline

pipeline = PredictPipeline()

# ─────────────────────────────
# App Setup
# ─────────────────────────────

app = FastAPI(title="IDS System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

# ─────────────────────────────
# Load Model
# ─────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "artifacts", "models", "model.pkl")

model = joblib.load(model_path)

# ─────────────────────────────
# Input Schema (ONLY 7 SHOWN)
# ─────────────────────────────

class SimpleInput(BaseModel):
    duration: float
    src_bytes: float
    dst_bytes: float
    wrong_fragment: float = 0
    urgent: float = 0
    count: float = 5
    srv_count: float = 3

# ─────────────────────────────
# Default Full Schema
# ─────────────────────────────

def get_default_features():
    return {
        "duration": 0,
        "protocol_type": "tcp",
        "service": "http",
        "flag": "SF",
        "src_bytes": 0,
        "dst_bytes": 0,
        "land": 0,
        "wrong_fragment": 0,
        "urgent": 0,
        "hot": 0,
        "num_failed_logins": 0,
        "logged_in": 1,
        "num_compromised": 0,
        "root_shell": 0,
        "su_attempted": 0,
        "num_root": 0,
        "num_file_creations": 0,
        "num_shells": 0,
        "num_access_files": 0,
        "num_outbound_cmds": 0,
        "is_host_login": 0,
        "is_guest_login": 0,
        "count": 0,
        "srv_count": 0,
        "serror_rate": 0.0,
        "srv_serror_rate": 0.0,
        "rerror_rate": 0.0,
        "srv_rerror_rate": 0.0,
        "same_srv_rate": 1.0,
        "diff_srv_rate": 0.0,
        "srv_diff_host_rate": 0.0,
        "dst_host_count": 0,
        "dst_host_srv_count": 0,
        "dst_host_same_srv_rate": 1.0,
        "dst_host_diff_srv_rate": 0.0,
        "dst_host_same_src_port_rate": 0.0,
        "dst_host_srv_diff_host_rate": 0.0,
        "dst_host_serror_rate": 0.0,
        "dst_host_srv_serror_rate": 0.0,
        "dst_host_rerror_rate": 0.0,
        "dst_host_srv_rerror_rate": 0.0,
    }

# ─────────────────────────────
# Routes
# ─────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/predict")
def predict(data: SimpleInput):
    try:
        full_data = get_default_features()

        # overwrite only provided values
        full_data.update(data.dict())

        df = pd.DataFrame([full_data])
        pred = pipeline.predict(df)

        pred = int(pred[0])

        result = "Anomaly" if pred in [-1, 1] and pred != 0 else "Normal"

        return {
            "prediction": result
        }

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)