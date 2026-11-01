# Code Reference

## Frontend

- `src/App.jsx` — routes, dashboard, sensing page and Agentic AI UI.
- `src/styles.css` — visual styling.
- `vite.config.js` — `/api` proxy to backend port 5000.

## Backend

- `backend/server.js` — Express API, sensor storage, agentic orchestration, knowledge retrieval, optional LLM and MQTT subscriber.
- `backend/data/readings.json` — latest reading and recent history.
- `backend/data/feedback.json` — feedback records.
- `backend/knowledge/water-quality.json` — local knowledge used by the Knowledge Agent.

## Important endpoint

### POST `/api/agentic/ask`

Input:
```json
{"question":"Is the water safe right now?"}
```

Processing:
```text
Question
  ↓
Intent Agent
  ↓
Monitoring Agent → latest /api/readings context
  ↓
Knowledge Agent → relevant knowledge
  ↓
Decision Agent → parameter checks + prediction context
  ↓
Recommendation Agent
  ↓
Answer + evidence + recommendation + stages
```

## Sensor endpoint

### POST `/api/readings`

Input:
```json
{
  "nodeId":"WQM-01",
  "ph":7.18,
  "turbidity":2.4,
  "tds":318,
  "temperature":26.4
}
```

Every accepted reading updates the latest sensor context and appends a history point. Agentic AI reads this latest context for the next user question.
