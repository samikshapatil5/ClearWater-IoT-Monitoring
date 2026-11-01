# Project Requirements — Current Package

## Core requirement

The key functional requirement is:

**A sensor reading is received/stored, and when a user asks Agentic AI a question, Agentic AI must use the latest sensor reading to produce the response.**

## Implemented in this ZIP

| Requirement | Status | Implementation |
|---|---|---|
| pH sensor value | Included | `/api/readings`, Sensing page |
| Turbidity value | Included | `/api/readings`, Sensing page |
| TDS value | Included | `/api/readings`, Sensing page |
| Temperature value | Included | `/api/readings`, Sensing page |
| Latest reading storage | Included | `backend/data/readings.json` |
| Reading history | Included | `history` array + `/api/readings/history` |
| User asks a question | Included | Agentic AI chat page |
| Agentic AI reads current sensor values | Included | Monitoring Agent in `/api/agentic/ask` |
| Sensor-aware decision | Included | Decision Agent + configured demo checks |
| Knowledge retrieval | Included | `backend/knowledge/water-quality.json` |
| Action/recommendation | Included | Recommendation Agent |
| Agent orchestration display | Included | Agentic AI page |
| Demo sensor input without hardware | Included | Sensing page → Send reading |
| ESP32/MQTT integration foundation | Included | MQTT subscriber in backend |
| Optional external LLM | Included | backend-only `.env` configuration |
| Feedback integration | Included | `/api/feedback` |

## Example expected behaviour

If the latest reading is:

```json
{"ph":9.2,"turbidity":8,"tds":700,"temperature":28}
```

and the user asks:

> Is the water safe right now?

Agentic AI should answer using those current values and identify that pH, turbidity and TDS fail the configured demo checks.

If the user then sends:

```json
{"ph":7.2,"turbidity":2.1,"tds":320,"temperature":26}
```

and asks the same question, the response changes because Agentic AI reads the new latest packet.

## Final project work still required

1. Connect and calibrate the physical ESP32 sensors.
2. Publish real readings to the MQTT topic.
3. Replace demo threshold values with validated project standards.
4. Train and expose the actual CNN-LSTM model/API using the project dataset.
5. Connect production storage/time-series database if required.
6. Configure real alerts/notifications and production authentication/security.
7. Perform end-to-end hardware → MQTT → backend → CNN-LSTM → Agentic AI testing.
