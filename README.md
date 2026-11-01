# ClearWater — IoT Water Quality Monitoring + Agentic AI

## What this version actually does

The main flow is now:

**Sensor reading → Backend stores latest values → User asks Agentic AI → Monitoring Agent reads latest values → Decision Agent checks them → Knowledge Agent retrieves relevant project knowledge → Agentic AI gives an answer + recommendation.**

The four sensor parameters are:
- pH
- Turbidity (NTU)
- TDS (mg/L)
- Temperature (°C)

The same backend accepts readings from the **Demo Sensor Input** page or from an **ESP32/MQTT** message.

## Run the project

Requirements: Node.js 18+ recommended.

### Windows easiest way
1. Extract this ZIP.
2. Open the extracted `water-quality-monitoring-frontend` folder.
3. Double-click `run.bat`.
4. Open the Vite URL shown in the terminal (normally `http://localhost:5173`).
5. Login/register if the UI asks for it.
6. Open **Sensing** and use **Send a new sensor reading** to test different values.
7. Open **Agentic AI** and ask questions about those values.

### Terminal way
```bash
npm install
npm run dev
```

The root `npm run dev` starts both Vite and the Express backend.

## Test the requested workflow

Example 1:
1. Sensing → set pH = `9.2`, turbidity = `8`, TDS = `700`, temperature = `28`.
2. Click **Send reading to backend**.
3. Open Agentic AI.
4. Ask: **Is the water safe right now?**
5. The answer will use the new sensor values and explain which configured checks failed.

Example 2:
1. Set pH = `7.2`, turbidity = `2.1`, TDS = `320`, temperature = `26`.
2. Send the reading.
3. Ask: **Is the pH normal?**, **What is the current TDS?**, or **What should I check next?**
4. Agentic AI reads the latest stored sensor packet before responding.

## Agentic AI pipeline

1. **Intent Agent** — identifies whether the question is about safety, pH, turbidity, TDS, temperature, trends, prediction, actions or the system.
2. **Monitoring Agent** — loads the latest WQM-01 sensor reading.
3. **Knowledge Agent** — retrieves relevant content from `backend/knowledge/water-quality.json`.
4. **Decision Agent** — evaluates the current sensor values and configured demo thresholds.
5. **Recommendation Agent** — produces the next action or monitoring advice.
6. **Response** — returns the answer, evidence, recommendation and the stages used.

The Agentic AI page also refreshes the monitoring context every 5 seconds so the displayed sensor values follow the backend.

## API endpoints

- `GET /api/health` — backend status
- `GET /api/readings` — latest reading + history
- `GET /api/readings/history` — stored reading history
- `POST /api/readings` — add a new sensor reading
- `POST /api/agentic/ask` — ask Agentic AI using the latest sensor context
- `POST /api/feedback` — store user feedback

Example sensor JSON:
```json
{
  "nodeId": "WQM-01",
  "ph": 7.18,
  "turbidity": 2.4,
  "tds": 318,
  "temperature": 26.4
}
```

## MQTT / ESP32

Copy `backend/.env.example` to `backend/.env` and configure:

```env
MQTT_BROKER_URL=
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC=water/wqm-01/readings
```

The backend subscribes to the topic and accepts the same four numeric fields. When an MQTT packet arrives, it becomes the latest reading used by Agentic AI.

## Optional LLM

The project works without an external AI key using the built-in agentic reasoning + knowledge retrieval. For richer natural-language responses, configure an OpenAI-compatible Chat Completions endpoint in `backend/.env`:

```env
LLM_BASE_URL=https://api.openai.com/v1/chat/completions
LLM_API_KEY=
LLM_MODEL=
```

Keep the API key in the backend `.env`; do not put it in React/frontend code.

## Important project note

The current threshold values are **demo/project rules**, not a certification of drinking-water safety. They are currently:
- pH: 6.5–8.5
- Turbidity: ≤ 5 NTU
- TDS: ≤ 500 mg/L
- Temperature: 0–40 °C

For the final academic/real deployment, validate the thresholds against the standards selected by your project and connect the trained CNN-LSTM model/API.

## Included vs final hardware work

Included and working in this package:
- React/Vite frontend
- Sensor dashboard and live context
- Demo sensor input
- Express backend
- Latest-reading storage
- Reading history
- Agentic question/answer endpoint
- Intent, monitoring, knowledge, decision and recommendation stages
- Local knowledge retrieval
- Optional LLM integration
- MQTT subscriber foundation
- Feedback storage

Still dependent on your physical/production setup:
- ESP32 wiring and calibration
- Real MQTT broker credentials
- Production database/time-series storage
- Actual trained CNN-LSTM model/API
- Validated water-quality thresholds
- Production authentication/security and notifications

## Full academic implementation path

For the complete version, use `run-all.bat`. It starts the React frontend, Node.js backend and (when Python is available) the CNN-LSTM API.

Train the real model with `ml_service/train.py` using your labelled real dataset. Do not describe the threshold fallback as CNN-LSTM output in the report.

See `docs/IMPLEMENTATION_ARCHITECTURE.md` for the complete sensor → MQTT → CNN-LSTM → Agentic AI flow and `iot/esp32_water_quality.ino` for the ESP32 publisher.


## Homepage visual update
The homepage now uses real-source photographs from USGS/USFWS via remote image URLs, with local fallback images preserved. The droplet animation uses the user-provided droplet reference asset. See `REAL_ASSET_UPDATE.md` for source/licensing details.
