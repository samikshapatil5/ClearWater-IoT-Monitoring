import os
import requests

DL_API_URL = os.getenv("CLEARWATER_DL_API_URL", "http://127.0.0.1:8000")
TIMEOUT_SECONDS = float(os.getenv("CLEARWATER_DL_TIMEOUT", "30"))


def get_model_prediction(water_quality=None, history=None):
    """Call the actual trained CNN-LSTM + CMI FastAPI service.

    Exactly 10 chronological REAL readings are required. This function never
    fills missing history with examples or duplicates.
    """
    history = history or []
    if len(history) < 10:
        return {
            "prediction": "Unavailable",
            "available": False,
            "reason": f"Need 10 actual chronological sensor readings; only {len(history)} stored.",
            "readings_used": len(history),
            "cmi": None,
        }
    window = history[-10:]
    readings = []
    for r in window:
        readings.append({
            "pH": r.get("pH", r.get("ph")),
            "TDS_ppm": r.get("TDS", r.get("TDS_ppm", r.get("tds"))),
            "Turbidity_NTU": r.get("turbidity", r.get("Turbidity_NTU")),
            "Temperature_C": r.get("temperature", r.get("Temperature_C")),
        })
    try:
        response = requests.post(f"{DL_API_URL.rstrip('/')}/predict", json={"readings": readings}, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success") or not isinstance(payload.get("data"), dict):
            raise ValueError("DL API returned an unexpected response")
        data = payload["data"]
        cnn = data.get("cnn_lstm") or {}
        cmi = data.get("wqi") or {}
        prediction = str(cnn.get("prediction", "Unavailable")).strip().title()
        if prediction not in ("Safe", "Unsafe"):
            prediction = "Unavailable"
        return {
            "prediction": prediction,
            "available": prediction in ("Safe", "Unsafe"),
            "probability": cnn.get("probability"),
            "confidence": cnn.get("confidence"),
            "raw_cnn_lstm": cnn,
            "cmi": cmi,
            "latest_sensor_reading": data.get("latest_sensor_reading"),
            "readings_used": data.get("readings_used", len(readings)),
            "source": "trained_cnn_lstm_api",
        }
    except (requests.RequestException, ValueError, KeyError) as exc:
        return {
            "prediction": "Unavailable",
            "available": False,
            "reason": f"Could not obtain a real model result from {DL_API_URL}: {exc}",
            "readings_used": len(window),
            "cmi": None,
            "source": "trained_cnn_lstm_api",
        }
