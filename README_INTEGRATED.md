# ClearWater Integrated Frontend + Python Backend

This package keeps the existing React/Vite UI and integrates the supplied Python Agentic AI backend and FastAPI CNN-LSTM service. The original Node backend source is preserved in `backend_original_preserved/`; it is not started because the React UI now calls the Python APIs through Vite.

## What is connected

- Home: latest sensor values, parameter analysis, CNN-LSTM prediction/confidence, overall decision and project CMI/WQI from `GET /api/dashboard`.
- Sensor Readings: loads the current dashboard assessment; manual readings post to the Agentic API and refresh the assessment.
- Analysis: uses current backend readings, analysis and recorded sensor history.
- 10-Day History: `GET /api/readings/history` groups actual records by India local calendar date. Empty dates stay empty; no synthetic readings are inserted.
- Agentic AI: `POST /api/agentic/ask` adapts the existing `generate_response()` result to the frontend's chat UI.
- Alerts: `GET /api/alerts` displays generated/persisted backend alert records.
- Feedback: `POST /api/feedback` accepts the existing UI rating/category/note and stores it using the Python feedback JSON implementation; `GET /api/feedback` retrieves stored feedback.

## Important credentials note

For security, this shareable ZIP intentionally does **not** contain the uploaded `.env` or `serviceAccountKey.json` private credentials. Do not distribute those files. Copy `backend/TASK_3_AGENTIC_AI/.env.example` to `backend/TASK_3_AGENTIC_AI/.env`, fill in your own `GEMINI_API_KEY` and Firebase settings, and place your private Firebase service-account file at `backend/TASK_3_AGENTIC_AI/serviceAccountKey.json`. Since private credentials were present in the uploaded archive, rotate/revoke the exposed Gemini API key and Firebase service-account key before further sharing.

## Setup

Use Python 3.11 for the DL service (TensorFlow may not support the Python 3.15 interpreter shown in your screenshots). In a terminal: 

```powershell
cd backend\TASK_3_AGENTIC_AI
py -3.11 -m pip install -r requirements.txt
cd ..\ClearWater_DL_API
py -3.11 -m pip install -r requirements.txt
cd ..\..
npm install
```

Then configure the private `.env` and service-account JSON as described above. Run `run-all.bat`; it opens separate windows for the DL API (8000), Agentic AI Flask API (5000), and Vite frontend (5173).

## API checks

- `http://127.0.0.1:5000/api/health`
- `http://127.0.0.1:5000/api/dashboard`
- `http://127.0.0.1:5000/api/readings/history`
- `http://127.0.0.1:5000/api/alerts`
- `http://127.0.0.1:8000/docs`

The CNN-LSTM requires 10 valid chronological sensor readings. If Firebase is not configured, the Agentic API uses local JSON storage and will report unavailable data/model results rather than fabricate live readings. CMI/WQI and the four measured parameters are not a laboratory certification of drinking-water safety.
