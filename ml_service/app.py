from pathlib import Path
import os
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE / "models" / "cnn_lstm.keras"
SCALER_PATH = BASE / "models" / "scaler.joblib"

app = FastAPI(title="ClearWater CNN-LSTM Service", version="1.0.0")

class Reading(BaseModel):
    ph: float
    turbidity: float
    tds: float
    temperature: float

model = None
scaler = None


def load_artifacts():
    global model, scaler
    if MODEL_PATH.exists() and SCALER_PATH.exists():
        try:
            import tensorflow as tf
            import joblib
            model = tf.keras.models.load_model(MODEL_PATH)
            scaler = joblib.load(SCALER_PATH)
        except Exception as exc:
            print(f"Model load failed: {exc}")

load_artifacts()

@app.get("/health")
def health():
    return {"ok": True, "model_loaded": model is not None, "model_path": str(MODEL_PATH)}

@app.post("/predict")
def predict(reading: Reading):
    values = np.array([[reading.ph, reading.turbidity, reading.tds, reading.temperature]], dtype=np.float32)

    # Real CNN-LSTM prediction is used only when a trained model exists.
    if model is not None and scaler is not None:
        scaled = scaler.transform(values).astype(np.float32)
        # A single reading is wrapped as a 1-step sequence. The training script
        # uses sliding windows; this endpoint remains compatible for live inference.
        x = scaled.reshape(1, 1, 4)
        probability = float(model.predict(x, verbose=0).reshape(-1)[0])
        label = "Contaminated" if probability >= 0.5 else "Safe"
        confidence = probability if label == "Contaminated" else 1.0 - probability
        return {"prediction": label, "confidence": round(confidence * 100, 2), "source": "trained CNN-LSTM"}

    # Explicit fallback for development/demo when the trained model is not installed.
    checks = [
        6.5 <= reading.ph <= 8.5,
        reading.turbidity <= 5,
        reading.tds <= 500,
        0 <= reading.temperature <= 40,
    ]
    safe_ratio = sum(checks) / len(checks)
    label = "Safe" if all(checks) else "Contaminated"
    confidence = 90.0 if label == "Safe" else round(60 + (1 - safe_ratio) * 30, 2)
    return {"prediction": label, "confidence": confidence, "source": "demo threshold fallback"}
