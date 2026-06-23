"""Create catalog product recommendations for a saved diagnosis.

Direct disease-product mappings are preferred. When too few are available, the
service fills the result with safe general catalog products instead of inventing names.
"""

from sqlalchemy.orm import Session

from app.models import DiagnosisResult, DiseaseProductMapping, Product, ProductRecommendation

GENERAL_REASON = "General recommendation because the disease was not confidently identified."
PREFERRED_FALLBACK_TERMS = {"general", "fungal", "leaf", "spot", "preventive", "broad", "spectrum", "broad-spectrum"}


def create_product_recommendations(
    db: Session,
    diagnosis: DiagnosisResult,
    tags: list[str] | None = None,
) -> list[ProductRecommendation]:
    recommendations = _mapped_recommendations(db, diagnosis)
    fallback_used = False

    # Keep the result useful even when the disease is unknown or has few direct mappings.
    if len(recommendations) < 2:
        fallback_used = True
        recommendations = _fill_with_general_catalog_recommendations(db, diagnosis.id, recommendations)

    for recommendation in recommendations:
        db.add(recommendation)
    db.commit()
    for recommendation in recommendations:
        db.refresh(recommendation)

    print(
        "ProductRecommendation rows created:",
        {
            "diagnosis_id": diagnosis.id,
            "matched_disease": None if diagnosis.disease_name == "Unknown" else diagnosis.disease_name,
            "fallback_used": fallback_used,
            "products_created_count": len(recommendations),
            "tags": tags or [],
        },
        flush=True,
    )
    return recommendations


def _mapped_recommendations(db: Session, diagnosis: DiagnosisResult) -> list[ProductRecommendation]:
    # Unknown diagnoses skip disease-specific mappings and go straight to the fallback selection.
    if diagnosis.disease_name == "Unknown":
        return []

    mappings = (
        db.query(DiseaseProductMapping)
        .join(DiseaseProductMapping.disease)
        .filter(DiseaseProductMapping.disease.has(name=diagnosis.disease_name))
        .all()
    )
    print(
        "Disease product mappings found:",
        {
            "diagnosis_id": diagnosis.id,
            "matched_disease": diagnosis.disease_name,
            "product_mappings_found": len(mappings),
        },
        flush=True,
    )
    return [
        ProductRecommendation(
            diagnosis_id=diagnosis.id,
            product_id=mapping.product_id,
            score=0.95,
            reason=mapping.match_reason,
        )
        for mapping in mappings
    ]


def _fill_with_general_catalog_recommendations(
    db: Session,
    diagnosis_id: int,
    existing: list[ProductRecommendation],
) -> list[ProductRecommendation]:
    products = db.query(Product).order_by(Product.id).all()
    existing_product_ids = {recommendation.product_id for recommendation in existing}
    # Prefer broadly useful, preventive catalog products before other available products.
    preferred = [product for product in products if _is_preferred_general_product(product)]
    candidates = preferred + [product for product in products if product not in preferred]
    needed = max(0, 2 - len(existing))
    selected = [product for product in candidates if product.id not in existing_product_ids][:needed]

    print(
        "General product fallback selected:",
        {
            "diagnosis_id": diagnosis_id,
            "preferred_matches": len(preferred),
            "existing_products_count": len(existing),
            "selected_product_ids": [product.id for product in selected],
        },
        flush=True,
    )

    return existing + [
        ProductRecommendation(diagnosis_id=diagnosis_id, product_id=product.id, score=0.5, reason=GENERAL_REASON)
        for product in selected
    ]


def _is_preferred_general_product(product: Product) -> bool:
    text = " ".join(
        [
            product.name or "",
            product.english_name or "",
            product.product_type or "",
            product.active_ingredient or "",
            product.target_disease or "",
            product.usage_instructions or "",
            product.safety_notes or "",
            product.tags or "",
            product.crops or "",
        ]
    ).lower()
    normalized = text.replace("-", " ")
    return any(term in text or term in normalized for term in PREFERRED_FALLBACK_TERMS)
