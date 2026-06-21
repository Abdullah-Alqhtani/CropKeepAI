import re
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.models import Disease, DiseaseProductMapping, KnowledgeBaseEntry, Product

UNKNOWN_DESCRIPTION = "Sorry, we could not confidently identify this plant problem. General plant-care recommendations are shown below."
UNKNOWN_TREATMENT = "\n".join(
    [
        "Remove heavily affected leaves if safe.",
        "Keep the plant isolated from healthy plants.",
        "Avoid overhead watering.",
        "Improve airflow.",
        "Monitor symptoms for 48-72 hours.",
        "Consult an agricultural expert if symptoms spread.",
    ]
)
UNKNOWN_PREVENTION = "\n".join(
    [
        "Water at soil level.",
        "Avoid overcrowding.",
        "Remove dead or infected leaves.",
        "Keep tools clean.",
        "Monitor leaves regularly.",
    ]
)
UNKNOWN_ENVIRONMENT = "\n".join(
    [
        "Avoid high humidity around leaves.",
        "Improve ventilation.",
        "Avoid watering late in the day.",
    ]
)


def normalize_disease_name(value: str, crop: str = "") -> str:
    text = (value or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\b(disease|plant|crop|leaf|leaves)\b", " ", text)

    for token in re.findall(r"[a-z0-9]+", (crop or "").lower()):
        text = re.sub(rf"\b{re.escape(token)}\b", " ", text)

    return " ".join(text.split())


def match_database_disease(
    db: Session,
    detected_crop: str,
    detected_disease: str,
    detected_symptoms: str = "",
    tags: list[str] | None = None,
) -> tuple[Disease | None, str, float]:
    normalized_detected = normalize_disease_name(detected_disease, detected_crop)
    crop_text = (detected_crop or "").strip().lower()
    evidence_terms = _terms(" ".join([detected_symptoms or "", " ".join(tags or [])]))
    diseases = db.query(Disease).join(Disease.crop_type).all()

    exact_matches: list[tuple[bool, Disease]] = []
    for disease in diseases:
        normalized_database = normalize_disease_name(disease.name, disease.crop_type.name)
        if normalized_detected and normalized_detected == normalized_database:
            crop_matches = bool(crop_text) and crop_text == disease.crop_type.name.lower()
            exact_matches.append((crop_matches, disease))

    if exact_matches:
        exact_matches.sort(key=lambda item: item[0], reverse=True)
        return exact_matches[0][1], normalized_detected, 1.0

    best_match: Disease | None = None
    best_score = 0.0
    best_crop_matches = False
    candidate_scores: list[dict] = []
    for disease in diseases:
        normalized_database = normalize_disease_name(disease.name, disease.crop_type.name)
        database_terms = _database_terms(db, disease, normalized_database)

        sequence_score = 0.0
        if normalized_detected and normalized_database:
            sequence_score = SequenceMatcher(None, normalized_detected, normalized_database).ratio()

        disease_term_score = _overlap_score(set(normalized_detected.split()), set(normalized_database.split()))
        evidence_score = _overlap_score(evidence_terms, database_terms)
        score = max(sequence_score, disease_term_score, evidence_score)

        crop_matches = bool(crop_text) and crop_text == disease.crop_type.name.lower()
        if crop_matches:
            score += 0.12
            if evidence_score:
                score = max(score, evidence_score + 0.2)

        candidate_scores.append(
            {
                "disease": disease.name,
                "crop": disease.crop_type.name,
                "score": round(score, 3),
                "sequence_score": round(sequence_score, 3),
                "disease_term_score": round(disease_term_score, 3),
                "evidence_score": round(evidence_score, 3),
                "crop_match": crop_matches,
            }
        )

        if score > best_score:
            best_score = score
            best_match = disease
            best_crop_matches = crop_matches

    print(
        "Fallback disease candidate scores:",
        sorted(candidate_scores, key=lambda item: item["score"], reverse=True)[:8],
        flush=True,
    )

    if best_match and (best_score >= 0.55 or (best_crop_matches and best_score >= 0.25)):
        return best_match, normalized_detected, round(best_score, 3)
    return None, normalized_detected, round(best_score, 3)


def knowledge_for_disease(db: Session, disease: Disease | None) -> list[KnowledgeBaseEntry]:
    if not disease:
        return []
    return (
        db.query(KnowledgeBaseEntry)
        .filter(KnowledgeBaseEntry.disease_id == disease.id)
        .order_by(KnowledgeBaseEntry.id)
        .all()
    )


def build_database_diagnosis(
    classifier_data: dict,
    matched_disease: Disease | None,
    entries: list[KnowledgeBaseEntry],
) -> dict:
    detected_crop = classifier_data.get("crop_type") or "Unknown"
    detected_symptoms = classifier_data.get("symptoms") or "Unknown"

    if not matched_disease:
        diagnosis = {
            "crop_type": detected_crop,
            "disease_name": "Unknown",
            "confidence": "Low",
            "severity": "Unknown",
            "description": UNKNOWN_DESCRIPTION,
            "causes": "Unknown",
            "symptoms": detected_symptoms,
            "impact": "Unknown",
            "treatment_steps": UNKNOWN_TREATMENT,
            "preventive_actions": UNKNOWN_PREVENTION,
            "environmental_considerations": UNKNOWN_ENVIRONMENT,
        }
        _log_treatment_output(diagnosis)
        return diagnosis

    treatment_items, prevention_items = _treatment_and_prevention_from_entries(entries)

    diagnosis = {
        "crop_type": matched_disease.crop_type.name,
        "disease_name": matched_disease.name,
        "confidence": classifier_data.get("confidence", "Medium"),
        "severity": "Unknown",
        "description": matched_disease.description,
        "causes": matched_disease.causes,
        "symptoms": matched_disease.symptoms,
        "impact": matched_disease.impact,
        "treatment_steps": "\n".join(treatment_items) or matched_disease.description,
        "preventive_actions": "\n".join(prevention_items) or matched_disease.causes,
        "environmental_considerations": "Follow local regulations, product labels, PPE, re-entry intervals, and pre-harvest intervals.",
    }
    _log_treatment_output(diagnosis)
    return diagnosis


def _database_terms(db: Session, disease: Disease, normalized_database: str) -> set[str]:
    entry_text = " ".join(
        f"{entry.title} {entry.content} {entry.tags}"
        for entry in db.query(KnowledgeBaseEntry).filter(KnowledgeBaseEntry.disease_id == disease.id).all()
    )
    mapped_product_ids = [
        item.product_id
        for item in db.query(DiseaseProductMapping.product_id).filter(DiseaseProductMapping.disease_id == disease.id).all()
    ]
    product_text = ""
    if mapped_product_ids:
        product_text = " ".join(
            f"{product.name} {product.active_ingredient} {product.target_disease} {product.usage_instructions} {product.tags}"
            for product in db.query(Product).filter(Product.id.in_(mapped_product_ids)).all()
        )
    return _terms(
        " ".join(
            [
                normalized_database,
                disease.name,
                disease.crop_type.name,
                disease.description,
                disease.causes,
                disease.symptoms,
                disease.impact,
                entry_text,
                product_text,
            ]
        )
    )


def _treatment_and_prevention_from_entries(entries: list[KnowledgeBaseEntry]) -> tuple[list[str], list[str]]:
    treatment_items: list[str] = []
    prevention_items: list[str] = []

    for entry in entries:
        items = _split_items(entry.content)
        if not items:
            continue
        treatment_items.extend(items)
        if _is_prevention_entry(entry):
            prevention_items.extend(items)

    return _dedupe(treatment_items), _dedupe(prevention_items)


def _is_prevention_entry(entry: KnowledgeBaseEntry) -> bool:
    text = f"{entry.title} {entry.tags} {entry.content}".lower()
    return any(term in text for term in ["prevent", "prevention", "spacing", "airflow", "rotate", "resistant", "sanitize"])


def _split_items(text: str) -> list[str]:
    items: list[str] = []
    for line in (text or "").replace(";", ".").splitlines():
        for part in line.split("."):
            item = part.strip(" -\t")
            if item and item.lower() != "unknown":
                items.append(item)
    return items


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        key = " ".join(item.lower().split())
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _terms(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (value or "").lower())
        if len(token) > 2 and token not in {"unknown", "plant", "crop", "disease", "leaf", "leaves"}
    }


def _overlap_score(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _log_treatment_output(diagnosis: dict) -> None:
    print(
        "Treatment output:",
        {
            "crop": diagnosis.get("crop_type"),
            "disease": diagnosis.get("disease_name"),
            "treatment_steps": diagnosis.get("treatment_steps"),
            "preventive_actions": diagnosis.get("preventive_actions"),
        },
        flush=True,
    )
