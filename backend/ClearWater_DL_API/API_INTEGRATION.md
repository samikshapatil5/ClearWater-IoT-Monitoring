# ClearWater Deep Learning API — Integration Guide

## 1. Purpose

The ClearWater Deep Learning API connects the trained CNN-LSTM model and ClearWater Monitoring Index to the frontend and Agentic AI chatbot.

The API accepts water-quality sensor readings and returns a classification, model probability, monitoring index, parameter assessments, and the latest sensor readings.

## 2. Start the API server

Open the terminal in the ClearWater_DL_taskF project folder.

Activate the Python 3.11 environment if it is not already active:

```powershell
.\.venv311\Scripts\Activate.ps1
```

Start the API:

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

Keep the terminal open while testing.

## 3. API base URL

For frontend and backend applications running on the same computer:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

Note: If the frontend runs on another computer, 127.0.0.1 will refer to that computer, not the computer running the API.

## 4. Available endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | / | Check whether the API is running |
| GET | /health | Check service health |
| POST | /predict | Predict water quality and calculate the monitoring index |

## 5. Health endpoint

Request:

```http
GET /health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "ClearWater Deep Learning API"
}
```

## 6. Prediction endpoint

Request:

```http
POST /predict
Content-Type: application/json
```

The request must contain exactly 10 sensor readings.

Every reading must contain these four numeric fields:

| Field | Description | Unit |
|---|---|---|
| pH | Acidity or alkalinity measurement | pH units |
| TDS_ppm | Total dissolved solids | ppm |
| Turbidity_NTU | Turbidity | NTU |
| Temperature_C | Water temperature | °C |

The feature order used by the trained model is:

1. pH
2. TDS_ppm
3. Turbidity_NTU
4. Temperature_C

### Example request

The following values are illustrative and are not live sensor readings.

```json
{
  "readings": [
    {"pH": 7.0, "TDS_ppm": 300, "Turbidity_NTU": 0.8, "Temperature_C": 25.0},
    {"pH": 7.1, "TDS_ppm": 310, "Turbidity_NTU": 1.2, "Temperature_C": 25.1},
    {"pH": 7.0, "TDS_ppm": 320, "Turbidity_NTU": 1.4, "Temperature_C": 25.2},
    {"pH": 7.2, "TDS_ppm": 330, "Turbidity_NTU": 1.1, "Temperature_C": 25.0},
    {"pH": 7.1, "TDS_ppm": 340, "Turbidity_NTU": 1.6, "Temperature_C": 25.3},
    {"pH": 7.0, "TDS_ppm": 350, "Turbidity_NTU": 0.9, "Temperature_C": 25.1},
    {"pH": 7.2, "TDS_ppm": 360, "Turbidity_NTU": 1.8, "Temperature_C": 25.4},
    {"pH": 7.1, "TDS_ppm": 370, "Turbidity_NTU": 0.8, "Temperature_C": 25.2},
    {"pH": 7.0, "TDS_ppm": 380, "Turbidity_NTU": 1.5, "Temperature_C": 25.3},
    {"pH": 7.2, "TDS_ppm": 390, "Turbidity_NTU": 2.1, "Temperature_C": 25.4}
  ]
}
```

## 7. Prediction response

The endpoint returns a JSON object containing these sections:

### CNN-LSTM result

`data.cnn_lstm.prediction`

The model's Safe/Unsafe classification.

`data.cnn_lstm.probability`

The sigmoid model output representing its predicted probability for the Unsafe class.

`data.cnn_lstm.confidence`

The current implementation's confidence-like score, expressed as a percentage. This is not a calibrated guarantee of prediction correctness.

### ClearWater Monitoring Index

The current response places the monitoring index under `data.wqi`.

Important fields include:

- `data.wqi.index_name`
- `data.wqi.wqi`
- `data.wqi.category`
- `data.wqi.factors`
- `data.wqi.parameter_status`
- `data.wqi.readings_used`
- `data.wqi.interpretation`

The index evaluates pH, TDS and turbidity against selected monitoring objectives. Temperature is reported separately.

The CMI is a project-specific prototype and must not be presented as proof that water is safe to drink.

### Latest sensor readings

The latest reading is available through:

- `data.latest_sensor_reading.pH`
- `data.latest_sensor_reading.TDS_ppm`
- `data.latest_sensor_reading.Turbidity_NTU`
- `data.latest_sensor_reading.Temperature_C`

The number of processed readings is available through:

`data.readings_used`

## 8. Suggested frontend integration

1. Collect the four sensor parameters.
2. Maintain the latest 10 readings in the required format.
3. Send those readings to POST /predict.
4. Display the classification and probability.
5. Display the CMI score and category separately.
6. Display individual parameter assessments.
7. Handle validation and server errors without presenting a failed request as a valid result.

Do not label the CMI category as a drinking-water safety certification.

## 9. Important integration notes

- The API currently requires exactly 10 readings per prediction request.
- Use the existing JSON field names without changing capitalization.
- The current response uses `wqi` as the property name for the ClearWater Monitoring Index.
- The API must be running before the frontend calls it.
- Browser-based requests may require CORS configuration when the frontend and API use different origins.
- The local URL is intended for local development, not public deployment.

## 10. Current limitations

- The model's reported 100% test accuracy requires further investigation of data provenance and evaluation methodology.
- The current dataset does not retain the original timestamps or water-source identifiers.
- The CMI calculation and categories require additional scientific validation.
- Live ESP32-to-API integration has not yet been demonstrated.

These limitations should be considered during final testing and project documentation.