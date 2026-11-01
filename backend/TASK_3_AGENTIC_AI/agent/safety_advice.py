"""Build structured precautions, possible remedies, and follow-up checks.

This module does not prescribe chemical doses. Treatment depends on source-water
chemistry and should be selected by a qualified water-treatment professional.
"""


def build_safety_advice(water_quality, analysis, decision):
    precautions = []
    remedies = []
    follow_up = []

    if not isinstance(water_quality, dict) or not water_quality.get("available", True):
        return {
            "precautions": ["Do not rely on a water-quality classification until valid sensor readings are available."],
            "remedies": ["Connect the sensor data source and submit valid readings. Do not assume missing values are safe."],
            "follow_up": ["Collect valid readings and verify sensor calibration before running the analysis again."],
            "disclaimer": "The four monitored parameters alone cannot certify drinking-water safety."
        }

    if not isinstance(analysis, dict) or not analysis:
        return {
            "precautions": ["Treat the water status as unconfirmed because parameter analysis is unavailable."],
            "remedies": ["Repeat the measurement and check the data connection."],
            "follow_up": ["Run the analysis again after valid readings are available."],
            "disclaimer": "The four monitored parameters alone cannot certify drinking-water safety."
        }

    status = str(decision.get("overall_status", "Insufficient data"))
    wqi_category = str(decision.get("wqi_category") or "").upper()
    wqi_score = decision.get("wqi_score")
    if wqi_category in ("POOR", "MARGINAL", "FAIR"):
        score_text = f" (score {wqi_score}/100)" if isinstance(wqi_score, (int, float)) else ""
        precautions.append(
            f"The project ClearWater Monitoring Index category is {wqi_category}{score_text}; investigate the contributing parameters and do not treat this index as proof of drinking-water safety."
        )
        remedies.append(
            "Review the CMI/WQI parameter assessment to identify which measured objectives failed, confirm the readings, and select any corrective action only after the water source and relevant chemistry are assessed."
        )
        follow_up.append(
            "After corrective action, collect a new valid sequence of readings and recalculate the project CMI/WQI; also verify the individual parameters and any additional tests appropriate for the intended use."
        )
    if status in ("Unsafe", "Warning", "Insufficient data"):
        precautions.append("If the water is intended for drinking, do not assume it is safe from these sensor readings alone; use an appropriate verified source while the concern is investigated.")

    ph = analysis.get("pH", {})
    ph_value = ph.get("value")
    ph_status = ph.get("status")
    if ph_status == "Unsafe" and isinstance(ph_value, (int, float)):
        if ph_value < 6.5:
            precautions.extend([
                "Verify the pH sensor calibration and repeat the reading with a fresh sample.",
                "Avoid drinking the water until the cause is investigated and its suitability is verified."
            ])
            remedies.extend([
                "Possible causes of low pH include source-water geology, acidic runoff or rainwater, and certain discharges; the reading alone cannot identify the cause.",
                "Arrange appropriate water testing to confirm pH and assess relevant contaminants or corrosion-related metals.",
                "If treatment is needed, ask a qualified water-treatment professional to select a suitable neutralization method based on the water chemistry. Do not add alkali or other chemicals by guesswork."
            ])
            follow_up.extend([
                "After any approved treatment, retest pH using a calibrated meter and compare it with the target range for the intended use.",
                "Confirm other relevant water-quality parameters as well; a corrected pH alone does not prove the water is potable."
            ])
        elif ph_value > 8.5:
            precautions.append("Verify the pH reading and avoid assuming the water is suitable for drinking until the cause is assessed.")
            remedies.extend([
                "High pH can be associated with source-water minerals or treatment chemicals; testing is needed to determine the cause.",
                "Seek qualified advice on an appropriate treatment method rather than adding acids or chemicals by guesswork."
            ])
            follow_up.append("Retest pH after any approved corrective treatment and test other relevant water-quality parameters.")

    for parameter, label in (("TDS", "TDS"), ("turbidity", "turbidity")):
        item = analysis.get(parameter, {})
        if item.get("status") in ("Warning", "Unsafe"):
            if parameter == "TDS":
                precautions.append("Investigate elevated dissolved solids before using the water for drinking.")
                remedies.append("Confirm TDS with a calibrated instrument and arrange further testing to identify which dissolved substances are present; TDS alone does not identify them.")
                follow_up.append("After any suitable treatment, retest TDS and test for the substances identified by the water assessment.")
            else:
                precautions.append("Investigate cloudy or particle-rich water before using it for drinking; turbidity alone does not establish whether pathogens are present.")
                remedies.append("Inspect the source and filtration system, and arrange appropriate testing. A suitable filtration process may be considered after the cause is assessed.")
                follow_up.append("Retest turbidity after corrective action and carry out any additional microbiological or chemical tests recommended by the water-quality assessment.")

    if status == "Safe":
        precautions.append("Continue routine monitoring; this classification covers only the parameters and rules implemented by this project.")
        follow_up.append("Keep checking sensor calibration and arrange broader water-quality testing as appropriate for the source and intended use.")
    elif status == "Insufficient data":
        precautions.append("Do not treat an unavailable or incomplete model result as a Safe classification.")
        remedies.append("Check that valid readings are being received and that the required chronological model input is available.")
        follow_up.append("Repeat the analysis once valid readings and any required model prediction are available.")

    if not remedies:
        remedies.append("No parameter-specific corrective treatment is indicated by the current rule results; continue monitoring and investigate any concerns with appropriate testing.")
    if not follow_up:
        follow_up.append("Repeat measurements with calibrated sensors and investigate unexpected changes.")

    # Deduplicate while preserving the order in which advice was added.
    return {
        "precautions": list(dict.fromkeys(precautions)),
        "remedies": list(dict.fromkeys(remedies)),
        "follow_up": list(dict.fromkeys(follow_up)),
        "disclaimer": "These are general precautions, not a treatment prescription. The four monitored parameters alone cannot certify drinking-water safety."
    }
