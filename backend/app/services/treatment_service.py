from app.models import Disease, KnowledgeBaseEntry


UNKNOWN_TREATMENT = "Diagnosis is uncertain. Isolate the affected plant if practical, take clearer photos of leaves and stems, and consult a local agronomist before applying disease-specific pesticides."
UNKNOWN_PREVENTION = "Monitor the crop, improve airflow where possible, avoid overhead irrigation, and keep records of new symptoms."


def refine_treatment(
    diagnosis_data: dict,
    disease: Disease | None,
    entries: list[KnowledgeBaseEntry],
) -> dict:
    crop = diagnosis_data.get("crop_type", "Unknown")
    disease_name = diagnosis_data.get("disease_name", "Unknown")
    symptoms = diagnosis_data.get("symptoms", "")
    tags = diagnosis_data.get("tags", [])

    print(
        "Diagnosis detected:",
        {"crop": crop, "disease": disease_name, "symptoms": symptoms, "tags": tags},
        flush=True,
    )

    if _is_unknown(crop) or _is_unknown(disease_name) or diagnosis_data.get("confidence") == "Low":
        diagnosis_data["treatment_steps"] = UNKNOWN_TREATMENT
        diagnosis_data["preventive_actions"] = UNKNOWN_PREVENTION
        return diagnosis_data

    treatment_items = []
    prevention_items = []
    for entry in entries:
        text = entry.content.strip()
        if not text:
            continue
        if _looks_preventive(entry.title, text):
            prevention_items.extend(_split_items(text))
        else:
            treatment_items.extend(_split_items(text))

    if disease:
        treatment_items.append(f"Manage as {disease.name}: {disease.description}")
        if symptoms:
            treatment_items.append(f"Prioritize leaves or stems showing: {symptoms.replace(chr(10), '; ')}")
        prevention_items.extend(_split_items(disease.causes))

    treatment_items.extend(_split_items(diagnosis_data.get("treatment_steps", "")))
    prevention_items.extend(_split_items(diagnosis_data.get("preventive_actions", "")))

    diagnosis_data["treatment_steps"] = "\n".join(_dedupe(treatment_items)) or diagnosis_data.get("treatment_steps", "")
    diagnosis_data["preventive_actions"] = "\n".join(_dedupe(prevention_items)) or diagnosis_data.get("preventive_actions", "")
    return diagnosis_data


def _split_items(text: str) -> list[str]:
    items = []
    for line in (text or "").replace(";", ".").split("\n"):
        for part in line.split("."):
            cleaned = part.strip(" -\t")
            if cleaned and cleaned.lower() != "unknown":
                items.append(cleaned)
    return items


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    unique = []
    for item in items:
        key = " ".join(item.lower().split())
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:8]


def _looks_preventive(title: str, text: str) -> bool:
    haystack = f"{title} {text}".lower()
    return any(term in haystack for term in ["prevent", "spacing", "airflow", "rotate", "resistant", "sanitize"])


def _is_unknown(value: str) -> bool:
    return not value or value.strip().lower() in {"unknown", "uncertain", "n/a", "none"}
