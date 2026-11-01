"""Lightweight checks that each knowledge JSON is reachable from live code."""
from tools.knowledge_tool import (
    get_parameter_knowledge, get_standards, get_interpretation_rules,
    get_recommendations, get_model_knowledge, get_faq,
)
from agent.reasoning import analyze_water_quality
from agent.decision import make_decision
from agent.recommendation import get_recommendation


def test_all_six_knowledge_files_load():
    assert "parameters" in get_parameter_knowledge()
    assert "standard" in get_standards()
    assert "rules" in get_interpretation_rules()
    assert "decision_policy" in get_interpretation_rules()
    assert "recommendations" in get_recommendations()
    assert "selection" in get_recommendations()
    assert "model" in get_model_knowledge()
    assert "faqs" in get_faq()


def test_runtime_analysis_uses_parameter_and_standard_metadata():
    reading = {"pH": 7.2, "TDS": 400, "turbidity": 0.8, "temperature": 25.0}
    unavailable = {"prediction": "Unavailable", "available": False, "reason": "test", "cmi": None}
    analysis = analyze_water_quality(reading, unavailable)
    assert analysis["pH"]["description"]
    assert analysis["pH"]["reference_standard"] == get_standards()["standard"]["name"]
    assert analysis["standards_source"] == "knowledge_base/standards.json"
    decision = make_decision(analysis)
    assert decision["overall_status"] == "Insufficient data"
    advice = get_recommendation(analysis, decision)
    assert advice
    assert any("CNN-LSTM" in item or "model" in item.lower() for item in advice)
