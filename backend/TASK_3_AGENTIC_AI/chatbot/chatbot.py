"""ClearWater Agentic AI chatbot.



The deterministic Python agent owns sensor interpretation, model outputs,

decisions, and approved recommendations. Gemini is the conversational layer

that explains those results and answers general water-quality questions.

"""

from agent.agent import run_agent

import json

import os

import logging

from dotenv import load_dotenv

from tools.knowledge_tool import get_faq, get_parameter_knowledge, get_standards, get_model_knowledge

from feedback.feedback import submit_feedback

logger = logging.getLogger(__name__)

# Load TASK_3_AGENTIC_AI/.env reliably, independent of the terminal's working directory.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)

def normalize_text(text):

    """

    Converts text to lowercase and removes punctuation.

    """

    return " ".join(

        word.strip("?,.!")

        for word in text.lower().split()

    )

def find_faq_answer(user_question, faq_data):

    """

    Finds the most relevant answer from the FAQ knowledge base.

    """

    question = normalize_text(user_question)

    # Exact FAQ match

    for faq in faq_data["faqs"]:

        faq_question = normalize_text(faq["question"])

        if question == faq_question:

            return faq["answer"]

    # Keyword matching

    stop_words = {

        "what", "is", "the", "a", "an", "does",

        "do", "can", "why", "how", "my", "your",

        "me", "to", "of", "and", "be", "that",

        "this", "system"

    }

    question_words = {

        word

        for word in question.split()

        if len(word) > 2 and word not in stop_words

    }

    best_answer = None

    best_score = 0

    for faq in faq_data["faqs"]:

        faq_question = normalize_text(faq["question"])

        faq_words = {

            word

            for word in faq_question.split()

            if len(word) > 2 and word not in stop_words

        }

        matched_words = question_words.intersection(faq_words)

        score = len(matched_words)

        if score > best_score:

            best_score = score

            best_answer = faq["answer"]

    if best_score >= 1:

        return best_answer

    return None

def _parameter_key_matches(question, key):

    """Return whether a normalized question mentions a monitored parameter."""

    aliases = {

        "pH": ("ph", "acidity", "alkalinity"),

        "TDS": ("tds", "total dissolved solids", "dissolved solids"),

        "turbidity": ("turbidity", "cloudiness", "cloudy water"),

        "temperature": ("temperature", "water temperature"),

    }

    return any(alias in question for alias in aliases.get(key, (key.lower(),)))

def _educational_parameter_fallback(user_question, question, parameter_data):

    """Provide a complete non-LLM fallback for common parameter questions."""

    keys = [key for key in ("pH", "TDS", "turbidity", "temperature")

            if _parameter_key_matches(question, key)]

    if not keys:

        return None

    # Avoid intercepting current-reading/status questions, which have dedicated handlers.

    detail_terms = ("cause", "causes", "precaution", "precautions", "remedy", "remedies",

                    "treat", "treatment", "reduce", "difference", "compare", "comparison",

                    "what is", "what does", "meaning", "explain", "define", "unit", "how to")

    if not any(term in question for term in detail_terms):

        return None

    facts = {

        "pH": {

            "causes": "pH can be affected by local geology, dissolved minerals, runoff, industrial or agricultural inputs, and treatment processes. A pH reading alone cannot identify the exact cause.",

            "precautions": "Verify the pH sensor calibration and repeat the measurement. If the value is outside the applicable local guideline, avoid relying on the reading alone to decide drinking-water safety and arrange further testing.",

            "remedies": "Investigate the source and water chemistry first. Any pH correction should be selected by qualified personnel for that water source, then pH and other relevant parameters should be retested. Do not add chemicals based on pH alone.",

        },

        "TDS": {

            "causes": "TDS can rise because of dissolved minerals and salts, source-water geology, runoff, or some human activities. TDS alone does not identify which substances are present.",

            "precautions": "Check calibration and repeat the measurement. If TDS is elevated, compare it with the project's stated reference limits and arrange further testing to identify the dissolved substances.",

            "remedies": "Choose treatment only after identifying the water chemistry; suitable systems vary with the dissolved substances. Retest after treatment. Do not assume a low TDS reading proves water is microbiologically safe.",

        },

        "turbidity": {

            "causes": "Common causes include suspended soil or clay, sediment stirred up in a source or tank, runoff after rain, organic particles, and inadequate filtration. A turbidity reading alone does not identify the particles or prove that pathogens are present or absent.",

            "precautions": "Check the sensor is clean, calibrated, and correctly positioned; repeat the reading and inspect the source for recent disturbance or runoff. If water is visibly cloudy or exceeds the applicable guideline, do not assume it is safe to drink; use a verified alternative source while the cause is assessed.",

            "remedies": "Depending on the source, settling and appropriate filtration may reduce suspended particles. Heavily turbid water may require professionally selected treatment such as coagulation and sedimentation followed by filtration. Disinfection may also be needed; clear appearance alone does not prove safety. Retest after treatment.",

        },

        "temperature": {

            "causes": "Water temperature can vary with weather, storage conditions, source depth, pipes, and time of day.",

            "precautions": "Check the probe placement and calibration and compare repeated measurements. This project's temperature input alone is not a drinking-water safety test.",

            "remedies": "Investigate unusual changes in the source or storage conditions. Temperature by itself does not establish which treatment is required; assess other water-quality parameters as well.",

        },

    }

    sections = []

    for key in keys:

        info = parameter_data.get(key, {})

        name = info.get("name", key)

        unit = info.get("unit", "unit not specified")

        description = info.get("description", "No definition is available in the local knowledge base.")

        block = [f"{name} ({unit})", f"Meaning: {description}"]

        if info.get("interpretation"):

            interp = info["interpretation"]

            block.append("Interpretation: " + "; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in interp.items()))

        if any(term in question for term in ("cause", "causes", "why")):

            block.append("Common causes: " + facts[key]["causes"])

        if any(term in question for term in ("precaution", "precautions", "safe", "safety", "before drinking")):

            block.append("Precautions: " + facts[key]["precautions"])

        if any(term in question for term in ("remedy", "remedies", "treat", "treatment", "reduce", "how to")):

            block.append("Possible remedies: " + facts[key]["remedies"])

        sections.append("\n".join(block))

    if len(keys) > 1:

        sections.append("Difference: pH describes acidity/alkalinity, TDS describes the amount of dissolved material, turbidity describes cloudiness from suspended particles, and temperature describes how warm or cool the water is. They measure different properties and cannot substitute for one another.")

    return "\n\n".join(sections) + "\n\nSafety note: These explanations are general guidance. The four monitored parameters alone cannot certify drinking-water safety."



def _direct_live_answer(question, water_quality, analysis, decision, agent_result, standards_data):

    """Answer common live-reading questions deterministically before the LLM."""

    q = normalize_text(question)

    if not water_quality or water_quality.get("available") is False:

        return None



    specs = [

        ("turbidity", ("turbidity", "cloudiness"), ("turbidity", "Turbidity_NTU"), "NTU"),

        ("pH", ("ph", "acidity", "alkalinity"), ("pH", "ph"), "pH"),

        ("TDS", ("tds", "total dissolved solids", "dissolved solids"), ("TDS", "TDS_ppm", "tds", "tds_ppm"), "mg/L"),

        ("temperature", ("temperature", "water temperature"), ("temperature", "Temperature_C", "temp"), "°C"),

    ]

    # Handle hypothetical/action questions BEFORE current-reading checks.
    # Otherwise phrases such as "if pH goes below 6.5" are mistaken for
    # questions asking only for the current pH.
    action_terms = (
        "what should i do", "what action", "what should i", "how should i",
        "what do i do", "what steps", "what can i do", "if ", "when "
    )
    asks_action = any(term in q for term in action_terms)
    if asks_action and any(term in q for term in ("ph", "acidity", "alkalinity")) and any(
        term in q for term in ("below", "falls", "drop", "decrease", "low", "increases", "increase")
    ):
        ph_standard = (standards_data.get("parameters", {}) or {}).get("pH", {}) or {}
        low = ph_standard.get("acceptable_min", 6.5)
        current = water_quality.get("pH", water_quality.get("ph"))
        current_text = (
            f" Your latest measured pH is {current}, which is within the configured range."
            if current is not None and str(current).strip() else ""
        )
        return (
            f"If pH falls below {low}, first repeat the measurement and check that the pH sensor "
            "is clean and calibrated. Compare the confirmed result with the applicable local "
            "guideline and arrange further water-quality testing to investigate the cause. "
            "Do not add chemicals or attempt pH correction based on this reading alone; any "
            "treatment should be selected by qualified personnel after assessing the water chemistry. "
            "Retest after any treatment. pH alone cannot confirm drinking-water safety."
            + current_text
        )

    if asks_action and any(term in q for term in ("turbidity", "cloudiness", "cloudy water")) and any(
        term in q for term in ("increase", "increases", "rise", "rises", "high", "above", "exceeds", "if ", "when ")
    ):
        turbidity_standard = (standards_data.get("parameters", {}) or {}).get("turbidity", {}) or {}
        limit = turbidity_standard.get("acceptable_max", 1.0)
        current = water_quality.get("turbidity", water_quality.get("Turbidity_NTU"))
        current_text = (
            f" Your latest measured turbidity is {current} NTU; the project's configured threshold is {limit} NTU."
            if current is not None and str(current).strip() else
            f" Compare the next reading with the project's configured threshold of {limit} NTU."
        )
        return (
            "If turbidity increases, repeat the measurement and check that the sensor is clean, "
            "calibrated, and positioned correctly. Inspect the source or storage tank for sediment, "
            "runoff, or other disturbance. If the confirmed reading exceeds the applicable guideline "
            "or the water looks cloudy, use a verified alternative source for drinking while the cause "
            "is assessed. Appropriate settling and filtration may help depending on the source; arrange "
            "suitable testing and treatment guidance, then retest. Clear-looking water is not proof of safety."
            + current_text
        )

    spec = next((item for item in specs if any(alias in q for alias in item[1])), None)

    if spec and any(term in q for term in ("high", "low", "normal", "above", "below", "within", "current", "reading", "value", "status", "acceptable", "elevated", "is my", "is it", "right now")):

        label, aliases, value_keys, unit = spec

        value = next((water_quality.get(k) for k in value_keys if water_quality.get(k) is not None), None)

        if value is None:

            return f"The current {label} reading is unavailable. Please check the sensor connection and latest Firebase reading."

        try:

            number = float(value)

        except (TypeError, ValueError):

            return f"The current {label} reading is {value}, but it could not be assessed numerically."

        standards = (standards_data.get("parameters", {}) or {})

        standard_key = "pH" if label == "pH" else label

        standard = standards.get(standard_key, {}) or {}

        status_obj = (analysis.get(standard_key, {}) or {}) if isinstance(analysis, dict) else {}

        status = status_obj.get("status") if isinstance(status_obj, dict) else None

        if label == "pH":

            low, high = standard.get("acceptable_min", 6.5), standard.get("acceptable_max", 8.5)

            assessment = f"within the configured reference range of {low}–{high}" if float(low) <= number <= float(high) else (f"below the configured reference range of {low}–{high}" if number < float(low) else f"above the configured reference range of {low}–{high}")

        elif label == "turbidity":

            limit = standard.get("acceptable_max", 1.0)

            assessment = f"above the project's configured threshold of {limit} NTU" if number > float(limit) else f"within the project's configured threshold of {limit} NTU"

        elif label == "TDS":

            limit = standard.get("acceptable_max", 500)

            assessment = f"above the configured reference limit of {limit} mg/L" if number > float(limit) else f"within the configured reference limit of {limit} mg/L"

        else:

            assessment = f"currently classified as {status}" if status else "monitored as an input to the model; temperature alone does not establish drinking-water safety"

        if label == "turbidity" and any(t in q for t in ("high", "above", "elevated")):

            prefix = "Yes" if "above" in assessment else "No"

            return f"{prefix}. Your latest turbidity reading is {number:g} NTU, {assessment}. Repeat the measurement and check sensor calibration. Do not rely on this four-sensor system alone to certify drinking-water safety."

        if label == "pH" and any(t in q for t in ("normal", "high", "low", "above", "below", "acceptable")):

            return f"Your latest pH reading is {number:g}; it is {assessment}. This reading alone does not certify drinking-water safety."

        if label in ("TDS", "temperature"):

            return f"Your latest {label} reading is {number:g} {unit}. It is {assessment}."

        return f"Your latest {label} reading is {number:g} {unit}; it is {assessment}."



    if any(term in q for term in ("wqi", "cmi", "monitoring index", "water quality index")):

        model = agent_result.get("model_prediction") or {}

        cmi = agent_result.get("cmi") or model.get("cmi") or {}

        score = cmi.get("wqi", cmi.get("score"))

        category = cmi.get("category", "not available")

        if score is not None:

            return f"The current ClearWater Monitoring Index (CMI/WQI) is {score}/100, category {category}. It is a project-specific monitoring score, not a certified drinking-water safety result."



    if any(term in q for term in ("water safe", "safe right now", "safe to drink", "overall status", "why warning")):

        status = decision.get("overall_status", decision.get("status", "Unavailable"))

        prediction = (agent_result.get("model_prediction") or {}).get("prediction", decision.get("model_prediction", "Unavailable"))

        reasons = []

        for name, detail in (analysis or {}).items():

            if isinstance(detail, dict) and any(word in str(detail.get("status", "")).lower() for word in ("not met", "warning", "high", "outside", "fail")):

                reasons.append(name)

        reason_text = f" The parameter(s) requiring attention are: {', '.join(reasons)}." if reasons else " Check the parameter assessments for the reason behind the decision."

        return f"The current monitored decision is {status}, while the CNN-LSTM prediction is {prediction}. These outputs serve different purposes and the model prediction does not override the rule-based decision.{reason_text} The four monitored parameters cannot certify that water is safe to drink; arrange appropriate testing before relying on it for drinking."

    return None



def generate_response(user_question):

    """

    Generates a chatbot response using the Agentic AI system.

    """

    agent_result = run_agent()

    question = normalize_text(user_question)

    water_quality = agent_result["water_quality"]

    decision = agent_result["decision"]

    analysis = agent_result["analysis"]

    recommendations = agent_result["recommendation"]

    # Handle explicit requests for a complete/current report deterministically.

    # This uses the already-computed agent result and does not invent readings.

    report_question = normalize_text(user_question)

    asks_for_full_report = (

        any(term in report_question for term in (

            "complete report", "full report", "all results", "current results",

            "latest results", "computed results", "actual readings", "sensor readings",

            "overall decision", "complete water quality report"

        ))

        or (

            "confidence" in report_question

            and any(term in report_question for term in ("prediction", "wqi", "cmi", "readings"))

            and any(term in report_question for term in ("report", "results", "explain", "include"))

        )

    )

    if asks_for_full_report and not os.getenv("GEMINI_API_KEY", "").strip():

        model_result = agent_result.get("model_prediction") or {}

        cmi_result = agent_result.get("cmi") or model_result.get("cmi") or {}

        latest = model_result.get("latest_sensor_reading") or {}

        # The model's latest reading is preferred; agent sensor values are fallback.

        values = {

            "pH": latest.get("pH", water_quality.get("pH", "Unavailable")),

            "TDS": latest.get("TDS_ppm", latest.get("TDS", water_quality.get("TDS", "Unavailable"))),

            "Turbidity": latest.get("Turbidity_NTU", latest.get("turbidity", water_quality.get("turbidity", "Unavailable"))),

            "Temperature": latest.get("Temperature_C", latest.get("temperature", water_quality.get("temperature", "Unavailable"))),

        }

        prediction = model_result.get("prediction", decision.get("model_prediction", "Unavailable"))

        confidence = model_result.get("confidence")

        score = cmi_result.get("wqi", cmi_result.get("score", "Unavailable"))

        category = cmi_result.get("category", "Unavailable")

        overall_status = decision.get("overall_status", decision.get("status", "Unavailable"))

        lines = [

            "CURRENT WATER-QUALITY TEST REPORT",

            "(Values are from the current agent result; test/simulated readings are not a drinking-water certification.)",

            "",

            f"pH: {values['pH']}",

            f"TDS: {values['TDS']} ppm",

            f"Turbidity: {values['Turbidity']} NTU",

            f"Temperature: {values['Temperature']} °C",

            "",

            f"CNN-LSTM prediction: {prediction}",

            f"Model confidence: {confidence}%" if confidence is not None else "Model confidence: Unavailable",

            f"CMI/WQI score: {score}",

            f"CMI/WQI category: {category}",

            f"Overall system status: {overall_status}",

            "",

            "PARAMETER STATUS:"

        ]

        for name, details in analysis.items():

            if isinstance(details, dict):

                lines.append(f"- {name}: {details.get('status', 'Not available')}")

        # Also report objective assessments supplied by the CMI/WQI calculator.

        statuses = cmi_result.get("parameter_status") or {}

        for name, details in statuses.items():

            if isinstance(details, dict):

                status = details.get("status", "Not available")

                failed = details.get("failed_tests")

                tests = details.get("tests")

                suffix = f" ({failed}/{tests} tests failed)" if failed is not None and tests is not None else ""

                lines.append(f"- {name}: {status}{suffix}")

        lines.extend(["", "RECOMMENDATIONS:"])

        if recommendations:

            lines.extend(f"- {item}" for item in recommendations)

        else:

            lines.append("- No approved recommendations were returned by the agent.")

        lines.extend([

            "",

            "SAFETY NOTE: The CNN-LSTM classification and this project-specific index only describe the monitored inputs. They do not prove that water is safe to drink. Use appropriate laboratory testing and applicable local guidance."

        ])

        return {

            "question": user_question,

            "response": "\n".join(lines),

            "response_source": "deterministic_current_results",

            "agent_result": agent_result,

        }

    faq_data = get_faq()

    parameter_data = get_parameter_knowledge().get("parameters", {})

    standards_data = get_standards()

    model_knowledge = get_model_knowledge().get("model", {})



    # Prefer concise, data-grounded answers for live parameter/WQI/status questions.

    direct_answer = _direct_live_answer(

        user_question, water_quality, analysis, decision, agent_result, standards_data

    )

    # Temporary diagnostics: inspect the actual question, live values, and rule result.

    logger.warning("CHATBOT DEBUG question=%r", user_question)

    logger.warning("CHATBOT DEBUG water_quality=%r", water_quality)

    logger.warning("CHATBOT DEBUG direct_answer=%r", direct_answer)

    # Optional conversational layer: the agent remains responsible for the

    # readings, parameter analysis, final decision, and approved recommendations.

    # Gemini only explains those already-computed results to the user.

    if os.getenv("GEMINI_API_KEY", "").strip():

        try:

            from api.llm_api import ask_llm

            context = {

                "sensor_readings": water_quality,

                "deterministic_interpretation": direct_answer,

                "parameter_analysis": analysis,

                "model_prediction": agent_result.get("model_prediction", {}),

                "overall_decision": decision,

                "approved_recommendations": recommendations,

                "precautions_remedies_follow_up": agent_result.get("safety_advice", {}),

                "project_CMI": agent_result.get("cmi"),

                "reference_standards": standards_data,

                "parameter_knowledge": parameter_data,

                "model_knowledge": model_knowledge,

                "data_available": water_quality.get("available", True),

            }

            prompt = f"""You are the conversational explanation layer for a water-quality monitoring project.

The Python agent has already calculated the sensor analysis, overall decision, and approved recommendations.

Explain these results clearly and directly in simple language, answering the user's exact question.

Rules:

- Gemini is the primary conversational response generator when configured. Use the provided live readings, analysis, decision, approved recommendations, reference standards, and deterministic_interpretation as grounded project context. Explain results naturally instead of copying a fixed fallback sentence.

- For hypothetical questions, answer the hypothetical first and then separately mention current measured values if available. Never treat a hypothetical condition as the current reading.

- For action/recommendation questions, provide clear practical next steps grounded in readings and configured thresholds. Do not invent readings, thresholds, model outputs, or treatment instructions.

- Answer the user's exact question, including EVERY requested part. Never return only a copied one-line parameter description when the user asks for causes, precautions, remedies, examples, or comparisons.

- For questions asking about a parameter's meaning, causes, precautions, and/or remedies, use clear headings for each requested part and explain them in useful detail.

- For comparison questions, explain each parameter and then state the practical difference between them.

- Treat the supplied context as the only source for this reading; never invent or change sensor values.

- Do not recalculate, override, or contradict the Python decision or approved recommendations.

- Clearly distinguish measured readings, model prediction, overall decision, and recommendations.

- Explain why the decision was made only when the supplied analysis supports that explanation.

- If data or a model prediction is unavailable, say so plainly; still answer general educational questions using the supplied knowledge base and established general knowledge.

- Do not claim that these four sensors prove water is safe to drink or detect contaminants they do not measure.

- Explain the supplied precautions, possible remedies, and follow-up checks as separate sections when relevant.

- Treat remedies as general guidance, not a chemical-treatment prescription. Never invent chemical doses or suggest adding treatment chemicals without qualified guidance.

- For low pH, explain that possible causes need testing; do not claim the exact cause from pH alone. Any treatment must be selected based on water chemistry by qualified personnel, followed by retesting.

- If asked a general concept question, explain it simply and relate it to this project only where relevant.

- Do not repeat the entire context as raw JSON.

- Be explicit when advice is general educational guidance rather than a finding from current sensor data.

USER QUESTION:

{user_question}

COMPUTED PROJECT CONTEXT:

{json.dumps(context, ensure_ascii=False, default=str)}

"""

            llm_response = ask_llm(prompt)

            if isinstance(llm_response, str) and llm_response.strip():

                return {

                    "question": user_question,

                    "response": llm_response.strip(),

                    "response_source": "gemini_explanation",

                    "agent_result": agent_result,

                }

        except Exception as exc:

            # Keep the existing deterministic FAQ/rule responses working if the

            # optional Gemini service is unavailable or misconfigured.

            logger.warning("Gemini explanation failed; using built-in response: %s", exc)

    # Gemini is the primary response generator. Keep deterministic live answers
    # as a reliable fallback only when Gemini is unavailable or returns no answer.
    if direct_answer:
        return {
            "question": user_question,
            "response": direct_answer,
            "response_source": "deterministic_live_answer_fallback",
            "agent_result": agent_result,
        }

    # --------------------------------------------------

    # KNOWLEDGE-BASE CONTENT: parameter definitions / standards / model

    # --------------------------------------------------

    normalized_parameter = None

    if "ph" in question or "acidity" in question or "alkalinity" in question:

        normalized_parameter = "pH"

    elif "tds" in question or "dissolved solids" in question:

        normalized_parameter = "TDS"

    elif "turbidity" in question or "cloudiness" in question:

        normalized_parameter = "turbidity"

    elif "temperature" in question:

        normalized_parameter = "temperature"

    # Knowledge-base fallback if Gemini is not configured or unavailable.

    # Prefer complete answers for multi-part questions over returning only a definition.

    educational_response = _educational_parameter_fallback(user_question, question, parameter_data)

    if educational_response:

        return {

            "question": user_question,

            "response": educational_response,

            "response_source": "knowledge_base_fallback",

            "agent_result": agent_result,

        }

    asks_definition = any(term in question for term in ("what is", "what does", "meaning", "explain", "define", "unit"))

    if normalized_parameter and asks_definition:

        info = parameter_data.get(normalized_parameter, {})

        interpretation = info.get("interpretation", {})

        response = f"{info.get('name', normalized_parameter)} ({info.get('unit', 'unit not specified')}): {info.get('description', 'Description not available in parameters.json')}"

        if interpretation:

            response += " Interpretation: " + "; ".join(f"{key.replace('_', ' ')}: {value}" for key, value in interpretation.items()) + "."

        if info.get("usage"):

            response += " " + info["usage"]

        return {"question": user_question, "response": response, "agent_result": agent_result}

    if any(term in question for term in ("standard", "bis", "acceptable limit", "permissible limit", "reference limit")):

        standard = standards_data.get("standard", {})

        parameters = standards_data.get("parameters", {})

        lines = [f"Reference: {standard.get('name', 'not specified')} — {standard.get('description', '')}".strip()]

        for name, details in parameters.items():

            range_text = details.get("acceptable_range")

            if not range_text and details.get("acceptable_max") is not None:

                range_text = f"acceptable maximum {details['acceptable_max']} {details.get('unit', '')}".strip()

            if details.get("permissible_max") is not None:

                range_text = (range_text + "; " if range_text else "") + f"permissible maximum {details['permissible_max']} {details.get('unit', '')}".strip()

            if range_text:

                lines.append(f"{name}: {range_text}")

            elif details.get("threshold_available") is False:

                lines.append(f"{name}: no project-specific safety threshold is defined; monitored as model input")

        lines.append(standards_data.get("important_note", ""))

        return {"question": user_question, "response": "\n".join(lines), "agent_result": agent_result}

    if any(term in question for term in ("how does the model", "what is cnn", "what is lstm", "model architecture", "cnn lstm", "deep learning model")):

        architecture = model_knowledge.get("architecture", {})

        parts = [f"{model_knowledge.get('full_name', model_knowledge.get('name', 'Model'))}: {model_knowledge.get('purpose', '')}"]

        for component, details in architecture.items():

            if isinstance(details, dict):

                parts.append(f"{component}: {details.get('role', '')}")

        parts.append("Input parameters: " + ", ".join(model_knowledge.get("input_parameters", [])))

        parts.append("The model provides a classification; the Agentic AI interprets it and prepares recommendations.")

        parts.append("This system's four monitored parameters alone cannot certify complete drinking-water safety.")

        return {"question": user_question, "response": "\n".join(parts), "agent_result": agent_result}

    # General knowledge and FAQ questions work even before the first sensor reading.

    if not water_quality.get("available", True):

        faq_answer = find_faq_answer(user_question, faq_data)

        if faq_answer is not None:

            return {"question": user_question, "response": faq_answer, "agent_result": agent_result}

        response = (

            "No actual sensor reading is available yet. Submit a reading through "

            "POST /api/readings or connect the ESP32 publisher, then try again. "

            "The system will not invent sensor values or a model prediction."

        )

        return {"question": user_question, "response": response, "agent_result": agent_result}

    # --------------------------------------------------

    # 1. CURRENT SENSOR VALUES

    # --------------------------------------------------

    if (

        ("current" in question or "my" in question)

        and "ph" in question

        and (

            "value" in question

            or "reading" in question

            or "level" in question

            or "current" in question

        )

    ):

        response = (

            f"Your current pH reading is "

            f"{water_quality['pH']}."

        )

        return {

            "question": user_question,

            "response": response,

            "agent_result": agent_result

        }

    if (

        ("current" in question or "my" in question)

        and "tds" in question

        and (

            "value" in question

            or "reading" in question

            or "level" in question

            or "current" in question

        )

    ):

        response = (

            f"Your current TDS reading is "

            f"{water_quality['TDS']} mg/L."

        )

        return {

            "question": user_question,

            "response": response,

            "agent_result": agent_result

        }

    if (

        ("current" in question or "my" in question)

        and "turbidity" in question

        and (

            "value" in question

            or "reading" in question

            or "level" in question

            or "current" in question

        )

    ):

        response = (

            f"Your current turbidity reading is "

            f"{water_quality['turbidity']} NTU."

        )

        return {

            "question": user_question,

            "response": response,

            "agent_result": agent_result

        }

    if (

        ("current" in question or "my" in question)

        and "temperature" in question

        and (

            "value" in question

            or "reading" in question

            or "current" in question

        )

    ):

        response = (

            f"Your current water temperature is "

            f"{water_quality['temperature']} °C."

        )

        return {

            "question": user_question,

            "response": response,

            "agent_result": agent_result

        }

    # --------------------------------------------------

    # 2. CURRENT WATER QUALITY STATUS

    # --------------------------------------------------

    if (

        "safe right now" in question

        or "water safe right now" in question

        or "current status" in question

        or "current water quality" in question

        or "how is my water" in question

        or "is my water safe" in question

    ):

        status = decision["overall_status"]

        prediction = decision["model_prediction"]

        response = (

            f"The current monitored water-quality status is "

            f"{status}. The CNN-LSTM model predicts "

            f"{prediction}. "

            f"This result is based on the parameters monitored "

            f"by this project and does not guarantee complete "

            f"drinking-water safety."

        )

        return {

            "question": user_question,

            "response": response,

            "agent_result": agent_result

        }

    # --------------------------------------------------

    # 3. CLEARWATER MONITORING INDEX (CMI)

    # --------------------------------------------------

    if any(term in question for term in ("cmi", "monitoring index", "wqi", "water quality index")):

        cmi = agent_result.get("cmi")

        if not cmi:

            response = "The CMI is currently unavailable. The trained DL API needs 10 actual chronological sensor readings and must be running."

        else:

            score = cmi.get("wqi", "not returned")

            category = cmi.get("category", "not returned")

            response = f"The ClearWater Monitoring Index (CMI) score is {score}, category {category}. It is calculated separately from the CNN-LSTM classification using the project’s monitoring formula. It is not a certified drinking-water safety result."

            assessments = cmi.get("parameter_status") or {}

            if assessments:

                response += " Parameter assessments: " + "; ".join(f"{name}: {details.get('status', 'not available')}" for name, details in assessments.items() if isinstance(details, dict) ) + "."

        return {"question": user_question, "response": response, "agent_result": agent_result}

    # --------------------------------------------------

    # 3. CURRENT CNN-LSTM PREDICTION

    # --------------------------------------------------

    if (

        "current prediction" in question

        or "model prediction" in question

        or "cnn lstm prediction" in question

    ):

        prediction = decision["model_prediction"]

        model_result = agent_result.get("model_prediction", {})

        if not model_result.get("available"):

            response = "The actual CNN-LSTM prediction is unavailable. " + model_result.get("reason", "Check that the DL API is running and that 10 real chronological readings are stored.")

        else:

            model_name = model_knowledge.get("full_name", model_knowledge.get("name", "configured model"))

            model_purpose = model_knowledge.get("purpose", "Classifies the monitored sensor sequence.")

            response = f"The actual trained {model_name} prediction is {prediction}. {model_purpose}"

            architecture = model_knowledge.get("architecture", {})

            architecture_text = " ".join(

                f"{component}: {details.get('role', '')}" for component, details in architecture.items()

                if isinstance(details, dict) and details.get("role")

            )

            if architecture_text:

                response += " Architecture knowledge: " + architecture_text

            if model_result.get("probability") is not None:

                response += f" Unsafe-class probability: {float(model_result['probability']):.4f}."

            if model_result.get("confidence") is not None:

                response += f" Confidence-like percentage returned by the model: {model_result['confidence']}%."

            response += " This model output is not a guarantee of drinking-water safety."

        return {

            "question": user_question,

            "response": response,

            "agent_result": agent_result

        }

    # --------------------------------------------------

    # 4. CURRENT RECOMMENDATIONS

    # --------------------------------------------------

    if (

        "what should i do now" in question

        or "what should i do with the water" in question

        or "current recommendation" in question

        or "what do you recommend now" in question

    ):

        response = (

            f"The current overall status is "

            f"{decision['overall_status']}.\n\n"

            f"Recommendations:\n"

            + "\n".join(

                f"- {item}"

                for item in recommendations

            )

        )

        return {

            "question": user_question,

            "response": response,

            "agent_result": agent_result

        }

    # --------------------------------------------------

    # 5. FAQ / KNOWLEDGE BASE

    # --------------------------------------------------

    faq_answer = find_faq_answer(

        user_question,

        faq_data

    )

    if faq_answer is not None:

        return {

            "question": user_question,

            "response": faq_answer,

            "agent_result": agent_result

        }

    # --------------------------------------------------

    # 6. PARAMETER STATUS

    # --------------------------------------------------

    if "ph" in question and (

        "status" in question

        or "condition" in question

    ):

        response = (

            f"The current pH is {water_quality['pH']}. "

            f"Its current status is "

            f"{analysis['pH']['status']}."

        )

        return {

            "question": user_question,

            "response": response,

            "agent_result": agent_result

        }

    if "tds" in question and (

        "status" in question

        or "condition" in question

    ):

        response = (

            f"The current TDS is {water_quality['TDS']} mg/L. "

            f"Its current status is "

            f"{analysis['TDS']['status']}."

        )

        return {

            "question": user_question,

            "response": response,

            "agent_result": agent_result

        }

    if "turbidity" in question and (

        "status" in question

        or "condition" in question

    ):

        response = (

            f"The current turbidity is "

            f"{water_quality['turbidity']} NTU. "

            f"Its current status is "

            f"{analysis['turbidity']['status']}."

        )

        return {

            "question": user_question,

            "response": response,

            "agent_result": agent_result

        }

    # --------------------------------------------------

    # MODEL KNOWLEDGE FROM model_knowledge.json

    # --------------------------------------------------

    if any(term in question for term in ("how does the model", "what is cnn", "what is lstm", "model architecture", "cnn lstm", "deep learning model")):

        architecture = model_knowledge.get("architecture", {})

        parts = [f"{model_knowledge.get('full_name', model_knowledge.get('name', 'Model'))}: {model_knowledge.get('purpose', '')}"]

        for component, details in architecture.items():

            if isinstance(details, dict):

                parts.append(f"{component}: {details.get('role', '')}")

        parts.append("Input parameters: " + ", ".join(model_knowledge.get("input_parameters", [])))

        parts.append("The model provides a classification; the Agentic AI interprets it and prepares recommendations.")

        parts.append("This system's four monitored parameters alone cannot certify complete drinking-water safety.")

        return {"question": user_question, "response": "\n".join(parts), "agent_result": agent_result}

    # --------------------------------------------------

    # 7. GENERAL FALLBACK

    # --------------------------------------------------

    response = (

        "I can help you with current water-quality readings, "

        "CNN-LSTM predictions, water-quality status, "

        "recommendations, and water-quality FAQs."

    )

    return {

        "question": user_question,

        "response": response,

        "agent_result": agent_result

    }

# ------------------------------------------------------

# FEEDBACK FUNCTION

# ------------------------------------------------------

def give_feedback(

    feedback_type,

    user_feedback,

    agent_result

):

    """

    Sends chatbot/user feedback to the feedback system.

    """

    prediction = agent_result["decision"]["model_prediction"]

    recommendation = agent_result["recommendation"]

    water_quality = agent_result["water_quality"]

    feedback = submit_feedback(

        feedback_type=feedback_type,

        user_feedback=user_feedback,

        prediction=prediction,

        recommendation=recommendation,

        water_quality=water_quality

    )

    return feedback

# ------------------------------------------------------

# TEST CHATBOT + FEEDBACK

# ------------------------------------------------------

if __name__ == "__main__":

    print("======================================")

    print("   CHATBOT + FEEDBACK SYSTEM TEST")

    print("======================================")

    # Get chatbot response

    result = generate_response(

        "Is my water safe right now?"

    )

    print("\nUser:")

    print(result["question"])

    print("\nChatbot:")

    print(result["response"])

    # Submit prediction feedback

    feedback1 = give_feedback(

        feedback_type="prediction",

        user_feedback="Prediction was correct",

        agent_result=result["agent_result"]

    )

    print("\nPrediction Feedback Saved:")

    print(feedback1)

    # Submit recommendation feedback

    feedback2 = give_feedback(

        feedback_type="recommendation",

        user_feedback="Recommendation was helpful",

        agent_result=result["agent_result"]

    )

    print("\nRecommendation Feedback Saved:")

    print(feedback2)

    # Submit chatbot feedback

    feedback3 = give_feedback(

        feedback_type="chatbot",

        user_feedback="Response was helpful",

        agent_result=result["agent_result"]

    )

    print("\nChatbot Feedback Saved:")

    print(feedback3)

    print("\n======================================")

    print("   CHATBOT + FEEDBACK TEST COMPLETE")

    print("======================================")
