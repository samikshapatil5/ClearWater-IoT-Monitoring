import math
from collections.abc import Mapping


# ============================================================
# CLEARWATER MONITORING INDEX (CMI)
# CCME-INSPIRED ADAPTATION
#
# Purpose:
#   Monitor variations in water quality over a sequence of
#   sensor readings.
#
# Parameters assessed:
#   1. pH
#   2. TDS
#   3. Turbidity
#
# Temperature:
#   Validated and reported separately; excluded from the index
#   until a suitable monitoring objective is established.
#
# IMPORTANT:
#   This is a project-specific adaptation inspired by the
#   CCME WQI framework. It is NOT the official CCME WQI.
#
#   The selected objectives are initial prototype benchmarks.
#   They must be reviewed for the intended water source and
#   monitoring application.
# ============================================================


# ============================================================
# 1. MONITORING OBJECTIVES
# ============================================================

# Initial reference objectives for the prototype.
#
# pH is assessed against both a lower and an upper objective.
# TDS and turbidity are assessed against upper objectives.
#
# These values are not universal objectives for every type
# of water. Document and justify them for your application.

PH_MIN = 6.5
PH_MAX = 8.5

TDS_MAX_PPM = 500.0

TURBIDITY_MAX_NTU = 1.0

PARAMETERS = (
    "pH",
    "TDS_ppm",
    "Turbidity_NTU",
)


# ============================================================
# 2. CATEGORY CLASSIFICATION
# ============================================================

def classify_cmi(score):
    """
    Classify the ClearWater Monitoring Index.

    These are CCME-style descriptive categories.

    Because CMI is a three-parameter adaptation, these
    categories must not be interpreted as a validation or
    certification of the official CCME WQI.
    """

    if score >= 95:
        return "EXCELLENT"

    elif score >= 80:
        return "GOOD"

    elif score >= 65:
        return "FAIR"

    elif score >= 45:
        return "MARGINAL"

    return "POOR"


# ============================================================
# 3. INPUT VALIDATION
# ============================================================

def validate_input(value, name):
    """Convert an input to a finite floating-point number."""

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

    if not math.isfinite(value):
        raise ValueError(
            f"{name} must be finite."
        )

    return value


def validate_reading(reading, index):
    """
    Validate and normalize one sensor reading.

    Supported formats:

    Dictionary:
        {
            "pH": 7.0,
            "TDS_ppm": 300,
            "Turbidity_NTU": 0.8,
            "Temperature_C": 25
        }

    Sequence:
        [pH, TDS_ppm, Turbidity_NTU, Temperature_C]

    Temperature is optional for the index calculation.
    """

    if isinstance(reading, Mapping):

        missing = [
            key
            for key in PARAMETERS
            if key not in reading
        ]

        if missing:
            raise ValueError(
                f"Reading {index}: missing parameters {missing}."
            )

        ph = reading["pH"]
        tds = reading["TDS_ppm"]
        turbidity = reading["Turbidity_NTU"]
        temperature = reading.get("Temperature_C")

    else:

        if isinstance(reading, (str, bytes)):
            raise ValueError(
                f"Reading {index} must be a dictionary "
                "or a sequence of sensor values."
            )

        try:
            values = list(reading)

        except TypeError:
            raise ValueError(
                f"Reading {index} must be a dictionary "
                "or a sequence of sensor values."
            ) from None

        if len(values) not in (3, 4):
            raise ValueError(
                f"Reading {index} must contain 3 or 4 values "
                "in this order: pH, TDS_ppm, "
                "Turbidity_NTU, Temperature_C."
            )

        ph = values[0]
        tds = values[1]
        turbidity = values[2]

        temperature = (
            values[3]
            if len(values) == 4
            else None
        )

    # Validate numerical values.

    ph = validate_input(ph, f"Reading {index}: pH")

    tds = validate_input(
        tds,
        f"Reading {index}: TDS_ppm"
    )

    turbidity = validate_input(
        turbidity,
        f"Reading {index}: Turbidity_NTU"
    )

    if temperature is not None:

        temperature = validate_input(
            temperature,
            f"Reading {index}: Temperature_C"
        )

    # Validate pH.

    if not 0 < ph <= 14:
        raise ValueError(
            f"Reading {index}: pH must be greater than 0 "
            "and at most 14."
        )

    # Validate TDS.

    if tds < 0:
        raise ValueError(
            f"Reading {index}: TDS cannot be negative."
        )

    # Validate turbidity.

    if turbidity < 0:
        raise ValueError(
            f"Reading {index}: turbidity cannot be negative."
        )

    return {
        "pH": ph,
        "TDS_ppm": tds,
        "Turbidity_NTU": turbidity,
        "Temperature_C": temperature,
    }


# ============================================================
# 4. CHECK EACH PARAMETER AGAINST ITS OBJECTIVE
# ============================================================

def evaluate_parameter(name, value):
    """
    Compare a parameter measurement with its selected objective.

    Returns:
        failed: whether the objective was not met
        excursion: magnitude of deviation if it failed
        objective: descriptive objective
    """

    # --------------------------------------------------------
    # pH: lower and upper objectives
    # --------------------------------------------------------

    if name == "pH":

        objective = (
            f"{PH_MIN} <= pH <= {PH_MAX}"
        )

        if value < PH_MIN:

            # Lower-bound failure.
            excursion = (
                PH_MIN / value
            ) - 1.0

            return {
                "failed": True,
                "excursion": excursion,
                "objective": objective,
            }

        if value > PH_MAX:

            # Upper-bound failure.
            excursion = (
                value / PH_MAX
            ) - 1.0

            return {
                "failed": True,
                "excursion": excursion,
                "objective": objective,
            }

        return {
            "failed": False,
            "excursion": 0.0,
            "objective": objective,
        }

    # --------------------------------------------------------
    # TDS: upper objective
    # --------------------------------------------------------

    if name == "TDS_ppm":

        objective = (
            f"TDS <= {TDS_MAX_PPM} ppm"
        )

        if value > TDS_MAX_PPM:

            excursion = (
                value / TDS_MAX_PPM
            ) - 1.0

            return {
                "failed": True,
                "excursion": excursion,
                "objective": objective,
            }

        return {
            "failed": False,
            "excursion": 0.0,
            "objective": objective,
        }

    # --------------------------------------------------------
    # Turbidity: upper objective
    # --------------------------------------------------------

    if name == "Turbidity_NTU":

        objective = (
            f"Turbidity <= {TURBIDITY_MAX_NTU} NTU"
        )

        if value > TURBIDITY_MAX_NTU:

            excursion = (
                value / TURBIDITY_MAX_NTU
            ) - 1.0

            return {
                "failed": True,
                "excursion": excursion,
                "objective": objective,
            }

        return {
            "failed": False,
            "excursion": 0.0,
            "objective": objective,
        }

    raise ValueError(
        f"Unsupported parameter: {name}"
    )


# ============================================================
# 5. CALCULATE THE CLEARWATER MONITORING INDEX
# ============================================================

def calculate_cmi(readings):
    """
    Calculate the ClearWater Monitoring Index from multiple
    sensor readings.

    Args:
        readings:
            An iterable of sensor-reading dictionaries or
            sequences.

            Sequence order:
                pH, TDS_ppm, Turbidity_NTU, Temperature_C

    Returns:
        A dictionary containing:
            - wqi: index score, 0 to 100
            - category: descriptive index category
            - factors: F1, F2, F3
            - parameter_status: per-parameter objective checks
            - readings_used: number of readings processed
            - temperature_C: most recent temperature, if present

    The score summarizes compliance with the selected
    objectives. It does not certify drinking-water safety.
    """

    if readings is None:
        raise ValueError(
            "Readings cannot be None."
        )

    # --------------------------------------------------------
    # Normalize and validate all readings
    # --------------------------------------------------------

    try:
        raw_readings = list(readings)

    except TypeError:
        raise ValueError(
            "Readings must be an iterable of sensor readings."
        ) from None

    if not raw_readings:
        raise ValueError(
            "At least one sensor reading is required."
        )

    normalized_readings = [
        validate_reading(reading, index + 1)
        for index, reading in enumerate(raw_readings)
    ]

    number_of_readings = len(normalized_readings)
    number_of_parameters = len(PARAMETERS)

    # Each parameter measurement is one test.
    total_tests = (
        number_of_readings * number_of_parameters
    )

    # --------------------------------------------------------
    # Evaluate all parameter measurements
    # --------------------------------------------------------

    failed_parameters = set()

    failed_tests = 0
    excursion_sum = 0.0

    parameter_results = {
        name: {
            "objective": None,
            "tests": number_of_readings,
            "failed_tests": 0,
            "status": "WITHIN OBJECTIVE",
        }
        for name in PARAMETERS
    }

    for reading in normalized_readings:

        for name in PARAMETERS:

            value = reading[name]

            assessment = evaluate_parameter(
                name,
                value
            )

            parameter_results[name]["objective"] = (
                assessment["objective"]
            )

            if assessment["failed"]:

                failed_tests += 1

                failed_parameters.add(name)

                excursion_sum += assessment["excursion"]

                parameter_results[name]["failed_tests"] += 1

                parameter_results[name]["status"] = (
                    "OBJECTIVE NOT MET"
                )

    # --------------------------------------------------------
    # F1: SCOPE
    #
    # Percentage of distinct parameters that failed at least
    # once during the monitoring period.
    # --------------------------------------------------------

    F1 = (
        len(failed_parameters)
        / number_of_parameters
    ) * 100.0

    # --------------------------------------------------------
    # F2: FREQUENCY
    #
    # Percentage of all individual tests that failed.
    # --------------------------------------------------------

    F2 = (
        failed_tests
        / total_tests
    ) * 100.0

    # --------------------------------------------------------
    # F3: AMPLITUDE
    #
    # Step 1: Normalized sum of excursions.
    # --------------------------------------------------------

    NSE = (
        excursion_sum
        / total_tests
    )

    # --------------------------------------------------------
    # Step 2: Scale amplitude to a range approaching 0 to 100.
    # --------------------------------------------------------

    if NSE == 0:

        F3 = 0.0

    else:

        F3 = (
            NSE
            / (0.01 * NSE + 0.01)
        )

    # --------------------------------------------------------
    # Final index
    #
    # CMI = 100 - sqrt(F1² + F2² + F3²) / sqrt(3)
    # --------------------------------------------------------

    score = (
        100.0
        - math.sqrt(
            F1 ** 2
            + F2 ** 2
            + F3 ** 2
        ) / math.sqrt(3.0)
    )

    # Keep the score within the required range.
    score = max(
        0.0,
        min(100.0, score)
    )

    category = classify_cmi(score)

    # --------------------------------------------------------
    # Construct result
    # --------------------------------------------------------

    latest_temperature = (
        normalized_readings[-1]["Temperature_C"]
    )

    if latest_temperature is not None:

        latest_temperature = round(
            latest_temperature,
            2
        )

    # Round the score only after classification has used
    # the unrounded score.

    return {
        "index_name": "ClearWater Monitoring Index",
        "method": "CCME-inspired three-parameter adaptation",

        "wqi": round(score, 2),
        "category": category,

        "factors": {
            "scope_F1": round(F1, 2),
            "frequency_F2": round(F2, 2),
            "amplitude_F3": round(F3, 2),
            "normalized_sum_of_excursions": round(NSE, 6),
        },

        "parameter_status": parameter_results,

        "parameters_assessed": list(PARAMETERS),

        "readings_used": number_of_readings,

        "temperature_C": latest_temperature,

        "interpretation": (
            "Higher scores indicate closer compliance with "
            "the selected monitoring objectives. This "
            "project-specific index does not establish "
            "overall water safety."
        ),
    }


# ============================================================
# 6. BACKWARD-COMPATIBLE FUNCTION
# ============================================================

def calculate_wqi(
    pH,
    TDS_ppm,
    Turbidity_NTU,
    Temperature_C=None
):
    """
    Backward-compatible wrapper for the existing application.

    IMPORTANT:
        This function evaluates ONE reading.

        For a monitoring-window index, use calculate_cmi()
        with the complete sequence of sensor readings.
    """

    single_reading = {
        "pH": pH,
        "TDS_ppm": TDS_ppm,
        "Turbidity_NTU": Turbidity_NTU,
        "Temperature_C": Temperature_C,
    }

    return calculate_cmi([single_reading])


# ============================================================
# 7. TESTS
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 65)
    print("CLEARWATER MONITORING INDEX TEST")
    print("=" * 65)

    # --------------------------------------------------------
    # TEST 1: All readings meet the selected objectives.
    # --------------------------------------------------------

    reference_readings = [
        {
            "pH": 7.0,
            "TDS_ppm": 300,
            "Turbidity_NTU": 0.8,
            "Temperature_C": 25.0,
        }
        for _ in range(10)
    ]

    result_reference = calculate_cmi(
        reference_readings
    )

    print("\nTEST 1: All measurements within objectives")

    print(
        "CMI:",
        result_reference["wqi"]
    )

    print(
        "Category:",
        result_reference["category"]
    )

    assert result_reference["wqi"] == 100.0
    assert result_reference["category"] == "EXCELLENT"

    print("Result: PASSED")

    # --------------------------------------------------------
    # TEST 2: Turbidity exceeds the objective repeatedly.
    # --------------------------------------------------------

    monitoring_readings = [
        {
            "pH": 7.0,
            "TDS_ppm": 300,
            "Turbidity_NTU": 0.8,
            "Temperature_C": 25.0,
        },
        {
            "pH": 7.1,
            "TDS_ppm": 310,
            "Turbidity_NTU": 1.2,
            "Temperature_C": 25.1,
        },
        {
            "pH": 7.0,
            "TDS_ppm": 320,
            "Turbidity_NTU": 1.4,
            "Temperature_C": 25.2,
        },
        {
            "pH": 7.2,
            "TDS_ppm": 330,
            "Turbidity_NTU": 1.1,
            "Temperature_C": 25.0,
        },
        {
            "pH": 7.1,
            "TDS_ppm": 340,
            "Turbidity_NTU": 1.6,
            "Temperature_C": 25.3,
        },
        {
            "pH": 7.0,
            "TDS_ppm": 350,
            "Turbidity_NTU": 0.9,
            "Temperature_C": 25.1,
        },
        {
            "pH": 7.2,
            "TDS_ppm": 360,
            "Turbidity_NTU": 1.8,
            "Temperature_C": 25.4,
        },
        {
            "pH": 7.1,
            "TDS_ppm": 370,
            "Turbidity_NTU": 0.8,
            "Temperature_C": 25.2,
        },
        {
            "pH": 7.0,
            "TDS_ppm": 380,
            "Turbidity_NTU": 1.5,
            "Temperature_C": 25.3,
        },
        {
            "pH": 7.2,
            "TDS_ppm": 390,
            "Turbidity_NTU": 2.1,
            "Temperature_C": 25.4,
        },
    ]

    result_monitoring = calculate_cmi(
        monitoring_readings
    )

    print("\nTEST 2: Monitoring-window calculation")

    print(
        "CMI:",
        result_monitoring["wqi"]
    )

    print(
        "Category:",
        result_monitoring["category"]
    )

    print(
        "Readings used:",
        result_monitoring["readings_used"]
    )

    print("\nCalculation factors:")

    for name, value in result_monitoring["factors"].items():
        print(f"{name}: {value}")

    print("\nParameter assessment:")

    for name, details in result_monitoring["parameter_status"].items():

        print(
            f"{name}: "
            f"{details['status']} | "
            f"Failed tests: {details['failed_tests']}/"
            f"{details['tests']}"
        )

    assert result_monitoring["readings_used"] == 10
    assert result_monitoring["wqi"] < 100.0

    print("Result: PASSED")

    # --------------------------------------------------------
    # TEST 3: Invalid pH must be rejected.
    # --------------------------------------------------------

    print("\nTEST 3: Invalid pH validation")

    try:

        calculate_cmi([
            {
                "pH": 0,
                "TDS_ppm": 300,
                "Turbidity_NTU": 0.8,
                "Temperature_C": 25.0,
            }
        ])

        raise AssertionError(
            "Invalid pH was not rejected."
        )

    except ValueError as error:

        print("Invalid input rejected:", error)

    # --------------------------------------------------------
    # TEST 4: Empty input must be rejected.
    # --------------------------------------------------------

    print("\nTEST 4: Empty input validation")

    try:

        calculate_cmi([])

        raise AssertionError(
            "Empty readings were not rejected."
        )

    except ValueError as error:

        print("Empty input rejected:", error)

    print("\n" + "=" * 65)
    print("ALL CMI TESTS PASSED")
    print("=" * 65)