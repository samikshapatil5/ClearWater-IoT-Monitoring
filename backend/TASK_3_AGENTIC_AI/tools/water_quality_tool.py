from tools.history_tool import get_latest_reading


def get_current_water_quality():
    """Return the latest valid stored sensor reading, never a hard-coded sample."""
    latest = get_latest_reading()
    if latest is None:
        return {"available": False, "message": "No valid sensor readings found in the configured data source."}
    return {
        "pH": latest["pH"],
        "TDS": latest["TDS"],
        "turbidity": latest["turbidity"],
        "temperature": latest["temperature"],
        "timestamp": latest.get("timestamp"),
        "available": True,
        "source": "configured_sensor_history",
    }
