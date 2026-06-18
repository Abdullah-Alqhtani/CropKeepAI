import re

from sqlalchemy.orm import Session

from app.models import CropType, Disease, DiseaseProductMapping, Product, ProductRecommendation


def create_product_recommendations(
    db: Session,
    diagnosis_id: int,
    crop_type: str,
    disease_name: str,
    symptoms: str = "",
    tags: list[str] | None = None,
) -> list[ProductRecommendation]:
    if _is_unknown(crop_type) or _is_unknown(disease_name):
        print(
            "Product matching skipped: diagnosis is uncertain.",
            {"crop": crop_type, "disease": disease_name, "symptoms": symptoms, "tags": tags or []},
            flush=True,
        )
        return []

    disease = (
        db.query(Disease)
        .join(Disease.crop_type)
        .filter(Disease.name.ilike(f"%{disease_name}%"), CropType.name.ilike(crop_type))
        .first()
    )
    if not disease:
        disease = db.query(Disease).filter(Disease.name.ilike(f"%{disease_name}%")).first()

    recommendations: list[ProductRecommendation] = []
    if disease:
        mappings = db.query(DiseaseProductMapping).filter(DiseaseProductMapping.disease_id == disease.id).all()
        for mapping in mappings:
            print(
                "Product mapped by disease mapping:",
                {"product_id": mapping.product_id, "disease": disease.name, "reason": mapping.match_reason},
                flush=True,
            )
            recommendations.append(
                ProductRecommendation(
                    diagnosis_id=diagnosis_id,
                    product_id=mapping.product_id,
                    score=0.95,
                    reason=mapping.match_reason,
                )
            )

    catalog_matches = _rank_catalog_products(db, crop_type, disease_name, symptoms, tags or [])
    existing_product_ids = {recommendation.product_id for recommendation in recommendations}
    for product, score, reason in catalog_matches:
        if product.id not in existing_product_ids:
            print(
                "Product matched by catalog evidence:",
                {"product_id": product.id, "name": product.name, "score": score, "reason": reason},
                flush=True,
            )
            recommendations.append(
                ProductRecommendation(
                    diagnosis_id=diagnosis_id,
                    product_id=product.id,
                    score=score,
                    reason=reason,
                )
            )
            existing_product_ids.add(product.id)
        if len(recommendations) >= 5:
            break

    if not recommendations:
        print(
            "No specific product recommendation found for this diagnosis.",
            {"crop": crop_type, "disease": disease_name, "symptoms": symptoms, "tags": tags or []},
            flush=True,
        )

    for recommendation in recommendations:
        db.add(recommendation)
    db.commit()
    for recommendation in recommendations:
        db.refresh(recommendation)
    return recommendations


def _rank_catalog_products(
    db: Session,
    crop_type: str,
    disease_name: str,
    symptoms: str,
    tags: list[str],
) -> list[tuple[Product, float, str]]:
    disease_terms = _terms(disease_name)
    crop_terms = _terms(crop_type)
    symptom_terms = _terms(symptoms)
    tag_terms = {term for tag in tags for term in _terms(tag)}
    products = db.query(Product).all()
    ranked: list[tuple[Product, float, str]] = []
    for product in products:
        search_text = " ".join(
            [
                product.name or "",
                product.english_name or "",
                product.product_type or "",
                product.active_ingredient or "",
                product.target_disease or "",
                product.usage_instructions or "",
                product.crops or "",
                product.tags or "",
            ]
        ).lower()
        exact_disease = disease_name and disease_name.lower() in search_text
        exact_crop = crop_type and crop_type.lower() in search_text
        disease_hits = {term for term in disease_terms if term in search_text}
        crop_hits = {term for term in crop_terms if term in search_text}
        symptom_hits = {term for term in symptom_terms if term in search_text}
        tag_hits = {term for term in tag_terms if term in search_text}

        has_disease_evidence = exact_disease or len(disease_hits) >= 2 or bool(tag_hits & disease_terms)
        has_crop_evidence = exact_crop or bool(crop_hits)
        if not has_disease_evidence:
            continue

        score = len(disease_hits) * 2 + len(crop_hits) + len(symptom_hits) + len(tag_hits)
        if exact_disease:
            score += 6
        if exact_crop:
            score += 3
        if has_crop_evidence:
            reason = f"Matched {disease_name} for {crop_type}"
        else:
            reason = f"Matched disease evidence for {disease_name}"
        evidence = sorted((disease_hits | crop_hits | symptom_hits | tag_hits))[:8]
        ranked.append((product, min(0.55 + score * 0.05, 0.92), f"{reason}. Evidence: {', '.join(evidence)}."))
    return sorted(ranked, key=lambda item: item[1], reverse=True)


def _terms(value: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]+", (value or "").lower()) if len(term) > 2 and term != "unknown"}


def _is_unknown(value: str) -> bool:
    return not value or value.strip().lower() in {"unknown", "uncertain", "n/a", "none"}
