from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import joblib

app = FastAPI(title="Network IDS API")

# Load model once at startup
model = joblib.load("artifacts/models/model.pkl")

# ---- Input Schema ----
class NetworkData(BaseModel):
    duration: float
    src_bytes: float
    dst_bytes: float
    wrong_fragment: float
    urgent: float
    count: float
    srv_count: float

# ---- Health Check ----
@app.get("/")
def home():
    return {"message": "IDS API is running 🚀"}

# ---- Prediction Endpoint ----
@app.post("/predict")
def predict(data: NetworkData):
    try:
        # Convert input → array
        features = np.array([[
            data.duration,
            data.src_bytes,
            data.dst_bytes,
            data.wrong_fragment,
            data.urgent,
            data.count,
            data.srv_count
        ]])

        # Predict
        pred = model.predict(features)[0]

        # Isolation Forest → (-1, 1)
        result = "Anomaly" if pred == -1 else "Normal"

        return {
            "prediction": result,
            "raw_output": int(pred)
        }

    except Exception as e:
        return {"error": str(e)}