from flask import Flask, jsonify
from flask_cors import CORS

from agent.agent import run_agent

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return jsonify({
        "message": "AquaSense Agentic AI Backend is running",
        "status": "online"
    })


@app.route("/api/water-quality", methods=["GET"])
def water_quality():
    try:
        result = run_agent()

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    print("====================================")
    print("     AQUASENSE BACKEND SERVER")
    print("====================================")
    print("Server running at: http://127.0.0.1:5000")
    print("Water Quality API: http://127.0.0.1:5000/api/water-quality")
    print("====================================")

    app.run(host="127.0.0.1", port=5000, debug=True)