# Predict from existing Firebase readings

The Swagger page at `http://127.0.0.1:8000/docs` shows a JSON example for `POST /predict`; that example is for manual testing only. It is not automatically loaded from Firebase.

Use `GET /predict-from-firebase` to fetch the latest 10 valid records from the existing root `/sensor_readings` node and run the model. It does not write to Firebase and never creates fake readings. The result includes `source.source = firebase`, the path, number of valid readings, and the Firebase keys used.

You can also call `POST /predict` with no request body to trigger the same Firebase-backed behavior. If a JSON body is provided, `/predict` intentionally uses that manual request body.

## Configuration

The API loads Firebase settings from `TASK_3_AGENTIC_AI/.env`. It resolves a relative `FIREBASE_SERVICE_ACCOUNT_PATH` from `TASK_3_AGENTIC_AI`, matching the sibling-project setup. Expected settings:

```env
FIREBASE_DATABASE_URL=https://YOUR-PROJECT-default-rtdb.firebaseio.com
FIREBASE_SERVICE_ACCOUNT_PATH=../serviceAccountKey.json
FIREBASE_SENSOR_PATH=sensor_readings
```

Install updated dependencies inside the `ClearWater_DL_API` virtual environment:

```powershell
python -m pip install -r requirements.txt
```

If fewer than 10 valid readings are found, the endpoint returns an explicit error instead of using zeros or dummy data.
