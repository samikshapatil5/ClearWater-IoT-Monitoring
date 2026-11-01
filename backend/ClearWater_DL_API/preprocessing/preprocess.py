import os
import joblib
import numpy as np
import pandas as pd

from functools import lru_cache


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

SCALER_PATH = os.path.join(
    BASE_DIR,
    "preprocessing",
    "scaler.pkl"
)


# ============================================================
# CONFIGURATION
# ============================================================

FEATURE_NAMES = [
    "pH",
    "TDS_ppm",
    "Turbidity_NTU",
    "Temperature_C",
]

NUMBER_OF_FEATURES = len(FEATURE_NAMES)
SEQUENCE_LENGTH = 10


# ============================================================
# LOAD ORIGINAL TRAINING SCALER
# ============================================================

@lru_cache(maxsize=1)
def load_scaler():
    """
    Load and validate the original training scaler.

    The scaler is loaded once and reused for subsequent calls.
    The original fitted scaler is not modified or retrained.
    """

    if not os.path.exists(SCALER_PATH):
        raise FileNotFoundError(
            f"\nScaler not found!\n"
            f"Expected location:\n{SCALER_PATH}\n"
        )

    scaler = joblib.load(SCALER_PATH)

    if not hasattr(scaler, "n_features_in_"):
        raise ValueError(
            "The saved scaler does not contain the expected "
            "feature-count information."
        )

    if scaler.n_features_in_ != NUMBER_OF_FEATURES:
        raise ValueError(
            f"Scaler expects {scaler.n_features_in_} features, "
            f"but the project requires {NUMBER_OF_FEATURES}."
        )

    # Check the original feature order when available.
    if hasattr(scaler, "feature_names_in_"):

        original_names = list(scaler.feature_names_in_)

        if original_names != FEATURE_NAMES:
            raise ValueError(
                "Scaler feature names or order do not match "
                f"the project configuration.\n"
                f"Expected: {FEATURE_NAMES}\n"
                f"Found: {original_names}"
            )

    return scaler


# ============================================================
# VALIDATE SENSOR READING
# ============================================================

def validate_sensor_reading(
    pH,
    TDS_ppm,
    Turbidity_NTU,
    Temperature_C,
):
    """
    Validate one sensor reading.

    Feature order:
        pH, TDS_ppm, Turbidity_NTU, Temperature_C

    Returns:
        A NumPy array with shape (4,).
    """

    values = [
        pH,
        TDS_ppm,
        Turbidity_NTU,
        Temperature_C,
    ]

    validated_values = []

    for name, value in zip(FEATURE_NAMES, values):

        if value is None:
            raise ValueError(
                f"{name} cannot be None."
            )

        try:
            value = float(value)

        except (TypeError, ValueError, OverflowError):
            raise ValueError(
                f"{name} must be a valid numeric value."
            ) from None

        if not np.isfinite(value):
            raise ValueError(
                f"{name} must be a finite numeric value."
            )

        validated_values.append(value)

    pH, TDS_ppm, Turbidity_NTU, Temperature_C = (
        validated_values
    )

    # Basic input validation.

    if not 0 < pH <= 14:
        raise ValueError(
            "pH must be greater than 0 and at most 14."
        )

    if TDS_ppm < 0:
        raise ValueError(
            "TDS cannot be negative."
        )

    if Turbidity_NTU < 0:
        raise ValueError(
            "Turbidity cannot be negative."
        )

    return np.asarray(
        validated_values,
        dtype=np.float32,
    )


# ============================================================
# CREATE NAMED DATAFRAME
# ============================================================

def _to_feature_dataframe(readings):
    """
    Create a pandas DataFrame using the exact feature names
    used when the original scaler was fitted.

    This prevents the StandardScaler feature-name warning
    when the scaler was trained using named columns.
    """

    return pd.DataFrame(
        readings,
        columns=FEATURE_NAMES,
    )


# ============================================================
# SCALE ONE SENSOR READING
# ============================================================

def scale_sensor_reading(
    pH,
    TDS_ppm,
    Turbidity_NTU,
    Temperature_C,
):
    """
    Validate and scale one raw sensor reading.

    Returns:
        Scaled NumPy array with shape (4,).
    """

    scaler = load_scaler()

    raw_data = validate_sensor_reading(
        pH,
        TDS_ppm,
        Turbidity_NTU,
        Temperature_C,
    )

    # Preserve the original feature names for the scaler.
    feature_dataframe = _to_feature_dataframe(
        raw_data.reshape(1, NUMBER_OF_FEATURES)
    )

    scaled_data = scaler.transform(
        feature_dataframe
    )

    return np.asarray(
        scaled_data[0],
        dtype=np.float32,
    )


# ============================================================
# CREATE CNN-LSTM SEQUENCE
# ============================================================

def create_sequence(readings):
    """
    Reshape ten scaled readings into the CNN-LSTM input shape.

    Input:
        (10, 4)

    Output:
        (1, 10, 4)
    """

    readings = np.asarray(
        readings,
        dtype=np.float32,
    )

    if readings.shape != (
        SEQUENCE_LENGTH,
        NUMBER_OF_FEATURES,
    ):
        raise ValueError(
            "Expected scaled readings with shape "
            f"({SEQUENCE_LENGTH}, {NUMBER_OF_FEATURES}), "
            f"but received {readings.shape}."
        )

    if not np.isfinite(readings).all():
        raise ValueError(
            "Scaled readings contain non-finite values."
        )

    return readings.reshape(
        1,
        SEQUENCE_LENGTH,
        NUMBER_OF_FEATURES,
    )


# ============================================================
# PREPROCESS TEN RAW SENSOR READINGS
# ============================================================

def preprocess_sequence(readings):
    """
    Preprocess ten raw sensor readings for CNN-LSTM inference.

    Expected feature order:
        pH, TDS_ppm, Turbidity_NTU, Temperature_C

    Expected raw input shape:
        (10, 4)

    Returned model input shape:
        (1, 10, 4)

    Important:
        The original saved scaler is reused.
        No retraining or refitting occurs here.
    """

    try:
        readings = np.asarray(
            readings,
            dtype=np.float32,
        )

    except (TypeError, ValueError, OverflowError):
        raise ValueError(
            "Sensor readings must contain valid numeric values."
        ) from None

    expected_shape = (
        SEQUENCE_LENGTH,
        NUMBER_OF_FEATURES,
    )

    if readings.shape != expected_shape:
        raise ValueError(
            f"Expected sensor data with shape {expected_shape}, "
            f"but received {readings.shape}."
        )

    if not np.isfinite(readings).all():
        raise ValueError(
            "Sensor readings contain non-finite values."
        )

    # Validate each raw reading before preprocessing.
    for index, reading in enumerate(readings, start=1):

        validate_sensor_reading(
            pH=reading[0],
            TDS_ppm=reading[1],
            Turbidity_NTU=reading[2],
            Temperature_C=reading[3],
        )

    scaler = load_scaler()

    # IMPORTANT:
    # Supply named columns matching the scaler's training data.
    feature_dataframe = _to_feature_dataframe(
        readings
    )

    scaled_readings = scaler.transform(
        feature_dataframe
    )

    scaled_readings = np.asarray(
        scaled_readings,
        dtype=np.float32,
    )

    return create_sequence(
        scaled_readings
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 65)
    print("CLEARWATER PREPROCESSING TEST")
    print("=" * 65)

    scaler = load_scaler()

    print("\nScaler loaded successfully!")
    print(f"Scaler type: {type(scaler).__name__}")
    print(f"Number of features: {scaler.n_features_in_}")
    print(f"Feature order: {FEATURE_NAMES}")

    if hasattr(scaler, "feature_names_in_"):
        print(
            "Scaler training feature names:",
            list(scaler.feature_names_in_),
        )

    # Illustrative test values only.
    # These are not live sensor measurements.

    sample_readings = np.array(
        [
            [7.2, 450, 3.5, 25.0],
            [7.3, 455, 3.7, 25.1],
            [7.2, 460, 3.6, 25.2],
            [7.1, 458, 3.8, 25.0],
            [7.2, 462, 3.9, 25.3],
            [7.3, 465, 4.0, 25.4],
            [7.2, 468, 3.8, 25.2],
            [7.1, 470, 4.1, 25.5],
            [7.2, 472, 4.0, 25.3],
            [7.3, 475, 3.9, 25.4],
        ],
        dtype=np.float32,
    )

    processed = preprocess_sequence(
        sample_readings
    )

    print("\nRaw input shape:")
    print(sample_readings.shape)

    print("\nProcessed CNN-LSTM input shape:")
    print(processed.shape)

    print("\nProcessed data:")
    print(processed)

    # Confirm that one-reading preprocessing also works.
    scaled_single = scale_sensor_reading(
        pH=7.2,
        TDS_ppm=450,
        Turbidity_NTU=3.5,
        Temperature_C=25.0,
    )

    print("\nSingle reading scaled successfully.")
    print("Scaled reading shape:", scaled_single.shape)

    # Confirm invalid pH is rejected.
    try:
        validate_sensor_reading(
            pH=0,
            TDS_ppm=300,
            Turbidity_NTU=1.0,
            Temperature_C=25.0,
        )

        raise AssertionError(
            "Invalid pH should have been rejected."
        )

    except ValueError as error:
        print("\nInvalid-input test passed:")
        print(error)

    print("\n" + "=" * 65)
    print("PREPROCESSING TEST PASSED")
    print("=" * 65)