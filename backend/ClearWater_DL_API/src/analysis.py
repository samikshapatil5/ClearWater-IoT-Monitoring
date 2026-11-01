from functools import lru_cache
from math import isfinite

from src.model import load_cnn_lstm_model, predict_water_quality
from src.wqi import calculate_cmi


# ============================================================
# CLEARWATER ANALYSIS LAYER
# CNN-LSTM + CLEARWATER MONITORING INDEX
# ============================================================

FEATURE_NAMES = [
    "pH",
    "TDS_ppm",
    "Turbidity_NTU",
    "Temperature_C",
]

SEQUENCE_LENGTH = 10


# ============================================================
# LOAD THE TRAINED MODEL
# ============================================================

@lru_cache(maxsize=1)
def get_model():
    """
    Load the trained CNN-LSTM model once per Python process.

    Caching avoids repeatedly loading the model for every
    prediction request.
    """
    return load_cnn_lstm_model()


# ============================================================
# VALIDATE SENSOR DATA
# ============================================================

def validate_sensor_data(sensor_readings):
    """
    Validate the sensor sequence.

    Expected input:
        Exactly 10 readings.
        Each reading contains 4 values in this order:

        pH, TDS_ppm, Turbidity_NTU, Temperature_C
    """

    if sensor_readings is None:
        raise ValueError(
            "Sensor readings cannot be None."
        )

    try:
        readings = list(sensor_readings)
    except TypeError:
        raise ValueError(
            "Sensor readings must be a sequence of readings."
        ) from None

    if len(readings) != SEQUENCE_LENGTH:
        raise ValueError(
            f"Exactly {SEQUENCE_LENGTH} sensor readings "
            f"are required. Received {len(readings)}."
        )

    validated_readings = []

    for index, reading in enumerate(readings, start=1):

        if isinstance(reading, (str, bytes)):
            raise ValueError(
                f"Reading {index} must contain four numeric values."
            )

        try:
            values = list(reading)
        except TypeError:
            raise ValueError(
                f"Reading {index} must be a sequence."
            ) from None

        if len(values) != len(FEATURE_NAMES):
            raise ValueError(
                f"Reading {index} must contain exactly four values."
            )

        validated_values = []

        for feature_name, value in zip(FEATURE_NAMES, values):

            try:
                value = float(value)
            except (TypeError, ValueError, OverflowError):
                raise ValueError(
                    f"Reading {index}: {feature_name} "
                    "must be numeric."
                ) from None

            if not isfinite(value):
                raise ValueError(
                    f"Reading {index}: {feature_name} "
                    "must be finite."
                )

            validated_values.append(value)

        ph, tds, turbidity, temperature = validated_values

        if not 0 < ph <= 14:
            raise ValueError(
                f"Reading {index}: pH must be greater than 0 "
                "and at most 14."
            )

        if tds < 0:
            raise ValueError(
                f"Reading {index}: TDS cannot be negative."
            )

        if turbidity < 0:
            raise ValueError(
                f"Reading {index}: turbidity cannot be negative."
            )

        validated_readings.append(validated_values)

    return validated_readings


# ============================================================
# COMBINED WATER QUALITY ANALYSIS
# ============================================================

def analyze_water_quality(sensor_readings):
    """
    Combine CNN-LSTM classification with the ClearWater
    Monitoring Index.

    CNN-LSTM:
        Uses the 10 sensor readings to predict SAFE or UNSAFE.

    CMI:
        Evaluates all 10 readings against the selected
        monitoring objectives.

    Returns:
        cnn_lstm
        wqi
        latest_sensor_reading
        readings_used
    """

    # --------------------------------------------------------
    # Step 1: Validate the input
    # --------------------------------------------------------

    readings = validate_sensor_data(sensor_readings)

    # --------------------------------------------------------
    # Step 2: CNN-LSTM prediction
    # --------------------------------------------------------

    model = get_model()

    cnn_result = predict_water_quality(
        model,
        readings
    )

    # --------------------------------------------------------
    # Step 3: Monitoring index over all 10 readings
    # --------------------------------------------------------

    cmi_result = calculate_cmi(
        readings
    )

    # --------------------------------------------------------
    # Step 4: Extract the latest sensor reading
    # --------------------------------------------------------

    latest_values = readings[-1]

    latest_reading = {
        feature_name: value
        for feature_name, value in zip(
            FEATURE_NAMES,
            latest_values
        )
    }

    # --------------------------------------------------------
    # Step 5: Return the combined result
    # --------------------------------------------------------

    return {
        "cnn_lstm": cnn_result,

        "wqi": cmi_result,

        "latest_sensor_reading": latest_reading,

        "readings_used": len(readings),
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 65)
    print("CLEARWATER COMBINED ANALYSIS TEST")
    print("=" * 65)

    # Illustrative test data only.
    # These are not live sensor measurements.

    sample_readings = [
        [7.0, 300, 0.8, 25.0],
        [7.1, 310, 1.2, 25.1],
        [7.0, 320, 1.4, 25.2],
        [7.2, 330, 1.1, 25.0],
        [7.1, 340, 1.6, 25.3],
        [7.0, 350, 0.9, 25.1],
        [7.2, 360, 1.8, 25.4],
        [7.1, 370, 0.8, 25.2],
        [7.0, 380, 1.5, 25.3],
        [7.2, 390, 2.1, 25.4],
    ]

    result = analyze_water_quality(
        sample_readings
    )

    print("\nCNN-LSTM Result:")

    for key, value in result["cnn_lstm"].items():
        print(f"{key}: {value}")

    print("\nClearWater Monitoring Index:")

    print(
        "CMI score:",
        result["wqi"]["wqi"]
    )

    print(
        "Category:",
        result["wqi"]["category"]
    )

    print(
        "Readings used:",
        result["wqi"]["readings_used"]
    )

    print("\nParameter assessments:")

    for name, details in result["wqi"]["parameter_status"].items():

        print(
            f"{name}: {details['status']} "
            f"({details['failed_tests']}/"
            f"{details['tests']} failed)"
        )

    print("\nLatest sensor reading:")
    print(result["latest_sensor_reading"])

    print("\nTotal readings processed:")
    print(result["readings_used"])

    print("\n" + "=" * 65)
    print("COMBINED ANALYSIS TEST COMPLETED")
    print("=" * 65)