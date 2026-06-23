"""Provide authenticated image-upload and diagnosis-history endpoints.

This router saves an uploaded image, asks the AI service for evidence, matches
that evidence with database knowledge, and stores the final result for the user.
"""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import DiagnosisResult, ImageUpload, ProductRecommendation, User
from app.schemas.diagnosis import DiagnosisHistoryItem, DiagnosisOut, ProductRecommendationOut
from app.services.ai_service import diagnose_crop_image
from app.services.auth_service import get_current_user
from app.services.recommendation_service import create_product_recommendations
from app.services.treatment_service import (
    build_database_diagnosis,
    knowledge_for_disease,
    match_database_disease,
)

router = APIRouter()
ALLOWED_TYPES = {"image/jpeg", "image/png"}


@router.post("", response_model=DiagnosisOut)
async def create_diagnosis(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only JPG and PNG files are supported")

    # Save first so the AI service can read the image from a stable server-side path.
    upload = await _save_upload(db, user, image)

    try:
        classifier_data = diagnose_crop_image(
            upload.file_path,
            image.content_type,
            "No treatment or product knowledge is provided. Identify only crop, disease, symptoms, confidence, and tags.",
        )
    except RuntimeError as exc:
        print("Groq diagnosis unavailable; continuing with database fallback:", str(exc), flush=True)
        classifier_data = _unknown_classifier_data()

    tags = classifier_data.pop("tags", [])
    detected_crop = classifier_data.get("crop_type", "Unknown")
    detected_disease = classifier_data.get("disease_name", "Unknown")
    detected_symptoms = classifier_data.get("symptoms", "")
    # Database matching makes treatment and product advice come from approved stored data.
    matched_disease, normalized_disease, fuzzy_match_score = match_database_disease(
        db,
        detected_crop,
        detected_disease,
        detected_symptoms,
        tags,
    )

    print(
        "Database disease matching:",
        {
            "groq_disease": detected_disease,
            "groq_confidence": classifier_data.get("confidence"),
            "detected_crop": detected_crop,
            "detected_disease": detected_disease,
            "normalized_disease": normalized_disease,
            "fuzzy_match_score": fuzzy_match_score,
            "matched_database_disease": matched_disease.name if matched_disease else None,
            "confidence": classifier_data.get("confidence"),
            "symptoms": detected_symptoms,
            "tags": tags,
            "fallback_symptoms": detected_symptoms,
            "fallback_tags": tags,
        },
        flush=True,
    )

    entries = knowledge_for_disease(db, matched_disease)
    print(
        "Database knowledge entries:",
        [{"id": entry.id, "title": entry.title, "disease": entry.disease.name} for entry in entries],
        flush=True,
    )

    diagnosis_data = build_database_diagnosis(classifier_data, matched_disease, entries)
    diagnosis = DiagnosisResult(user_id=user.id, image_upload_id=upload.id, **diagnosis_data)
    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)

    recommendations = create_product_recommendations(db, diagnosis, tags)
    products_created_count = (
        db.query(ProductRecommendation)
        .filter(ProductRecommendation.diagnosis_id == diagnosis.id)
        .count()
    )
    print(
        "Diagnosis recommendation summary:",
        {
            "diagnosis_id": diagnosis.id,
            "detected_crop": detected_crop,
            "detected_disease": detected_disease,
            "normalized_disease": normalized_disease,
            "fuzzy_match_score": fuzzy_match_score,
            "matched_database_disease": matched_disease.name if matched_disease else None,
            "matched_disease": matched_disease.name if matched_disease else None,
            "fallback_used": matched_disease is None,
            "matched_products_count": len(recommendations),
            "products_created_count": products_created_count,
        },
        flush=True,
    )
    return _diagnosis_out(db, diagnosis)


@router.get("", response_model=list[DiagnosisHistoryItem])
def list_diagnoses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    diagnoses = (
        db.query(DiagnosisResult)
        .filter(DiagnosisResult.user_id == user.id)
        .order_by(DiagnosisResult.created_at.desc())
        .all()
    )
    return [
        DiagnosisHistoryItem(
            id=item.id,
            crop_type=item.crop_type,
            disease_name=item.disease_name,
            confidence=item.confidence,
            severity=item.severity,
            created_at=item.created_at,
            image_url=f"/uploads/{Path(item.image_upload.file_path).name}",
        )
        for item in diagnoses
    ]


@router.get("/{diagnosis_id}", response_model=DiagnosisOut)
def get_diagnosis(
    diagnosis_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    diagnosis = db.query(DiagnosisResult).filter(DiagnosisResult.id == diagnosis_id).first()
    if not diagnosis or diagnosis.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis not found")
    return _diagnosis_out(db, diagnosis)


async def _save_upload(db: Session, user: User, image: UploadFile) -> ImageUpload:
    # A generated filename prevents two uploads with the same original name from overwriting each other.
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    extension = ".png" if image.content_type == "image/png" else ".jpg"
    filename = f"{uuid4().hex}{extension}"
    file_path = Path(settings.upload_dir) / filename
    file_path.write_bytes(await image.read())

    upload = ImageUpload(
        user_id=user.id,
        filename=image.filename or filename,
        content_type=image.content_type,
        file_path=str(file_path),
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def _unknown_classifier_data() -> dict:
    return {
        "crop_type": "Unknown",
        "disease_name": "Unknown",
        "confidence": "Low",
        "severity": "Unknown",
        "description": "Unknown",
        "causes": "Unknown",
        "symptoms": "Unknown",
        "impact": "Unknown",
        "treatment_steps": "Unknown",
        "preventive_actions": "Unknown",
        "environmental_considerations": "Unknown",
        "tags": [],
    }


def _diagnosis_out(db: Session, diagnosis: DiagnosisResult) -> DiagnosisOut:
    recommendation_rows = (
        db.query(ProductRecommendation)
        .filter(ProductRecommendation.diagnosis_id == diagnosis.id)
        .all()
    )
    recommendations = [
        ProductRecommendationOut(
            id=item.id,
            product=item.product,
            reason=item.reason,
            usage_note=item.usage_note,
            safety_note=item.product.safety_notes,
        )
        for item in recommendation_rows
    ]
    return DiagnosisOut(
        id=diagnosis.id,
        crop_type=diagnosis.crop_type,
        disease_name=diagnosis.disease_name,
        confidence=diagnosis.confidence,
        severity=diagnosis.severity,
        description=diagnosis.description,
        causes=diagnosis.causes,
        symptoms=diagnosis.symptoms,
        impact=diagnosis.impact,
        treatment_steps=diagnosis.treatment_steps,
        preventive_actions=diagnosis.preventive_actions,
        environmental_considerations=diagnosis.environmental_considerations,
        created_at=diagnosis.created_at,
        image_url=f"/uploads/{Path(diagnosis.image_upload.file_path).name}",
        recommendations=recommendations,
    )
