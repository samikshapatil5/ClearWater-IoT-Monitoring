"""Standalone alert-generation API for ClearWater; runs on port 5002."""
from flask import Flask, jsonify
from flask_cors import CORS
from agent.agent import run_agent
from alerts.alert_service import generate_alerts, get_all_alerts, acknowledge_alert

app = Flask(__name__)
CORS(app)

def evaluate_current_assessment():
    result = run_agent()
    generated = generate_alerts(result)
    return result, generated

@app.get("/")
def home():
    return jsonify({"status": "success", "service": "ClearWater Alert API", "endpoints": ["GET /api/alerts", "POST /api/alerts/evaluate", "POST /api/alerts/<alert_id>/acknowledge"]})

@app.get("/api/health")
def health():
    return jsonify({"status": "healthy", "service": "ClearWater Alert API", "storage": "local_json"})

@app.get("/api/alerts")
def list_and_evaluate_alerts():
    """Evaluate current data, persist newly generated alerts, and return stored history."""
    try:
        result, generated = evaluate_current_assessment()
        history = get_all_alerts()
        return jsonify({
            "status": "success",
            "new_alert_count": len(generated),
            "count": len(history),
            "alerts": history,
            "data_source": result.get("data_source", "unknown"),
            "test_data": bool(result.get("test_data", False)),
        })
    except Exception:
        app.logger.exception("Alert evaluation failed")
        return jsonify({"status": "error", "message": "Could not evaluate alerts. Check Firebase settings and that the Deep Learning API is running.", "alerts": []}), 503

@app.post("/api/alerts/evaluate")
def evaluate_alerts():
    """Explicitly run assessment and generate alerts now."""
    try:
        result, generated = evaluate_current_assessment()
        return jsonify({"status": "success", "new_alert_count": len(generated), "generated": generated, "alerts": get_all_alerts(), "data_source": result.get("data_source", "unknown")})
    except Exception:
        app.logger.exception("Alert evaluation failed")
        return jsonify({"status": "error", "message": "Could not evaluate alerts. Check Firebase settings and that the Deep Learning API is running."}), 503

@app.post("/api/alerts/<alert_id>/acknowledge")
def acknowledge(alert_id):
    try:
        record = acknowledge_alert(alert_id)
        if record is None:
            return jsonify({"status": "error", "message": "Alert not found."}), 404
        return jsonify({"status": "success", "message": "Alert acknowledged.", "alert": record})
    except Exception:
        app.logger.exception("Alert acknowledgement failed")
        return jsonify({"status": "error", "message": "Could not acknowledge alert."}), 500

if __name__ == "__main__":
    print("ClearWater Alert API: http://127.0.0.1:5002")
    app.run(host="0.0.0.0", port=5002, debug=False)
