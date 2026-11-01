from math import isfinite
from typing import List, Optional
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from src.analysis import analyze_water_quality


# Firebase config is read from the Agentic AI project's .env file.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENTIC_DIR = PROJECT_ROOT / "TASK_3_AGENTIC_AI"
load_dotenv(AGENTIC_DIR / ".env", override=False)
_FIREBASE_APP = None

def load_firebase_readings(limit: int = 10):
    """Fetch and normalize the newest valid readings from root /sensor_readings.

    Expected existing fields: TDS, pH, temperature, turbidity, timestamp.
    Does not write to Firebase and never substitutes dummy values.
    """
    global _FIREBASE_APP
    database_url = os.getenv("FIREBASE_DATABASE_URL", "").strip()
    if not database_url:
        raise ValueError("FIREBASE_DATABASE_URL is missing in TASK_3_AGENTIC_AI/.env")
    service_account_setting = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
    if not service_account_setting:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_PATH is missing in TASK_3_AGENTIC_AI/.env")
    credential_path = Path(service_account_setting)
    if not credential_path.is_absolute():
        credential_path = (AGENTIC_DIR / credential_path).resolve()
    if not credential_path.is_file():
        raise ValueError(f"Firebase service-account file not found: {credential_path}")
    try:
        import firebase_admin
        from firebase_admin import credentials, db
    except ImportError as exc:
        raise RuntimeError("firebase-admin is missing in the Deep Learning venv. Run: python -m pip install firebase-admin") from exc
    if _FIREBASE_APP is None:
        try:
            _FIREBASE_APP = firebase_admin.get_app("clearwater_dl")
        except ValueError:
            _FIREBASE_APP = firebase_admin.initialize_app(
                credentials.Certificate(str(credential_path)),
                {"databaseURL": database_url},
                name="clearwater_dl",
            )
    sensor_path = os.getenv("FIREBASE_SENSOR_PATH", "sensor_readings").strip().strip("/") or "sensor_readings"
    records = db.reference(sensor_path, app=_FIREBASE_APP).get()
    if isinstance(records, dict):
        iterable = [(str(key), value) for key, value in records.items()]
    elif isinstance(records, list):
        iterable = [(str(i), value) for i, value in enumerate(records) if value is not None]
    else:
        iterable = []
    normalized = []
    skipped = 0
    for key, record in iterable:
        if not isinstance(record, dict):
            skipped += 1
            continue
        try:
            def pick(*names):
                for name in names:
                    if name in record and record[name] is not None:
                        return float(record[name])
                raise ValueError("missing field")
            ph = pick("pH", "ph", "PH")
            tds = pick("TDS", "TDS_ppm", "tds", "tds_ppm")
            turbidity = pick("turbidity", "Turbidity_NTU", "Turbidity", "ntu")
            temperature = pick("temperature", "Temperature_C", "Temperature", "temp")
            vals = [ph, tds, turbidity, temperature]
            if not all(isfinite(v) for v in vals) or not (0 < ph <= 14) or tds < 0 or turbidity < 0:
                raise ValueError("invalid sensor value")
            timestamp = record.get("timestamp", "")
            # ISO timestamps sort chronologically after normalizing to epoch when parseable.
            try:
                parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
                order = parsed.timestamp()
            except Exception:
                order = float(len(normalized))
            normalized.append({
                "pH": ph, "TDS_ppm": tds, "Turbidity_NTU": turbidity, "Temperature_C": temperature,
                "timestamp": timestamp, "firebase_key": key, "_order": order,
            })
        except (TypeError, ValueError, OverflowError):
            skipped += 1
    normalized.sort(key=lambda row: row["_order"])
    if len(normalized) < limit:
        raise ValueError(f"Firebase has only {len(normalized)} valid readings in /{sensor_path}; exactly 10 are required for CNN-LSTM. Skipped {skipped} invalid records. No dummy readings were used.")
    selected = normalized[-limit:]
    return selected, {"source": "firebase", "path": "/" + sensor_path, "valid_records_found": len(normalized), "readings_used": len(selected), "invalid_records_skipped": skipped, "firebase_keys": [r["firebase_key"] for r in selected]}

# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="ClearWater DL API",
    description="Deep Learning API for IoT-based water quality monitoring.",
    version="1.0.0"
)


# ============================================================
# SENSOR INPUT VALIDATION
# ============================================================

class SensorReading(BaseModel):
    pH: float = Field(
        ...,
        description="Water pH value"
    )

    TDS_ppm: float = Field(
        ...,
        description="Total Dissolved Solids in ppm"
    )

    Turbidity_NTU: float = Field(
        ...,
        description="Turbidity in NTU"
    )

    Temperature_C: float = Field(
        ...,
        description="Water temperature in Celsius"
    )

    # Reject NaN and infinite values
    @field_validator(
        "pH",
        "TDS_ppm",
        "Turbidity_NTU",
        "Temperature_C"
    )
    @classmethod
    def validate_finite_values(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError(
                "Sensor readings must be finite numbers."
            )
        return value

    # pH validation
    @field_validator("pH")
    @classmethod
    def validate_ph(cls, value: float) -> float:
        if not 0 < value <= 14:
            raise ValueError(
                "pH must be greater than 0 and at most 14."
            )
        return value

    # TDS validation
    @field_validator("TDS_ppm")
    @classmethod
    def validate_tds(cls, value: float) -> float:
        if value < 0:
            raise ValueError(
                "TDS cannot be negative."
            )
        return value

    # Turbidity validation
    @field_validator("Turbidity_NTU")
    @classmethod
    def validate_turbidity(cls, value: float) -> float:
        if value < 0:
            raise ValueError(
                "Turbidity cannot be negative."
            )
        return value


# ============================================================
# PREDICTION REQUEST MODEL
# ============================================================

class PredictionRequest(BaseModel):
    readings: List[SensorReading] = Field(
        ...,
        min_length=10,
        max_length=10,
        description="Exactly 10 sequential sensor readings"
    )


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    return {
        "system": "ClearWater DL API",
        "status": "running",
        "version": "1.0.0"
    }


# ============================================================
# HEALTH CHECK ENDPOINT
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "ClearWater Deep Learning API"
    }


# ============================================================
# WATER QUALITY PREDICTION ENDPOINT
# ============================================================

@app.post("/predict")
def predict(request: Optional[PredictionRequest] = None):

    try:
        # If no request body is supplied, fetch the real existing Firebase readings.
        if request is None:
            firebase_readings, source_info = load_firebase_readings(limit=10)
            sensor_data = [[r["pH"], r["TDS_ppm"], r["Turbidity_NTU"], r["Temperature_C"]] for r in firebase_readings]
        else:
            source_info = {"source": "request_body", "readings_used": len(request.readings)}
            sensor_data = [
                [reading.pH, reading.TDS_ppm, reading.Turbidity_NTU, reading.Temperature_C]
                for reading in request.readings
            ]

        # Run CNN-LSTM prediction and current WQI analysis
        result = analyze_water_quality(sensor_data)

        return {
            "success": True,
            "source": source_info,
            "data": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        # Avoid exposing internal error details to API clients.
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Check the API server logs."
        )




@app.get("/predict-from-firebase")
def predict_from_firebase():
    """Fetch existing Firebase sensor_readings and run the CNN-LSTM model."""
    try:
        firebase_readings, source_info = load_firebase_readings(limit=10)
        sensor_data = [[r["pH"], r["TDS_ppm"], r["Turbidity_NTU"], r["Temperature_C"]] for r in firebase_readings]
        result = analyze_water_quality(sensor_data)
        return {"success": True, "source": source_info, "data": result}
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Firebase prediction failed: {type(error).__name__}: {error}") from error


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":
    print("\nClearWater DL API module loaded successfully.")