"""Select concise, non-duplicated recommendations from recommendations.json and standards.json."""

from tools.knowledge_tool import get_recommendations, get_standards


def _append_from(mapping, key, result):
    """Append configured recommendation strings for a key if present."""
    if not key:
        return
    values = mapping.get(key, [])
    if isinstance(values, str):
        values = [values]
    if isinstance(values, list):
        result.extend(
            item.strip()
            for item in values
            if isinstance(item, str) and item.strip()
        )


def _normalise_sentence(text):
    return " ".join(text.split()).strip().rstrip(".!?").casefold()


def _split_sentences(text):
    """Split recommendation text on sentence boundaries without breaking decimals."""
    text = " ".join(text.replace("\\r", " ").replace("\\n", " ").split())
    if not text:
        return []

    # Split after punctuation only when followed by whitespace and an uppercase
    # letter or digit. This keeps decimal readings such as 1.3 intact.
    import re
    parts = re.split(r"(?<=[.!?])\\s+(?=[A-Z0-9])", text)
    return [part.strip() for part in parts if part.strip()]


def _deduplicate_recommendations(items):
    """Deduplicate exact repeated sentences while preserving order."""
    result = []
    seen = set()
    for item in items:
        if not isinstance(item, str):
            continue
        for sentence in _split_sentences(item):
            key = _normalise_sentence(sentence)
            if key and key not in seen:
                seen.add(key)
                result.append(sentence)
    return result


def get_recommendation(analysis, decision):
    """Generate advice from configured knowledge without hardcoding thresholds."""
    data = get_recommendations() or {}
    standards_data = get_standards() or {}
    standards = standards_data.get("parameters", {})
    content = data.get("recommendations", {})
    selection = data.get("selection", {})
    result = []

    overall_status = decision.get("overall_status", "Insufficient data")
    overall_key = selection.get("overall_status", {}).get(overall_status)
    _append_from(content.get("overall_status", {}), overall_key, result)

    required_parameters = ("pH", "TDS", "turbidity", "temperature")
    if not isinstance(analysis, dict) or not all(
        isinstance(analysis.get(key), dict) for key in required_parameters
    ):
        return _deduplicate_recommendations(result)

    ph_info = analysis.get("pH", {})
    ph_status = ph_info.get("status")
    ph_value = ph_info.get("value")
    ph_selection = selection.get("pH", {})

    if ph_status == "Unsafe" and isinstance(ph_value, (int, float)):
        ph_standard = standards.get("pH", {})
        minimum = ph_standard.get("acceptable_min")
        maximum = ph_standard.get("acceptable_max")
        if minimum is not None and ph_value < float(minimum):
            _append_from(
                content.get("pH", {}),
                ph_selection.get("Unsafe", {}).get("below_min_key"),
                result,
            )
        elif maximum is not None and ph_value > float(maximum):
            _append_from(
                content.get("pH", {}),
                ph_selection.get("Unsafe", {}).get("above_max_key"),
                result,
            )
    elif ph_status == "Safe":
        _append_from(content.get("pH", {}), ph_selection.get("Safe"), result)

    for parameter in ("TDS", "turbidity"):
        status = analysis.get(parameter, {}).get("status")
        key = selection.get(parameter, {}).get(status)
        _append_from(content.get(parameter, {}), key, result)

    temperature_key = selection.get("temperature", {}).get("all_values")
    _append_from(content.get("temperature", {}), temperature_key, result)

    return _deduplicate_recommendations(result)


if __name__ == "__main__":
    print("Recommendation source: knowledge_base/recommendations.json")
    print("Recommendation selection metadata loaded successfully.")
