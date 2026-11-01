# CNN-LSTM service

This service is the real deep-learning layer of ClearWater. It is deliberately separate from the Node.js Agentic AI backend.

## Train with your real dataset

CSV columns required:

`ph,turbidity,tds,temperature,label`

where `label` is `Safe` or `Contaminated`.

Run:

```powershell
cd ml_service
python -m pip install -r requirements.txt
python train.py --csv ..\data\your_real_dataset.csv --window 12 --epochs 25
```

The trained artifacts are written to `models/`.

## Start the service

```powershell
uvicorn app:app --host 0.0.0.0 --port 8000
```

The Node.js backend can use this service through `ML_SERVICE_URL=http://localhost:8000`.

If no trained model exists, `/predict` explicitly reports `demo threshold fallback`; this must not be presented as CNN-LSTM results in the final report.
