# TASK 3 — Agentic AI Layer

## IoT Enabled Water Quality Monitoring Using Deep Learning with Agentic AI Chatbot and Feedback Integration

---

## 1. Project Overview

This project develops an IoT-enabled water-quality monitoring system that combines IoT sensors, a Deep Learning model, and an Agentic AI chatbot.

The system monitors four water-quality parameters:

- pH
- Total Dissolved Solids (TDS)
- Turbidity
- Water Temperature

The monitored data is analyzed using a 1D CNN-LSTM Deep Learning model to classify the monitored water quality as:

- Safe
- Unsafe

The Agentic AI layer uses the sensor readings, model prediction, knowledge base, interpretation rules, and recommendations to reason about the water-quality condition and provide understandable responses to the user.

---

## 2. Task 3 — Agentic AI Layer

The main objective of Task 3 is to develop an Agentic AI system that can:

1. Receive water-quality data.
2. Use the Deep Learning model prediction.
3. Interpret individual water-quality parameters.
4. Make an overall water-quality decision.
5. Generate recommendations.
6. Answer user questions through a chatbot.
7. Collect and store user feedback.
8. Integrate all components into one working pipeline.

---

## 3. System Architecture

The Agentic AI workflow is:

```text
Water Quality Data
        |
        v
Water Quality Tool
        |
        v
CNN-LSTM Model
        |
        v
Reasoning
        |
        v
Decision
        |
        v
Recommendation
        |
        v
Chatbot
        |
        v
User Feedback
        |
        v
Feedback Storage

## Firebase Realtime Database

Sensor records can be stored in Firebase Realtime Database. Follow [`FIREBASE_SETUP.md`](FIREBASE_SETUP.md) to configure `FIREBASE_DATABASE_URL`, `FIREBASE_SERVICE_ACCOUNT_PATH`, and `FIREBASE_SENSOR_PATH` in a local `.env` file. The private Firebase service-account JSON is intentionally not included in this ZIP.

When Firebase is configured, `POST /api/readings` stores incoming readings under `sensor_readings/<push-id>` by default, and both history retrieval and Agentic AI current-reading retrieval use that Firebase history. If Firebase is not configured, local JSON storage is used only as a development fallback.

## Knowledge-base runtime wiring (updated)

All six knowledge-base JSON files are now used by live application code:

- `parameters.json`: parameter descriptions/units are loaded by `agent/reasoning.py` and used by chatbot definition questions.
- `standards.json`: reference-standard metadata is attached to the analysis and is used by recommendations to distinguish pH below/above its configured range; chatbot standards questions read this file.
- `interpretation_rules.json`: parameter thresholds and meanings are read by `agent/reasoning.py`; the overall decision policy is read by `agent/decision.py` from its `decision_policy` section.
- `recommendations.json`: recommendation text and selection mappings are read by `agent/recommendation.py`. Selection mappings live in JSON so parameter/status key choices are not hard-coded in Python.
- `model_knowledge.json`: model-purpose and architecture explanations are used in chatbot model questions.
- `faq.json`: FAQ lookup remains connected to the chatbot.

The standalone `if __name__ == "__main__"` examples in Python files are test/demo examples only. The live agent must use readings returned by the configured history backend. No sample reading is silently substituted when history is empty, and the CNN-LSTM result remains unavailable until 10 actual chronological readings are available and the DL API returns a valid result.

To verify Python syntax, run from this directory:

```bash
python -m compileall -q agent api chatbot tools feedback
```

The configured thresholds are project reference rules, not a complete laboratory assessment or a guarantee that water is safe to drink.


## Optional OpenAI explanation layer

The Python agent still calculates parameter analysis, the overall decision, and recommendations. When `OPENAI_API_KEY` is configured in this backend's local `.env`, `/api/chat` passes those already-computed results and the user's question to OpenAI so it can explain them in conversational language. OpenAI is not allowed by the prompt to change the decision or invent readings.

1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` if you have not already done so.
3. Add your private key as `OPENAI_API_KEY=...`; optionally set `OPENAI_MODEL=gpt-4.1-mini`.
4. Restart the Flask API.

If the key is missing or the OpenAI request fails, the chatbot falls back to its existing built-in knowledge-base responses. API usage may incur charges. Never put the key in frontend code or commit the real `.env` file.

## Precautions, remedies, and follow-up advice

The agent now includes `agent/safety_advice.py`, which builds structured `precautions`, `remedies`, and `follow_up` lists from the current readings, parameter analysis, and overall decision. These lists are included in the agent result and passed to the optional OpenAI conversational layer so it can explain them to the user. The decision and recommendation remain Python-controlled; OpenAI explains rather than overrides them. Remedies are general guidance only: the system does not prescribe chemical doses, and treatment selection requires suitable water testing and qualified advice.

Run tests from this directory with:

```bash
PYTHONPATH=. pytest -q
```

## CMI/WQI is now part of the Agentic AI decision

The DL API returns the project-specific ClearWater Monitoring Index in `data.wqi` (score in `wqi`, category in `category`). `tools/model_tool.py` carries this result as `model_prediction["cmi"]`; `agent/agent.py` now passes it into `agent/decision.py`. The decision output includes `wqi_score`, `wqi_category`, and `wqi_status_contribution`, and the same context is passed to OpenAI for explanation.

Current project policy: `POOR` CMI contributes to `Unsafe`; `FAIR` or `MARGINAL` contributes to `Warning`; `GOOD` or `EXCELLENT` is supportive but cannot override an unsafe parameter or an Unsafe CNN-LSTM prediction. If the required CNN-LSTM prediction or CMI result is unavailable and no unsafe evidence already exists, the overall result is `Insufficient data`, not `Safe`. These are project rules, not official CCME WQI categories or a drinking-water safety certification.

Run the WQI decision tests with `PYTHONPATH=. pytest -q tests/test_wqi_decision.py`.
