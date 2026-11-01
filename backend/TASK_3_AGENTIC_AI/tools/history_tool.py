
"""Read actual ESP32 sensor history from Firebase Realtime Database.

Expected layout:
  sensor_readings/<Firebase-push-id>

Firebase is authoritative when configured. No dummy readings are created.
"""

import json
import os
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_FILE = os.path.join(DATA_DIR, "sensor_history.json")
MAX_HISTORY = 5000

load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)
_FIREBASE_APP = None


def get_storage_backend():
    return (
        "firebase"
        if os.getenv("FIREBASE_DATABASE_URL", "").strip()
        else "local_json"
    )


def _firebase_refs():
    """Return Firebase history and optional latest references."""
    global _FIREBASE_APP

    database_url = os.getenv("FIREBASE_DATABASE_URL", "").strip()
    if not database_url:
        return None

    service_account_setting = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH", ""
    ).strip()

    if not service_account_setting:
        raise RuntimeError(
            "FIREBASE_SERVICE_ACCOUNT_PATH is missing in .env"
        )

    try:
        import firebase_admin
        from firebase_admin import credentials, db
    except ImportError as exc:
        raise RuntimeError(
            "firebase-admin is not installed. Run pip install -r requirements.txt"
        ) from exc

    service_account_path = Path(service_account_setting)
    if not service_account_path.is_absolute():
        service_account_path = Path(BASE_DIR) / service_account_path

    if not service_account_path.is_file():
        raise RuntimeError(
            f"Firebase service-account file not found: {service_account_path}"
        )

    if _FIREBASE_APP is None:
        try:
            _FIREBASE_APP = firebase_admin.get_app("clearwater")
        except ValueError:
            _FIREBASE_APP = firebase_admin.initialize_app(
                credentials.Certificate(str(service_account_path)),
                {"databaseURL": database_url},
                name="clearwater",
            )

    readings_path = (
        os.getenv("FIREBASE_SENSOR_PATH", "sensor_readings")
        .strip()
        .strip("/")
        or "sensor_readings"
    )

    latest_path = (
        os.getenv("FIREBASE_LATEST_PATH", "").strip().strip("/")
    )

    history_ref = db.reference(readings_path, app=_FIREBASE_APP)
    latest_ref = (
        db.reference(latest_path, app=_FIREBASE_APP)
        if latest_path
        else None
    )

    return history_ref, latest_ref


def _normalize(reading):
    """Validate and normalize one actual sensor reading."""
    if not isinstance(reading, dict):
        raise TypeError("Sensor reading must be a dictionary.")

    aliases = {
        "pH": ("pH", "ph", "PH"),
        "TDS": ("TDS", "TDS_ppm", "tds", "tds_ppm"),
        "turbidity": (
            "turbidity", "Turbidity_NTU", "Turbidity", "ntu"
        ),
        "temperature": (
            "temperature", "Temperature_C", "Temperature", "temp"
        ),
    }

    result = {}

    for target, names in aliases.items():
        value = next(
            (
                reading[name]
                for name in names
                if name in reading and reading[name] is not None
            ),
            None,
        )

        if value is None:
            raise ValueError(f"Missing sensor field: {target}")

        try:
            value = float(value)
        except (TypeError, ValueError, OverflowError):
            raise ValueError(f"{target} must be numeric.") from None

        if not isfinite(value):
            raise ValueError(f"{target} must be finite.")

        result[target] = value

    if not 0 < result["pH"] <= 14:
        raise ValueError("pH must be > 0 and <= 14.")

    if result["TDS"] < 0 or result["turbidity"] < 0:
        raise ValueError("TDS and turbidity cannot be negative.")

    timestamp = (
        reading.get("timestamp")
        or reading.get("iso_time")
        or reading.get("time")
    )

    # Keep missing timestamps identifiable. Do not pretend that an
    # untimestamped historical record was measured at the current time.
    result["timestamp"] = (
        str(timestamp).strip() if timestamp else "time_not_synced"
    )

    if result["timestamp"].lower() in (
        "time_not_synced",
        "not_synced",
        "unknown",
        "none",
    ):
        result["timestamp"] = "time_not_synced"

    return result


def _record_time(record):
    return str(
        record.get(
            "timestamp",
            record.get("iso_time", record.get("time", "")),
        )
    )


def _timestamp_sort_key(record):
    """Return a UTC timestamp, or None if it cannot be parsed."""
    raw = _record_time(record)

    if not raw or raw.lower() in (
        "time_not_synced",
        "not_synced",
        "unknown",
        "none",
    ):
        return None

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc).timestamp()
    except (ValueError, TypeError, OverflowError):
        return None


def _get_local_history():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _safe_normalize(record):
    try:
        return _normalize(record)
    except (TypeError, ValueError):
        return {}


def get_water_quality_history():
    """Return normalized history, with valid timestamps in chronological order."""
    refs = _firebase_refs()

    if refs is None:
        raw_records = _get_local_history()
    else:
        history_ref, latest_ref = refs
        records = history_ref.get()
        raw_records = []

        if isinstance(records, dict):
            for key, record in records.items():
                if isinstance(record, dict):
                    item = dict(record)
                    item.setdefault("firebase_key", key)
                    raw_records.append(item)

        elif isinstance(records, list):
            raw_records = [
                record for record in records
                if isinstance(record, dict)
            ]

        if latest_ref is not None:
            latest = latest_ref.get()

            if isinstance(latest, dict):
                try:
                    normalized_latest = _normalize(latest)
                    latest_stamp = _record_time(normalized_latest)

                    if not any(
                        _record_time(_safe_normalize(record))
                        == latest_stamp
                        for record in raw_records
                    ):
                        raw_records.append(latest)

                except (TypeError, ValueError):
                    pass

    normalized = []

    for record in raw_records:
        try:
            normalized.append(_normalize(record))
        except (TypeError, ValueError):
            continue

    if normalized:
        # Keep valid timestamps chronological. Untimestamped records go first,
        # so they cannot displace the newest timestamped record.
        normalized.sort(
            key=lambda record: (
                _timestamp_sort_key(record) is not None,
                _timestamp_sort_key(record)
                if _timestamp_sort_key(record) is not None
                else 0,
            )
        )

    return normalized[-MAX_HISTORY:]


def get_latest_reading():
    """Return the newest timestamped reading when available."""
    history = get_water_quality_history()

    if not history:
        return None

    timestamped = [
        reading
        for reading in history
        if _timestamp_sort_key(reading) is not None
    ]

    if timestamped:
        return timestamped[-1]

    # Do not claim that an unsynchronized reading is the newest.
    return None


def add_water_quality_reading(reading):
    """Store a validated sensor reading in Firebase or local JSON."""
    normalized = _normalize(reading)
    refs = _firebase_refs()

    if refs is not None:
        history_ref, _ = refs
        history_ref.push(normalized)
        return normalized, len(get_water_quality_history())

    history = (_get_local_history() + [normalized])[-MAX_HISTORY:]
    os.makedirs(DATA_DIR, exist_ok=True)

    temp_file = HISTORY_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=2)

    os.replace(temp_file, HISTORY_FILE)

    return normalized, len(history)
