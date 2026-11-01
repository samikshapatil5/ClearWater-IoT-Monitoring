# ClearWater Implementation Architecture

## Project flow

ESP32 + pH/Turbidity/TDS/Temperature sensors
→ Wi-Fi/MQTT
→ Node.js backend + storage
→ preprocessing
→ CNN-LSTM model service
→ Agentic AI orchestration
→ React dashboard/chatbot
→ feedback and alerts.

## Agentic AI flow

1. Intent Agent — determines what the user is asking.
2. Monitoring Agent — retrieves the latest sensor packet.
3. Knowledge/RAG Agent — retrieves relevant water-quality information.
4. Decision Agent — combines model prediction, confidence and configured checks.
5. Recommendation Agent — proposes the next step.
6. Response — LLM (optional) converts the verified context into a natural-language answer.

## Important distinction

A normal chatbot answers from an LLM. ClearWater's Agentic AI is context-driven: it must read the latest sensor values before answering monitoring questions. The LLM is not allowed to invent sensor values.

## Deep learning

`ml_service/train.py` trains a real CNN-LSTM from a labelled dataset with columns:
`ph,turbidity,tds,temperature,label`.

The training script creates temporal sliding windows and saves:
- `models/cnn_lstm.keras`
- `models/scaler.joblib`

`ml_service/app.py` exposes `POST /predict` for live inference. Until a trained model is installed, the service explicitly labels its result as `demo threshold fallback`.

## Hardware

`iot/esp32_water_quality.ino` publishes JSON to:
`water/wqm-01/readings`.

The sensor conversion formulas in the Arduino sketch are placeholders and must be calibrated against the actual modules before real measurements are used.
