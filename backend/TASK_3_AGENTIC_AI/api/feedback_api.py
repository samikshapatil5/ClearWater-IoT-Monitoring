"""Standalone feedback API for ClearWater; runs on port 5001."""
from flask import Flask, jsonify, request
from flask_cors import CORS
from feedback.feedback import submit_feedback, get_all_feedback

app = Flask(__name__)
CORS(app)

@app.get("/")
def home():
    return jsonify({"status": "success", "service": "ClearWater Feedback API", "docs": "Use GET/POST /api/feedback"})

@app.get("/api/health")
def health():
    return jsonify({"status": "healthy", "service": "ClearWater Feedback API", "storage": "local_json"})

@app.post("/api/feedback")
def create_feedback():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"status": "error", "message": "A JSON request body is required."}), 400
    feedback_type = body.get("feedback_type")
    user_feedback = body.get("user_feedback")
    agent_result = body.get("agent_result") or {}
    if not isinstance(agent_result, dict):
        return jsonify({"status": "error", "message": "agent_result must be a JSON object when provided."}), 400
    decision = agent_result.get("decision") or {}
    prediction = decision.get("model_prediction", agent_result.get("model_prediction"))
    recommendation = agent_result.get("recommendation")
    water_quality = agent_result.get("water_quality")
    try:
        record = submit_feedback(
            feedback_type=feedback_type,
            user_feedback=user_feedback,
            prediction=prediction,
            recommendation=recommendation,
            water_quality=water_quality,
        )
        return jsonify({"status": "success", "message": "Feedback stored successfully.", "data": record}), 201
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception:
        app.logger.exception("Feedback save failed")
        return jsonify({"status": "error", "message": "Feedback could not be stored. Check the API server log."}), 500

@app.get("/api/feedback")
def list_feedback():
    try:
        records = get_all_feedback()
        return jsonify({"status": "success", "count": len(records), "feedback": records})
    except Exception:
        app.logger.exception("Feedback read failed")
        return jsonify({"status": "error", "message": "Feedback records could not be read."}), 500

if __name__ == "__main__":
    print("ClearWater Feedback API: http://127.0.0.1:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
