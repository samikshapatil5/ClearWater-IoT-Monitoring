from tools.knowledge_tool import get_interpretation_rules, get_standards, get_parameter_knowledge
import re


def _condition_matches(condition, value):
    """
    Safely evaluate the numeric comparison formats used in
    knowledge_base/interpretation_rules.json, such as:
      value < 6.5
      6.5 <= value <= 8.5
      500 < value <= 2000
      value > 5
    """
    condition = condition.strip()

    if condition == "all_values":
        return True

    tokens = re.findall(r"value|(?:\d+(?:\.\d+)?)|<=|>=|==|<|>", condition)
    if not tokens:
        raise ValueError(f"Unsupported interpretation condition: {condition}")

    # Convert the condition into a sequence of operands and operators.
    operands = []
    operators = []
    expect_operand = True

    for token in tokens:
        if expect_operand:
            if token == "value":
                operands.append(float(value))
            else:
                operands.append(float(token))
            expect_operand = False
        else:
            if token not in ("<", "<=", ">", ">=", "=="):
                raise ValueError(f"Unsupported operator in condition: {condition}")
            operators.append(token)
            expect_operand = True

    if expect_operand or len(operands) != len(operators) + 1:
        raise ValueError(f"Malformed interpretation condition: {condition}")

    for index, operator in enumerate(operators):
        left = operands[index]
        right = operands[index + 1]

        if operator == "<":
            matched = left < right
        elif operator == "<=":
            matched = left <= right
        elif operator == ">":
            matched = left > right
        elif operator == ">=":
            matched = left >= right
        else:
            matched = left == right

        if not matched:
            return False

    return True


def _analyze_parameter(parameter_name, value, parameter_rules):
    """Return the first matching status and explanation from the JSON rules."""
    for rule in parameter_rules["conditions"]:
        if _condition_matches(rule["condition"], value):
            return {
                "status": rule["status"],
                "meaning": rule["meaning"]
            }

    raise ValueError(
        f"No interpretation rule matched {parameter_name} value {value!r}"
    )


def analyze_water_quality(water_quality, model_prediction):
    """
    Interpret sensor readings using the configured JSON knowledge-base rules
    and include the actual CNN-LSTM model output.
    """
    knowledge = get_interpretation_rules()
    standards = get_standards()
    parameter_knowledge = get_parameter_knowledge()
    rules = knowledge["rules"]
    analysis = {}

    # Apply the rules stored in interpretation_rules.json.
    for parameter in ("pH", "TDS", "turbidity"):
        if parameter not in water_quality:
            raise KeyError(f"Missing sensor parameter: {parameter}")

        value = float(water_quality[parameter])
        if not (value == value and abs(value) != float("inf")):
            raise ValueError(f"{parameter} must be a finite number")
        analysis[parameter] = _analyze_parameter(parameter, value, rules[parameter])
        analysis[parameter]["value"] = value
        analysis[parameter]["unit"] = parameter_knowledge.get("parameters", {}).get(parameter, {}).get("unit")
        analysis[parameter]["description"] = parameter_knowledge.get("parameters", {}).get(parameter, {}).get("description")
        analysis[parameter]["reference_standard"] = standards.get("standard", {}).get("name")
        analysis[parameter]["standard_reference"] = standards.get("parameters", {}).get(parameter, {})

    # Temperature is currently monitoring-only in the knowledge base.
    temperature = float(water_quality["temperature"])
    temperature_result = _analyze_parameter(
        "temperature", temperature, rules["temperature"]
    )
    if not (temperature == temperature and abs(temperature) != float("inf")):
        raise ValueError("temperature must be a finite number")
    temperature_result["value"] = temperature
    temperature_result["unit"] = parameter_knowledge.get("parameters", {}).get("temperature", {}).get("unit")
    temperature_result["description"] = parameter_knowledge.get("parameters", {}).get("temperature", {}).get("description")
    temperature_result["reference_standard"] = standards.get("standard", {}).get("name")
    temperature_result["standard_reference"] = standards.get("parameters", {}).get("temperature", {})
    analysis["temperature"] = temperature_result
    analysis["standard"] = standards.get("standard", {})
    analysis["standards_note"] = standards.get("important_note", "")
    analysis["parameter_knowledge_source"] = "knowledge_base/parameters.json"
    analysis["standards_source"] = "knowledge_base/standards.json"

    # Include the real model result; do not invent a prediction when unavailable.
    prediction = str(
        model_prediction.get("prediction", "Unavailable")
    ).strip().title()

    model_available = (
        model_prediction.get("available", False)
        and prediction in ("Safe", "Unsafe")
    )

    analysis["model_prediction"] = (
        prediction if model_available else "Unavailable"
    )
    analysis["model_available"] = model_available
    analysis["cmi"] = model_prediction.get("cmi")
    analysis["model_reason"] = model_prediction.get("reason")

    # Explain the model result alongside the current parameter checks.
    warnings = [
        name for name in ("pH", "TDS", "turbidity")
        if analysis[name]["status"] in ("Warning", "Unsafe")
    ]
    analysis["parameters_needing_review"] = warnings

    if not model_available:
        explanation = (
            "The CNN-LSTM classification is unavailable. Review the "
            "individual sensor readings, but do not treat them as a "
            "confirmed model result."
        )
    elif prediction == "Unsafe":
        explanation = (
            "The trained CNN-LSTM classified the supplied sensor sequence "
            "as Unsafe. Review the sensor measurements and obtain appropriate "
            "water-quality testing. This classification does not identify "
            "a specific contaminant."
        )
    elif warnings:
        explanation = (
            "The CNN-LSTM classified the supplied sequence as Safe, but one "
            "or more current sensor parameters need review. The model result "
            "and the parameter checks differ; investigate before drawing "
            "conclusions about water quality."
        )
    else:
        explanation = (
            "The CNN-LSTM classified the supplied sequence as Safe, and the "
            "checked pH, TDS and turbidity readings are within their selected "
            "acceptable limits. These measurements alone do not confirm that "
            "the water is safe to drink."
        )

    analysis["explanation"] = explanation
    analysis["interpretation_note"] = knowledge.get(
        "overall_interpretation", {}
    ).get(
        "important_note",
        "This analysis covers only the parameters monitored by this project."
    )

    return analysis


if __name__ == "__main__":
    sample_water_quality = {
        "pH": 7.2,
        "TDS": 420,
        "turbidity": 0.8,
        "temperature": 27.0
    }

    # This is sample data for a local test only.
    # The live application should pass the result from model_tool.py.
    sample_prediction = {
        "prediction": "Safe",
        "available": True,
        "cmi": None
    }

    result = analyze_water_quality(sample_water_quality, sample_prediction)

    print("Water Quality Analysis:")
    print(result)
    print("\nExplanation for the user:")
    print(result["explanation"])
