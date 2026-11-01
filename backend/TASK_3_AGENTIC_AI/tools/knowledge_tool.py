"""Load ClearWater knowledge-base JSON files safely and consistently."""

import json
import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

# TASK_3_AGENTIC_AI/knowledge_base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "knowledge_base")


@lru_cache(maxsize=32)
def _load_json_cached(filename, modified_time_ns, file_size):
    """Read and parse JSON; cache is invalidated when file metadata changes."""
    file_path = os.path.join(KNOWLEDGE_BASE_DIR, filename)
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_json(filename):
    """Load a JSON file from the knowledge_base folder.

    Files are reloaded automatically after their modification time or size changes.
    """
    file_path = os.path.join(KNOWLEDGE_BASE_DIR, filename)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Knowledge-base file not found: {file_path}")

    stat = os.stat(file_path)
    try:
        return _load_json_cached(filename, stat.st_mtime_ns, stat.st_size)
    except json.JSONDecodeError as exc:
        logger.exception("Invalid JSON in knowledge-base file %s", file_path)
        raise ValueError(f"Invalid JSON in knowledge-base file: {filename}") from exc


def get_parameter_knowledge():
    """Return knowledge about pH, TDS, turbidity, and temperature."""
    return load_json("parameters.json")


def get_standards():
    """Return configured water-quality reference standards."""
    return load_json("standards.json")


def get_interpretation_rules():
    """Return water-quality interpretation rules."""
    return load_json("interpretation_rules.json")


def get_recommendations():
    """Return configured recommendations for water-quality conditions."""
    return load_json("recommendations.json")


def get_model_knowledge():
    """Return information about the CNN-LSTM model."""
    return load_json("model_knowledge.json")


def get_faq():
    """Return frequently asked questions and answers."""
    return load_json("faq.json")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing ClearWater knowledge base...")
    print("Knowledge-base directory:", KNOWLEDGE_BASE_DIR)

    for getter, label in (
        (get_parameter_knowledge, "Parameter knowledge"),
        (get_standards, "Water-quality standards"),
        (get_interpretation_rules, "Interpretation rules"),
        (get_recommendations, "Recommendations"),
        (get_model_knowledge, "CNN-LSTM model knowledge"),
        (get_faq, "FAQ"),
    ):
        try:
            data = getter()
            print(f"\n{label}: loaded successfully ({type(data).__name__})")
        except (OSError, ValueError) as exc:
            print(f"\n{label}: FAILED - {exc}")
            raise
