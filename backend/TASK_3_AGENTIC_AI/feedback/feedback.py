"""Local JSON feedback storage for ClearWater (single-host/demo deployment)."""
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FEEDBACK_FILE = BASE_DIR / "feedback_data.json"
_LOCK = threading.Lock()


def _read_store():
    if not FEEDBACK_FILE.exists():
        return {"feedback": []}
    try:
        with FEEDBACK_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not isinstance(data.get("feedback"), list):
            raise ValueError("Feedback JSON must contain a 'feedback' list.")
        return data
    except json.JSONDecodeError as exc:
        raise RuntimeError("feedback_data.json is invalid JSON; restore a backup before continuing.") from exc


def _write_store(data):
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = FEEDBACK_FILE.with_suffix(".json.tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, FEEDBACK_FILE)


def save_feedback(feedback_type, user_feedback, prediction=None, recommendation=None, water_quality=None):
    """Append one feedback record and return the stored record."""
    if not isinstance(feedback_type, str) or not feedback_type.strip():
        raise ValueError("feedback_type is required")
    if not isinstance(user_feedback, str) or not user_feedback.strip():
        raise ValueError("user_feedback is required")
    record = {
        "feedback_id": f"fb-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "feedback_type": feedback_type.strip()[:60],
        "user_feedback": user_feedback.strip()[:2000],
        "prediction": prediction,
        "recommendation": recommendation,
        "water_quality": water_quality,
    }
    with _LOCK:
        data = _read_store()
        data["feedback"].append(record)
        _write_store(data)
    return record


def submit_feedback(feedback_type, user_feedback, prediction=None, recommendation=None, water_quality=None):
    return save_feedback(feedback_type, user_feedback, prediction, recommendation, water_quality)


def get_all_feedback():
    with _LOCK:
        return _read_store().get("feedback", [])
