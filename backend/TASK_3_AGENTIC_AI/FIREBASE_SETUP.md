# Firebase Realtime Database: existing readings → CNN-LSTM → Agentic AI

This build is configured for the actual root-level structure shown in the Firebase Console:

- `/sensor_readings/<Firebase-push-id>` — existing historical records
- `/ESP32_01` — present at the root; its internal shape is not assumed

No data is added to or changed in Firebase by reading the dashboard endpoints. The same normalized readings are used by `/api/readings`, the CNN-LSTM service, the Agentic AI decision/chatbot context, and rule-based alerts. Feedback and alert history remain in local JSON files.

## 1. Configure Firebase privately

1. In Firebase Console, copy the exact Realtime Database URL.
2. In Project settings → Service accounts, generate a private service-account JSON key.
3. Save it as `TASK_3_AGENTIC_AI/serviceAccountKey.json`. Do not include it in a ZIP or commit it to Git.
4. Copy `.env.example` to `.env` in `TASK_3_AGENTIC_AI` and configure:

```env
GEMINI_API_KEY=your_private_key_if_used
GEMINI_MODEL=gemini-3.8-flash
FIREBASE_DATABASE_URL=https://waterquality-185b4-default-rtdb.firebaseio.com
FIREBASE_SERVICE_ACCOUNT_PATH=serviceAccountKey.json
FIREBASE_SENSOR_PATH=sensor_readings
# Keep blank unless ESP32_01 contains a verified single latest-reading object.
FIREBASE_LATEST_PATH=
CLEARWATER_DL_API_URL=http://127.0.0.1:8000
CLEARWATER_DL_TIMEOUT=30
```

Use your exact database URL if it differs. The Admin SDK reads data server-side. Never put the service-account JSON or `.env` in frontend code or a shared ZIP.

## 2. Existing field mapping

Each historical record is expected to contain the fields shown in your screenshot: `TDS`, `pH`, `temperature`, `timestamp`, and `turbidity`. These are normalized to the model's input names: `pH`, `TDS_ppm`, `Temperature_C`, and `Turbidity_NTU`. Incomplete or non-numeric records are skipped.

Records are sorted by timestamp oldest-to-newest. A real CNN-LSTM result requires at least 10 valid readings; if fewer exist, the prediction is `Unavailable` rather than fabricated or duplicated.

## 3. Install and run

Install dependencies in each project environment as appropriate:

```powershell
cd TASK_3_AGENTIC_AI
python -m pip install -r requirements.txt
```

Terminal 1 — from `ClearWater_DL_API`:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 — from `TASK_3_AGENTIC_AI`:

```powershell
python -m api.agent_api
```

## 4. Verify endpoints

- `GET http://127.0.0.1:5000/api/health` — configured storage backend
- `GET http://127.0.0.1:5000/api/readings` — actual existing Firebase records
- `GET http://127.0.0.1:5000/api/water-quality` — Agentic AI and model assessment
- `POST http://127.0.0.1:5000/api/chat` — chatbot (JSON body: `{"question":"What are my current readings?"}`)
- `POST http://127.0.0.1:5000/api/feedback` and `GET /api/feedback` — feedback stored in `feedback/feedback_data.json`
- `GET http://127.0.0.1:5000/api/alerts` — evaluate current assessment and store alert history in `data/alerts_data.json`
- `POST http://127.0.0.1:5000/api/alerts/<alert_id>/acknowledge` — acknowledge an alert

If Firebase is configured but the URL, credentials, rules, or path is wrong, fix the configuration; do not treat local JSON as Firebase data. The alert endpoint evaluates alerts when requested; there is no continuous background monitor or SMS/email/push notification in this build.

## 5. Security and interpretation

Feedback and alerts use JSON storage locally as requested. Protect API endpoints with authentication before internet exposure. This project's model and CMI/WQI output do not certify drinking-water safety; use appropriate laboratory testing and local guidance.
