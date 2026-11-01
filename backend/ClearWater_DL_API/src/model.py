import os
import numpy as np
import tensorflow as tf

from preprocessing.preprocess import preprocess_sequence


# ============================================================
# MODEL PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "best_cnn_lstm.keras"
)


# ============================================================
# LOAD CNN-LSTM MODEL
# ============================================================

def load_cnn_lstm_model():

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"\nModel not found!\n"
            f"Expected location:\n{MODEL_PATH}\n"
        )

    print("\nLoading CNN-LSTM model...")
    print(f"Model path: {MODEL_PATH}")

    model = tf.keras.models.load_model(
        MODEL_PATH,
        compile=False
    )

    print("CNN-LSTM model loaded successfully!")

    return model


# ============================================================
# PREDICT WATER QUALITY
# ============================================================

def predict_water_quality(model, sensor_readings):

    # --------------------------------------------------------
    # PREPROCESS
    # --------------------------------------------------------

    processed_data = preprocess_sequence(
        sensor_readings
    )

    # --------------------------------------------------------
    # MODEL PREDICTION
    # --------------------------------------------------------

    probability = model.predict(
        processed_data,
        verbose=0
    )[0][0]

    probability = float(probability)

    # --------------------------------------------------------
    # CLASSIFICATION
    # --------------------------------------------------------

    if probability >= 0.5:

        prediction = "UNSAFE"
        confidence = probability * 100

    else:

        prediction = "SAFE"
        confidence = (1 - probability) * 100

    return {
        "prediction": prediction,
        "probability": probability,
        "confidence": confidence
    }


# ============================================================
# TEST COMPLETE DL PIPELINE
# ============================================================

if __name__ == "__main__":

    try:

        # ----------------------------------------------------
        # LOAD MODEL
        # ----------------------------------------------------

        model = load_cnn_lstm_model()

        print("\n" + "=" * 60)
        print("CNN-LSTM MODEL INFORMATION")
        print("=" * 60)

        print(f"Input shape : {model.input_shape}")
        print(f"Output shape: {model.output_shape}")

        # ----------------------------------------------------
        # SAMPLE SENSOR DATA
        # ----------------------------------------------------
        #
        # 10 consecutive readings
        #
        # Feature order:
        # pH
        # TDS_ppm
        # Turbidity_NTU
        # Temperature_C
        #
        # ----------------------------------------------------

        sample_readings = np.array([

            [7.2, 450, 3.5, 25.0],
            [7.3, 455, 3.7, 25.1],
            [7.2, 460, 3.6, 25.2],
            [7.1, 458, 3.8, 25.0],
            [7.2, 462, 3.9, 25.3],
            [7.3, 465, 4.0, 25.4],
            [7.2, 468, 3.8, 25.2],
            [7.1, 470, 4.1, 25.5],
            [7.2, 472, 4.0, 25.3],
            [7.3, 475, 3.9, 25.4]

        ], dtype=np.float32)

        # ----------------------------------------------------
        # PREDICTION
        # ----------------------------------------------------

        result = predict_water_quality(
            model,
            sample_readings
        )

        # ----------------------------------------------------
        # DISPLAY RESULT
        # ----------------------------------------------------

        print("\n" + "=" * 60)
        print("WATER QUALITY PREDICTION")
        print("=" * 60)

        print(
            f"\nPrediction  : {result['prediction']}"
        )

        print(
            f"Probability : {result['probability']:.4f}"
        )

        print(
            f"Confidence  : {result['confidence']:.2f}%"
        )

        print("\n" + "=" * 60)
        print("COMPLETE DL PIPELINE TEST PASSED")
        print("=" * 60)

    except Exception as e:

        print("\n" + "=" * 60)
        print("DL PIPELINE FAILED")
        print("=" * 60)

        print(f"\nError:\n{e}")

        raise