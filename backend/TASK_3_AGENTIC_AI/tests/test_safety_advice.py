from agent.safety_advice import build_safety_advice


def test_low_ph_includes_precautions_remedies_and_follow_up():
    result = build_safety_advice(
        {"available": True, "pH": 5.5, "TDS": 300, "turbidity": 0.5, "temperature": 25},
        {
            "pH": {"status": "Unsafe", "value": 5.5},
            "TDS": {"status": "Safe", "value": 300},
            "turbidity": {"status": "Safe", "value": 0.5},
            "temperature": {"status": "Monitor", "value": 25},
        },
        {"overall_status": "Unsafe"},
    )
    assert result["precautions"]
    assert any("possible causes" in item.lower() for item in result["remedies"])
    assert any("retest ph" in item.lower() for item in result["follow_up"])
    assert "disclaimer" in result
