"""ClearWater Agentic AI Flask API.

This module exposes the existing dashboard, sensor-history, chatbot, feedback,
and alert endpoints. Live assessment data is obtained through run_agent(), which
uses the project's configured sensor/Firebase integration. Responses containing
current data are marked no-store so browsers and proxies do not reuse stale data.
"""

import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, request
from flask_cors import CORS

from agent.agent import run_agent
from chatbot.chatbot import generate_response, give_feedback
from tools.history_tool import (
    add_water_quality_reading,
    get_water_quality_history,
    get_storage_backend,
)
from alerts.alert_service import (
    generate_alerts,
    get_all_alerts,
    acknowledge_alert,
)
from feedback.feedback import get_all_feedback


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


def timed(label):
    """Log endpoint duration without changing its return value."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            started = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                logger.info(
                    "[TIMING] %s completed in %.3f seconds",
                    label,
                    time.perf_counter() - started,
                )
        return wrapper
    return decorator


@app.after_request
def prevent_stale_live_responses(response):
    """Avoid browser/proxy caching of live readings and chatbot answers."""
    if request.path in {
        "/api/water-quality",
        "/api/dashboard",
        "/api/agentic/ask",
        "/api/chat",
        "/api/alerts",
        "/api/readings",
        "/api/readings/history",
    }:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _first_present(*values):
    for value in values:
        if value is not None:
            return value
    return None


def _sensor_value(water, latest, *keys):
    """Return the first non-null sensor value across accepted field aliases."""
    for source in (water, latest):
        for key in keys:
            value = source.get(key)
            if value is not None:
                return value
    return None


def _normalise_history_row(row):
    row = _as_dict(row)
    stamp = row.get("timestamp") or row.get("time") or row.get("iso_time") or ""
    time_label = str(row.get("time") or "")
    try:
        parsed = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        if parsed.tzinfo:
            time_label = parsed.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%H:%M")
        elif not time_label:
            time_label = parsed.strftime("%H:%M")
    except (TypeError, ValueError, OverflowError):
        pass

    return {
        "time": time_label,
        "timestamp": stamp,
        "ph": _first_present(row.get("pH"), row.get("ph")),
        "tds": _first_present(row.get("TDS"), row.get("TDS_ppm"), row.get("tds")),
        "turbidity": _first_present(row.get("turbidity"), row.get("Turbidity_NTU")),
        "temperature": _first_present(row.get("temperature"), row.get("Temperature_C")),
    }


def _dashboard_payload(result):
    """Map the agent output into the field names expected by the existing React UI."""
    result = _as_dict(result)
    water = _as_dict(result.get("water_quality"))
    model = _as_dict(result.get("model_prediction"))
    decision = _as_dict(result.get("decision"))
    cmi_value = result.get("cmi") or model.get("cmi") or {}
    cmi = _as_dict(cmi_value)
    latest = _as_dict(model.get("latest_sensor_reading"))

    score = _first_present(
    cmi.get("wqi"),
    cmi.get("score"),
    cmi.get("value"),
    )
    if score is None and not isinstance(cmi_value, dict):
         score = cmi_value
    
    category = cmi.get("category", "Unavailable")
    ph = _sensor_value(water, latest, "pH", "ph")
    tds = _sensor_value(water, latest, "TDS", "TDS_ppm", "tds")
    turbidity = _sensor_value(water, latest, "turbidity", "Turbidity_NTU")
    temperature = _sensor_value(water, latest, "temperature", "Temperature_C")

    try:
        history = get_water_quality_history() or []
    except Exception:
        logger.exception("Could not load sensor history for dashboard")
        history = []

    normalised_history = [_normalise_history_row(row) for row in history if isinstance(row, dict)]
    confidence = _first_present(
        model.get("confidence"),
        _as_dict(model.get("raw_cnn_lstm")).get("confidence"),
    )
    overall = decision.get("overall_status", decision.get("status", "Unavailable"))

    return {
        "ph": ph,
        "tds": tds,
        "turbidity": turbidity,
        "temperature": temperature,
        "condition": str(overall).title(),
        "modelPrediction": model.get(
            "prediction", decision.get("model_prediction", "Unavailable")
        ),
        "confidence": confidence if confidence is not None else 0,
        "qualityScore": score if score is not None else 0,
        "wqi": {
            "value": score if score is not None else 0,
            "band": category,
            "method": cmi.get("method"),
        },
        "timestamp": water.get("timestamp") or latest.get("timestamp"),
        "data_source": result.get("data_source", water.get("source", "unknown")),
        "test_data": result.get("test_data", False),
        "history_count": len(normalised_history),
        "history": normalised_history,
        "analysis": result.get("analysis") or {},
        "decision": decision,
        "model_prediction": model,
        "recommendation": result.get("recommendation") or [],
        "sensor_available": bool(
            water.get(
                "available",
                ph is not None
                and tds is not None
                and turbidity is not None
                and temperature is not None,
            )
        ),
    }


def _agentic_payload(result):
    """Adapt generate_response output to the existing React Agentic AI contract."""
    result = _as_dict(result)
    agent_result = _as_dict(result.get("agent_result"))
    decision = _as_dict(agent_result.get("decision"))
    model = _as_dict(agent_result.get("model_prediction"))
    water = _as_dict(agent_result.get("water_quality"))
    cmi_value = agent_result.get("cmi") or model.get("cmi") or {}
    cmi = _as_dict(cmi_value)

    score = cmi.get("wqi", cmi.get("score"))
    if score is None and not isinstance(cmi_value, dict):
        score = cmi_value
    category = cmi.get("category", "Unavailable")

    ph = _first_present(water.get("pH"), water.get("ph"))
    tds = _first_present(water.get("TDS"), water.get("TDS_ppm"), water.get("tds"))
    turbidity = _first_present(water.get("turbidity"), water.get("Turbidity_NTU"))
    temperature = _first_present(water.get("temperature"), water.get("Temperature_C"))

    recommendations = agent_result.get("recommendation") or []
    if isinstance(recommendations, (list, tuple)):
        recommendation_text = " ".join(str(item) for item in recommendations)
    else:
        recommendation_text = str(recommendations)

    return {
        "intent": "water_quality",
        "risk": str(decision.get("overall_status", decision.get("status", "unknown"))).lower(),
        "answer": str(
            result.get("response")
            or "No response was returned by the Agentic AI service."
        ),
        "recommendation": recommendation_text,
        "evidence": [
            f"Current decision: {decision.get('overall_status', decision.get('status', 'Unavailable'))}",
            f"CNN-LSTM prediction: {model.get('prediction', 'Unavailable')} "
            f"(confidence {model.get('confidence', 'Unavailable')}%)",
            f"CMI/WQI: {score if score is not None else 'Unavailable'} / 100 ({category})",
            f"pH: {ph if ph is not None else 'Unavailable'}",
            f"TDS: {tds if tds is not None else 'Unavailable'} mg/L",
            f"Turbidity: {turbidity if turbidity is not None else 'Unavailable'} NTU",
            f"Temperature: {temperature if temperature is not None else 'Unavailable'} °C",
        ],
        "source": result.get("response_source", "agentic_ai"),
        "data_source": agent_result.get("data_source", water.get("source", "unknown")),
        "test_data": agent_result.get("test_data", False),
        "stages": [
            ["1", "Monitoring agent", "Loaded the latest configured sensor readings"],
            ["2", "Model agent", "Retrieved the CNN-LSTM result when 10 readings are available"],
            ["3", "Decision agent", "Applied project parameter checks and CMI/WQI policy"],
            ["4", "Explanation agent", "Generated a user-facing explanation"],
        ],
        "model": {
            "prediction": model.get("prediction", "Unavailable"),
            "confidence": model.get("confidence"),
            "source": model.get("source", "configured model service"),
        },
    }


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "success",
        "message": "Agentic AI Flask API is running",
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Agentic AI API",
        "storage_backend": get_storage_backend(),
    })


@app.route("/api/readings", methods=["GET"])
@timed("readings history")
def readings_history():
    history = get_water_quality_history() or []
    return jsonify({
        "status": "success",
        "count": len(history),
        "readings": history[-10:],
    })


@app.route("/api/readings", methods=["POST"])
def add_reading():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "JSON sensor reading is required",
        }), 400

    try:
        reading, count = add_water_quality_reading(data)
        return jsonify({
            "status": "success",
            "message": "Sensor reading stored",
            "count": count,
            "reading": reading,
            "model_ready": count >= 10,
        }), 201
    except (ValueError, TypeError) as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception:
        logger.exception("Failed to store sensor reading")
        return jsonify({
            "status": "error",
            "message": "Could not store sensor reading.",
        }), 500


@app.route("/api/water-quality", methods=["GET"])
@timed("water-quality assessment")
def water_quality():
    try:
        result = run_agent()
        return jsonify({"status": "success", "data": result})
    except Exception:
        logger.exception("Live water-quality assessment failed")
        return jsonify({
            "status": "error",
            "message": "Could not retrieve the current water-quality assessment. Check Firebase configuration and the Deep Learning API.",
        }), 503


@app.route("/api/dashboard", methods=["GET"])
@timed("dashboard")
def dashboard():
    try:
        # Deliberately fetch a fresh assessment for live Firebase-backed values.
        result = run_agent()
        return jsonify(_dashboard_payload(result))
    except Exception:
        logger.exception("Dashboard assessment failed")
        return jsonify({
            "status": "error",
            "message": "Could not load the current water-quality dashboard. Check Firebase configuration and the Deep Learning API.",
        }), 503


@app.route("/api/readings/history", methods=["GET"])
@timed("10-day history")
def readings_ten_day_history():
    """Return the last ten local calendar days, grouped by date, without synthetic rows."""
    try:
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        dates = [
            now.date() - timedelta(days=offset)
            for offset in range(9, -1, -1)
        ]
        grouped = {day.isoformat(): [] for day in dates}

        for row in (get_water_quality_history() or []):
            if not isinstance(row, dict):
                continue
            stamp = row.get("timestamp") or row.get("time") or row.get("iso_time")
            if not stamp:
                continue
            try:
                parsed = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
                local_dt = (
                    parsed.astimezone(ZoneInfo("Asia/Kolkata"))
                    if parsed.tzinfo
                    else parsed.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
                )
            except (TypeError, ValueError, OverflowError):
                continue

            date_key = local_dt.date().isoformat()
            if date_key not in grouped:
                continue
            normalised = _normalise_history_row(row)
            normalised["time"] = local_dt.strftime("%H:%M")
            normalised["timestamp"] = local_dt.isoformat()
            grouped[date_key].append(normalised)

        output = [
            {
                "day": index + 1,
                "date": date_key,
                "readings": sorted(rows, key=lambda item: item["timestamp"]),
            }
            for index, (date_key, rows) in enumerate(grouped.items())
        ]
        return jsonify(output)
    except Exception:
        logger.exception("Could not load the 10-day sensor history")
        return jsonify({
            "status": "error",
            "message": "Could not load the 10-day sensor history.",
        }), 503


@app.route("/api/chat", methods=["POST"])
@timed("chat")
def chat():
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()
    if not question:
        return jsonify({
            "status": "error",
            "message": "Question is required",
        }), 400

    try:
        # generate_response owns the single agent/LLM workflow; do not call run_agent
        # separately here, which would duplicate live reads/model work.
        result = generate_response(question)
        return jsonify({"status": "success", "data": result})
    except Exception:
        logger.exception("Chat request failed")
        return jsonify({
            "status": "error",
            "message": "The chatbot could not answer right now. Check the Agentic AI and Gemini configuration, then retry.",
        }), 503


@app.route("/api/agentic/ask", methods=["POST"])
@timed("frontend agentic ask")
def frontend_agentic_ask():
    """Adapter route matching the React Agentic AI tab's existing API contract."""
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()
    if not question:
        return jsonify({"error": "Question is required"}), 400

    try:
        # One call only: avoids duplicate agent and Firebase/model work in this route.
        result = generate_response(question)
        return jsonify(_agentic_payload(result))
    except Exception:
        logger.exception("Agentic AI request failed")
        return jsonify({
            "error": "Agentic AI request failed",
            "detail": "Unable to retrieve current sensor context or generate an answer. Check Firebase, the DL API, and Gemini configuration.",
        }), 503


@app.route("/api/feedback", methods=["POST"])
@timed("submit feedback")
def feedback():
    """Accept both the existing React form and the structured feedback contract."""
    data = request.get_json(silent=True) or {}
    feedback_type = data.get("feedback_type") or data.get("category") or "General"
    user_feedback = data.get("user_feedback")
    agent_result = data.get("agent_result")

    if not user_feedback:
        parts = []
        rating = data.get("rating")
        message = str(data.get("message") or "").strip()
        if rating not in (None, "", 0):
            parts.append(f"Rating: {rating}/5")
        if message:
            parts.append(message)
        user_feedback = " | ".join(parts)

    if not str(user_feedback or "").strip():
        return jsonify({
            "status": "error",
            "message": "Provide a rating or feedback note.",
        }), 400

    try:
        # Preserve the original behavior for feedback submitted without agent context.
        # The extra assessment occurs only on the feedback endpoint, not on every chat request.
        if not isinstance(agent_result, dict):
            agent_result = run_agent()
        result = give_feedback(
            feedback_type=feedback_type,
            user_feedback=user_feedback,
            agent_result=agent_result,
        )
        if data.get("rating") is not None and isinstance(result, dict):
            result["rating"] = data.get("rating")
        return jsonify({
            "status": "success",
            "message": "Feedback stored successfully",
            "data": result,
        }), 201
    except Exception:
        logger.exception("Feedback submission failed")
        return jsonify({
            "status": "error",
            "message": "Could not save feedback.",
        }), 500


@app.route("/api/feedback", methods=["GET"])
def list_feedback():
    try:
        records = get_all_feedback()
        return jsonify({
            "status": "success",
            "count": len(records),
            "feedback": records,
        })
    except Exception:
        logger.exception("Could not read feedback records")
        return jsonify({
            "status": "error",
            "message": "Could not read feedback records.",
        }), 500


@app.route("/api/alerts", methods=["GET"])
@timed("alerts")
def alerts():
    """Evaluate current readings, generate alerts, and return alert history."""
    try:
        result = run_agent()
        generated = generate_alerts(result)
        history = get_all_alerts()
        return jsonify({
            "status": "success",
            "new_alert_count": len(generated),
            "count": len(history),
            "alerts": history,
            "data_source": result.get("data_source", "unknown"),
            "test_data": result.get("test_data", False),
        })
    except Exception:
        logger.exception("Unable to evaluate current alerts")
        return jsonify({
            "status": "error",
            "message": "Unable to evaluate alerts because the Agentic AI/DL service failed.",
            "alerts": [{
                "severity": "warning",
                "code": "AGENT_SERVICE_ERROR",
                "message": "The system could not retrieve a current assessment. Check that the Deep Learning API is running and retry.",
            }],
        }), 503


@app.route("/api/alerts/<alert_id>/acknowledge", methods=["POST"])
def acknowledge_alert_route(alert_id):
    """Mark an alert as acknowledged; add authentication before public deployment."""
    try:
        alert = acknowledge_alert(alert_id)
        if alert is None:
            return jsonify({
                "status": "error",
                "message": "Alert not found",
            }), 404
        return jsonify({
            "status": "success",
            "message": "Alert acknowledged",
            "alert": alert,
        })
    except Exception:
        logger.exception("Could not acknowledge alert")
        return jsonify({
            "status": "error",
            "message": "Could not acknowledge alert.",
        }), 500


if __name__ == "__main__":
    print("==========================================")
    print("       AGENTIC AI FLASK API")
    print("==========================================")
    print("Server: http://127.0.0.1:5000")
    print("==========================================")
    # Disable the reloader to avoid starting duplicate workers and duplicate
    # background/API work during local development.
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
