from collections import deque
import numpy as np

from src.model import load_cnn_lstm_model
from preprocessing.preprocess import preprocess_sequence


SEQUENCE_LENGTH = 10


class RealTimeInference:

    def __init__(self):

        print("\nLoading Real-Time Inference System...")

        self.model = load_cnn_lstm_model()

        self.reading_buffer = deque(
            maxlen=SEQUENCE_LENGTH
        )

        print("Real-Time Inference System Ready!")

    def add_reading(
        self,
        pH,
        TDS_ppm,
        Turbidity_NTU,
        Temperature_C
    ):

        reading = [
            float(pH),
            float(TDS_ppm),
            float(Turbidity_NTU),
            float(Temperature_C)
        ]

        self.reading_buffer.append(reading)

        print(
            f"\nNew sensor reading added:"
            f"\npH          : {pH}"
            f"\nTDS         : {TDS_ppm} ppm"
            f"\nTurbidity   : {Turbidity_NTU} NTU"
            f"\nTemperature : {Temperature_C} °C"
        )

        print(
            f"Buffer: "
            f"{len(self.reading_buffer)}/{SEQUENCE_LENGTH}"
        )

    def is_ready(self):

        return len(self.reading_buffer) == SEQUENCE_LENGTH

    def predict(self):

        if not self.is_ready():

            raise ValueError(
                f"Need {SEQUENCE_LENGTH} readings "
                f"before prediction. "
                f"Currently available: "
                f"{len(self.reading_buffer)}"
            )

        readings = np.array(
            self.reading_buffer,
            dtype=np.float32
        )

        processed_sequence = preprocess_sequence(
            readings
        )

        probability = float(
            self.model.predict(
                processed_sequence,
                verbose=0
            )[0][0]
        )

        if probability >= 0.5:

            prediction = "UNSAFE"

        else:

            prediction = "SAFE"

        confidence = probability if prediction == "UNSAFE" else 1 - probability

        result = {
            "prediction": prediction,
            "unsafe_probability": round(
                probability,
                4
            ),
            "confidence": round(
                confidence,
                4
            ),
            "readings_used": len(
                self.reading_buffer
            )
        }

        return result


if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("CLEARWATER REAL-TIME INFERENCE TEST")
    print("=" * 60)

    inference = RealTimeInference()

    test_readings = [

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

    ]

    for reading in test_readings:

        inference.add_reading(
            pH=reading[0],
            TDS_ppm=reading[1],
            Turbidity_NTU=reading[2],
            Temperature_C=reading[3]
        )

    print("\n" + "=" * 60)
    print("RUNNING CNN-LSTM PREDICTION")
    print("=" * 60)

    result = inference.predict()

    print("\nPrediction Result:")
    print(
        f"Prediction         : "
        f"{result['prediction']}"
    )

    print(
        f"Unsafe Probability : "
        f"{result['unsafe_probability']}"
    )

    print(
        f"Confidence         : "
        f"{result['confidence'] * 100:.2f}%"
    )

    print(
        f"Readings Used      : "
        f"{result['readings_used']}"
    )

    print("\n" + "=" * 60)
    print("REAL-TIME INFERENCE TEST PASSED")
    print("=" * 60)