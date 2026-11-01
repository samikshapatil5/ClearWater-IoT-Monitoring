"""Combine parameter statuses, CNN-LSTM prediction, and the project CMI/WQI."""
from tools.knowledge_tool import get_interpretation_rules


# The DL service's `wqi` value is a project-specific ClearWater Monitoring
# Index (CMI), inspired by CCME WQI. These mappings are project decision
# policy, not an official regulatory classification.
WQI_CATEGORY_POLICY = {
    "POOR": "Unsafe",
    "MARGINAL": "Warning",
    "FAIR": "Warning",
    "GOOD": "Supportive",
    "EXCELLENT": "Supportive",
}


def _normalize_wqi(cmi):
    """Extract score/category from the CMI object returned by the DL API."""
    if not isinstance(cmi, dict):
        return None, None, "Unavailable"
    score = cmi.get("wqi", cmi.get("score"))
    category = str(cmi.get("category", "")).strip().upper()
    try:
        score = float(score) if score is not None else None
    except (TypeError, ValueError):
        score = None
    if score is not None and not 0 <= score <= 100:
        score = None
    status = WQI_CATEGORY_POLICY.get(category, "Unavailable")
    if score is None or not category:
        return score, category or None, "Unavailable"
    return score, category, status


def make_decision(analysis, cmi=None):
    """Combine parameter rules, CNN-LSTM output, and CMI/WQI category.

    Unsafe parameter/model results cannot be overridden by a good index score.
    A POOR index contributes an Unsafe decision; FAIR/MARGINAL contributes
    Warning. A final Safe status requires an available model and an available
    GOOD/EXCELLENT index category.
    """
    knowledge = get_interpretation_rules()
    policy = knowledge.get("decision_policy")
    if not isinstance(policy, dict):
        raise ValueError("Missing decision_policy in interpretation_rules.json")

    parameters = ("pH", "TDS", "turbidity")
    statuses = []
    for parameter in parameters:
        if parameter not in analysis or "status" not in analysis[parameter]:
            raise ValueError(f"Missing status for parameter: {parameter}")
        statuses.append(str(analysis[parameter]["status"]))

    model_prediction = str(analysis.get("model_prediction", "Unavailable")).title()
    unsafe_parameter_statuses = policy.get("unsafe_parameter_statuses", ["Unsafe"])
    warning_parameter_statuses = policy.get("warning_parameter_statuses", ["Warning"])
    unsafe_model_predictions = policy.get("unsafe_model_predictions", ["Unsafe"])
    unavailable_predictions = policy.get("unavailable_model_predictions", ["Unavailable"])

    wqi_score, wqi_category, wqi_status = _normalize_wqi(cmi)
    unsafe_wqi = wqi_status == "Unsafe"
    warning_wqi = wqi_status == "Warning"

    # Conservative precedence: unsafe evidence first, then missing required
    # model/index evidence, then warning, then Safe.
    if (any(status in unsafe_parameter_statuses for status in statuses)
            or model_prediction in unsafe_model_predictions or unsafe_wqi):
        overall_status = "Unsafe"
    elif model_prediction in unavailable_predictions:
        overall_status = "Insufficient data"
    elif wqi_status == "Unavailable":
        overall_status = "Insufficient data"
    elif any(status in warning_parameter_statuses for status in statuses) or warning_wqi:
        overall_status = "Warning"
    elif model_prediction == "Safe" and wqi_status == "Supportive":
        overall_status = "Safe"
    else:
        overall_status = "Insufficient data"

    parameter_statuses = {
        name: analysis.get(name, {}).get("status", "Unavailable")
        for name in (*parameters, "temperature")
    }
    return {
        "overall_status": overall_status,
        "model_prediction": model_prediction,
        "parameter_statuses": parameter_statuses,
        "wqi_score": wqi_score,
        "wqi_category": wqi_category,
        "wqi_status_contribution": wqi_status,
        "decision_considerations": {
            "parameter_statuses": parameter_statuses,
            "cnn_lstm_prediction": model_prediction,
            "wqi_score": wqi_score,
            "wqi_category": wqi_category,
            "wqi_policy_effect": wqi_status,
        },
        "decision_policy_source": "knowledge_base/interpretation_rules.json + project CMI/WQI category policy",
    }
