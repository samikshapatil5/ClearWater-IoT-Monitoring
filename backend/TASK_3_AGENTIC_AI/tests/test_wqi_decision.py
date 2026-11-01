from agent.decision import make_decision


def base_analysis(prediction="Safe", ph_status="Safe", tds_status="Safe", turbidity_status="Safe"):
    return {
        "pH": {"status": ph_status},
        "TDS": {"status": tds_status},
        "turbidity": {"status": turbidity_status},
        "temperature": {"status": "Monitor"},
        "model_prediction": prediction,
    }


def test_poor_wqi_makes_overall_unsafe_even_if_model_safe():
    result = make_decision(base_analysis(), {"wqi": 40, "category": "POOR"})
    assert result["overall_status"] == "Unsafe"
    assert result["wqi_score"] == 40
    assert result["wqi_category"] == "POOR"


def test_fair_wqi_causes_warning():
    result = make_decision(base_analysis(), {"wqi": 70, "category": "FAIR"})
    assert result["overall_status"] == "Warning"
    assert result["wqi_status_contribution"] == "Warning"


def test_good_wqi_does_not_override_unsafe_parameter():
    result = make_decision(base_analysis(ph_status="Unsafe"), {"wqi": 96, "category": "EXCELLENT"})
    assert result["overall_status"] == "Unsafe"


def test_missing_wqi_does_not_claim_safe():
    result = make_decision(base_analysis(), None)
    assert result["overall_status"] == "Insufficient data"
