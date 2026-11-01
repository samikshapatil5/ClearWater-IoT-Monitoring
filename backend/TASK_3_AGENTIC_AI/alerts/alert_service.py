
"""Parameter-specific water-quality alerts for ClearWater."""

import json
import math
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ALERT_FILE = BASE_DIR / "data" / "alerts_data.json"
_LOCK = threading.Lock()

# Project monitoring thresholds; verify against the applicable standard.
PH_MIN = 6.5
PH_MAX = 8.5

TDS_WARNING = 500.0
TDS_HIGH = 2000.0

TURBIDITY_OBJECTIVE = 1.0
TURBIDITY_HIGH = 5.0


def _read_alerts():
    """Read previously saved alert records."""
    if not ALERT_FILE.exists():
        return []

    try:
        with ALERT_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, list) else []

    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(
            "alerts_data.json cannot be read. Check the file "
            "and restore a backup if needed."
        ) from exc


def _write_alerts(alerts):
    """Save alerts atomically to the local JSON history."""
    ALERT_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = ALERT_FILE.with_suffix(".json.tmp")

    with temp_file.open("w", encoding="utf-8") as file:
        json.dump(alerts, file, indent=2, ensure_ascii=False)
        file.flush()
        os.fsync(file.fileno())

    os.replace(temp_file, ALERT_FILE)


def _get_numeric_value(analysis, water, parameter):
    """Read a finite numeric parameter without inventing a value."""
    details = analysis.get(parameter) or {}

    value = details.get("value")
    if value is None:
        value = water.get(parameter)

    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None

    return number if math.isfinite(number) else None


def _add_parameter_alerts(water, analysis, raw):
    """Add alerts based on individual measured parameters."""

    # -------------------------------------------------
    # pH
    # -------------------------------------------------
    ph = _get_numeric_value(analysis, water, "pH")

    if ph is None:
        raw.append((
            "warning",
            "PH_UNAVAILABLE",
            "A usable pH reading is unavailable. Check the pH sensor."
        ))
    elif not 0 <= ph <= 14:
        raw.append((
            "warning",
            "PH_INVALID",
            f"pH reading {ph:g} is outside the valid 0-14 scale. Check the sensor."
        ))
    elif ph < PH_MIN:
        raw.append((
            "critical",
            "PH_LOW",
            f"pH is {ph:g}, below the project reference minimum of {PH_MIN}."
        ))
    elif ph > PH_MAX:
        raw.append((
            "critical",
            "PH_HIGH",
            f"pH is {ph:g}, above the project reference maximum of {PH_MAX}."
        ))
    else:
        raw.append((
            "info",
            "PH_NORMAL",
            f"pH is {ph:g}, within the project reference range "
            f"of {PH_MIN}-{PH_MAX}."
        ))

    # -------------------------------------------------
    # TDS (ppm)
    # -------------------------------------------------
    tds = _get_numeric_value(analysis, water, "TDS")

    if tds is None:
        raw.append((
            "warning",
            "TDS_UNAVAILABLE",
            "A usable TDS reading is unavailable. Check the TDS sensor."
        ))
    elif tds < 0:
        raw.append((
            "warning",
            "TDS_INVALID",
            f"TDS reading {tds:g} ppm is invalid. Check the sensor."
        ))
    elif tds <= TDS_WARNING:
        raw.append((
            "info",
            "TDS_NORMAL",
            f"TDS is {tds:g} ppm, at or below the project reference "
            f"limit of {TDS_WARNING:g} ppm."
        ))
    elif tds <= TDS_HIGH:
        raw.append((
            "warning",
            "TDS_HIGH",
            f"TDS is {tds:g} ppm, above {TDS_WARNING:g} ppm. "
            "Verify the measurement and investigate."
        ))
    else:
        raw.append((
            "critical",
            "TDS_VERY_HIGH",
            f"TDS is {tds:g} ppm, above the project reference "
            f"limit of {TDS_HIGH:g} ppm."
        ))

    # -------------------------------------------------
    # Turbidity
    # Only calibrated NTU can be compared with NTU limits.
    # Raw ADC/voltage must not be treated as NTU.
    # -------------------------------------------------
    turbidity = _get_numeric_value(analysis, water, "turbidity")

    if turbidity is None:
        raw.append((
            "warning",
            "TURBIDITY_NTU_UNAVAILABLE",
            "Calibrated turbidity in NTU is unavailable. "
            "Raw ADC/voltage cannot be compared with NTU limits."
        ))
    elif turbidity < 0:
        raw.append((
            "warning",
            "TURBIDITY_INVALID",
            f"Turbidity reading {turbidity:g} NTU is invalid."
        ))
    elif turbidity <= TURBIDITY_OBJECTIVE:
        raw.append((
            "info",
            "TURBIDITY_NORMAL",
            f"Turbidity is {turbidity:g} NTU, at or below the "
            f"project objective of {TURBIDITY_OBJECTIVE:g} NTU."
        ))
    elif turbidity <= TURBIDITY_HIGH:
        raw.append((
            "warning",
            "TURBIDITY_HIGH",
            f"Turbidity is {turbidity:g} NTU, above the "
            f"{TURBIDITY_OBJECTIVE:g} NTU objective. Verify the sensor "
            "and investigate."
        ))
    else:
        raw.append((
            "critical",
            "TURBIDITY_VERY_HIGH",
            f"Turbidity is {turbidity:g} NTU, above the project "
            f"reference limit of {TURBIDITY_HIGH:g} NTU."
        ))


def generate_alerts(agent_result):
    """
    Generate parameter-specific alerts from an agent result.

    This function does not generate OVERALL_WARNING,
    OVERALL_UNSAFE, or CMI_WQI_REVIEW alerts.
    """
    water = agent_result.get("water_quality") or {}
    analysis = agent_result.get("analysis") or {}
    raw = []

    if not water.get("available", False):
        raw.append((
            "warning",
            "READINGS_UNAVAILABLE",
            "Current sensor readings are unavailable. "
            "Check the sensor connection and data pipeline."
        ))
    else:
        _add_parameter_alerts(water, analysis, raw)

    now = datetime.now(timezone.utc).isoformat()
    result = []

    for index, (severity, code, message) in enumerate(raw, 1):
        alert_time = datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )

        result.append({
            "alert_id": f"cw-{alert_time}-{index}",
            "timestamp": now,
            "severity": severity,
            "code": code,
            "message": message,
            "acknowledged": False,
            "source": agent_result.get(
                "data_source", "current_agent_result"
            ),
            "test_data": bool(agent_result.get("test_data", False)),
        })

    # Save only new active alert codes/messages.
    with _LOCK:
        existing = _read_alerts()

        active_keys = {
            (alert.get("code"), alert.get("message"))
            for alert in existing
            if not alert.get("acknowledged", False)
        }

        new_alerts = [
            alert for alert in result
            if (alert["code"], alert["message"]) not in active_keys
        ]

        existing.extend(new_alerts)
        _write_alerts(existing[-2000:])

    return result


def get_all_alerts():
    """Return saved alert history."""
    with _LOCK:
        return _read_alerts()


def acknowledge_alert(alert_id):
    """Mark an existing alert as acknowledged."""
    with _LOCK:
        alerts = _read_alerts()

        for alert in alerts:
            if alert.get("alert_id") == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_at"] = (
                    datetime.now(timezone.utc).isoformat()
                )
                _write_alerts(alerts)
                return alert

    return None
