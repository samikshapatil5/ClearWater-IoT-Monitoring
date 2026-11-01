"""Orchestrate live water-quality assessment for the ClearWater Agentic AI service.

The agent uses real sensor readings and history from the configured storage backend.
It does not invent fallback sensor values when live readings are unavailable.
"""

import logging
import time
from typing import Any

from tools.water_quality_tool import get_current_water_quality
from tools.history_tool import get_water_quality_history, get_storage_backend
from tools.model_tool import get_model_prediction
from agent.reasoning import analyze_water_quality
from agent.decision import make_decision
from agent.recommendation import get_recommendation
from agent.safety_advice import build_safety_advice

logger = logging.getLogger(__name__)


def _unavailable_result(water_quality: dict[str, Any], history_count: int) -> dict[str, Any]:
    """Return a consistent result when there are no valid sensor readings."""
    decision = {
        "overall_status": "Insufficient data",
        "model_prediction": "Unavailable",
        "parameter_statuses": {},
        "wqi_score": None,
        "wqi_category": None,
        "wqi_status_contribution": "Unavailable",
    }
    model_prediction = {
        "prediction": "Unavailable",
        "available": False,
        "reason": "No valid actual sensor readings are available from Firebase or the configured data source.",
        "readings_used": 0,
        "cmi": None,
    }

    return {
        "water_quality": water_quality,
        "model_prediction": model_prediction,
        "cmi": None,
        "analysis": {},
        "decision": decision,
        "recommendation": [
            "Check the configured data source and ensure valid ESP32 sensor readings are being recorded."
        ],
        "safety_advice": build_safety_advice(water_quality, {}, decision),
        "history_count": history_count,
        "data_source": _get_data_source(),
    }


def _get_data_source() -> str:
    """Identify the configured storage backend without failing the whole response."""
    try:
        backend = get_storage_backend()
        return "firebase" if str(backend).strip().lower() == "firebase" else "local_json_development"
    except Exception:
        logger.exception("Could not determine the configured storage backend")
        return "unknown"


def run_agent() -> dict[str, Any]:
    """Assess current water quality using actual readings, history, and the ML model.

    Missing readings are reported as unavailable; they are never replaced with dummy data.
    """
    started = time.perf_counter()

    try:
        water_quality = get_current_water_quality()
        if not isinstance(water_quality, dict):
            logger.error(
                "get_current_water_quality returned %s instead of a dictionary",
                type(water_quality).__name__,
            )
            water_quality = {
                "available": False,
                "reason": "The current water-quality tool returned an invalid response.",
            }

        history = get_water_quality_history()
        if not isinstance(history, list):
            logger.warning(
                "get_water_quality_history returned %s instead of a list; using empty history",
                type(history).__name__,
            )
            history = []

        if not water_quality.get("available"):
            result = _unavailable_result(water_quality, len(history))
            logger.info(
                "Agent assessment completed without current readings in %.3f seconds",
                time.perf_counter() - started,
            )
            return result

        model_started = time.perf_counter()
        model_prediction = get_model_prediction(water_quality, history)
        logger.info(
            "Model prediction completed in %.3f seconds",
            time.perf_counter() - model_started,
        )
        if not isinstance(model_prediction, dict):
            logger.error(
                "get_model_prediction returned %s instead of a dictionary",
                type(model_prediction).__name__,
            )
            model_prediction = {
                "prediction": "Unavailable",
                "available": False,
                "reason": "The prediction tool returned an invalid response.",
                "readings_used": 0,
                "cmi": None,
            }

        analysis = analyze_water_quality(water_quality, model_prediction)
        if not isinstance(analysis, dict):
            logger.warning("Water-quality analysis returned an invalid response; using empty analysis")
            analysis = {}

        # decision.py expects the complete WQI/CMI object (score and category).
        cmi = model_prediction.get("cmi")
        decision = make_decision(analysis, cmi)
        if not isinstance(decision, dict):
            logger.error("make_decision returned an invalid response")
            decision = {
                "overall_status": "Insufficient data",
                "model_prediction": model_prediction.get("prediction", "Unavailable"),
                "parameter_statuses": {},
                "wqi_score": None,
                "wqi_category": None,
                "wqi_status_contribution": "Unavailable",
            }

        recommendation = get_recommendation(analysis, decision)
        safety_advice = build_safety_advice(water_quality, analysis, decision)

        result = {
            "water_quality": water_quality,
            "model_prediction": model_prediction,
            "cmi": cmi,
            "analysis": analysis,
            "decision": decision,
            "recommendation": recommendation,
            "safety_advice": safety_advice,
            "history_count": len(history),
            "data_source": _get_data_source(),
        }
        logger.info(
            "Agent assessment completed in %.3f seconds (history_count=%d, data_source=%s)",
            time.perf_counter() - started,
            len(history),
            result["data_source"],
        )
        return result

    except Exception:
        logger.exception("Water-quality agent assessment failed after %.3f seconds", time.perf_counter() - started)
        raise


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    print(json.dumps(run_agent(), indent=2, default=str))
