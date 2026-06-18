from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import CropType, DiagnosisResult, Disease, ImageUpload, ProductRecommendation, User
from app.schemas.diagnosis import DiagnosisHistoryItem, DiagnosisOut
from app.services.ai_service import diagnose_crop_image
from app.services.auth_service import get_current_user
from app.services.rag_service import build_knowledge_context, retrieve_knowledge
from app.services.recommendation_service import create_product_recommendations
from app.services.treatment_service import refine_treatment

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

    try:
        diagnosis_data = diagnose_crop_image(str(file_path), image.content_type, "No crop or disease has been detected yet.")
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    tags = diagnosis_data.pop("tags", [])
    print(
        "Initial diagnosis detected:",
        {
            "crop": diagnosis_data["crop_type"],
            "disease": diagnosis_data["disease_name"],
            "confidence": diagnosis_data["confidence"],
            "symptoms": diagnosis_data["symptoms"],
            "tags": tags,
        },
        flush=True,
    )
    entries = retrieve_knowledge(
        db,
        diagnosis_data["crop_type"],
        diagnosis_data["disease_name"],
        diagnosis_data["symptoms"],
        tags,
    )
    try:
        diagnosis_data = diagnose_crop_image(str(file_path), image.content_type, build_knowledge_context(entries))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    tags = diagnosis_data.pop("tags", tags)
    entries = retrieve_knowledge(
        db,
        diagnosis_data["crop_type"],
        diagnosis_data["disease_name"],
        diagnosis_data["symptoms"],
        tags,
    )
    disease = _find_disease(db, diagnosis_data["crop_type"], diagnosis_data["disease_name"])
    diagnosis_data["tags"] = tags
    diagnosis_data = refine_treatment(diagnosis_data, disease, entries)
    diagnosis_data.pop("tags", None)

    diagnosis = DiagnosisResult(
        user_id=user.id,
        image_upload_id=upload.id,
        **diagnosis_data,
    )
    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)

    create_product_recommendations(db, diagnosis.id, diagnosis.crop_type, diagnosis.disease_name, diagnosis.symptoms, tags)
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


def _diagnosis_out(db: Session, diagnosis: DiagnosisResult) -> DiagnosisOut:
    recommendations = (
        db.query(ProductRecommendation)
        .filter(ProductRecommendation.diagnosis_id == diagnosis.id)
        .all()
    )
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


def _find_disease(db: Session, crop_type: str, disease_name: str) -> Disease | None:
    if not crop_type or not disease_name or crop_type == "Unknown" or disease_name == "Unknown":
        return None
    disease = (
        db.query(Disease)
        .join(Disease.crop_type)
        .filter(Disease.name.ilike(f"%{disease_name}%"), CropType.name.ilike(crop_type))
        .first()
    )
    return disease or db.query(Disease).filter(Disease.name.ilike(f"%{disease_name}%")).first()
