"""Train the project's CNN-LSTM on REAL labelled water-quality data.

Expected CSV columns:
  ph,turbidity,tds,temperature,label
Label should be Safe/Contaminated (or 0/1).
The script creates temporal sliding windows, as required by the project synopsis.
"""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

BASE = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE / "models"
MODEL_DIR.mkdir(exist_ok=True)
FEATURES = ["ph", "turbidity", "tds", "temperature"]


def make_windows(df, window):
    X, y = [], []
    values = df[FEATURES].to_numpy(dtype=np.float32)
    labels = df["label_num"].to_numpy(dtype=np.float32)
    for i in range(window - 1, len(df)):
        X.append(values[i-window+1:i+1])
        y.append(labels[i])
    return np.asarray(X), np.asarray(y)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--window", type=int, default=12)
    parser.add_argument("--epochs", type=int, default=25)
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    missing = [c for c in FEATURES + ["label"] if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")
    df = df[FEATURES + ["label"]].dropna().copy()
    df["label_num"] = df["label"].astype(str).str.lower().map({"safe": 0, "contaminated": 1, "0": 0, "1": 1})
    df = df.dropna(subset=["label_num"])
    if len(df) < args.window * 5:
        raise SystemExit("Not enough labelled rows for temporal windows. Provide a larger real dataset.")

    # Scale using only the training portion to avoid leakage.
    split = int(len(df) * 0.8)
    train_df, test_df = df.iloc[:split].copy(), df.iloc[split:].copy()
    scaler = StandardScaler()
    train_df[FEATURES] = scaler.fit_transform(train_df[FEATURES])
    test_df[FEATURES] = scaler.transform(test_df[FEATURES])

    X_train, y_train = make_windows(train_df, args.window)
    X_test, y_test = make_windows(test_df, args.window)

    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(args.window, len(FEATURES))),
        tf.keras.layers.Conv1D(64, 3, activation="relu", padding="same"),
        tf.keras.layers.MaxPooling1D(2),
        tf.keras.layers.LSTM(64),
        tf.keras.layers.Dropout(0.25),
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy", tf.keras.metrics.AUC(name="auc")])
    model.fit(X_train, y_train, validation_split=0.2, epochs=args.epochs, batch_size=32, verbose=1)
    metrics = model.evaluate(X_test, y_test, verbose=0)
    print(dict(zip(model.metrics_names, metrics)))

    model.save(MODEL_DIR / "cnn_lstm.keras")
    joblib.dump(scaler, MODEL_DIR / "scaler.joblib")
    print("Saved models/cnn_lstm.keras and models/scaler.joblib")

if __name__ == "__main__":
    main()
