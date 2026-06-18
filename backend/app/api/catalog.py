from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import DatasetImage, Disease, KnowledgeBaseEntry, Product, User
from app.schemas.catalog import ChatExampleStats, DatasetImageOut, DatasetImageStats, DiseaseOut, KnowledgeEntryOut, ProductOut
from app.services.auth_service import require_roles
from app.services.chat_example_service import chat_example_stats

router = APIRouter()


@router.get("/diseases", response_model=list[DiseaseOut])
def diseases(db: Session = Depends(get_db), _: User = Depends(require_roles("admin", "expert"))):
    records = db.query(Disease).all()
    return [
        DiseaseOut(id=item.id, crop_type=item.crop_type.name, name=item.name, description=item.description)
        for item in records
    ]


@router.get("/knowledge", response_model=list[KnowledgeEntryOut])
def knowledge(db: Session = Depends(get_db), _: User = Depends(require_roles("admin", "expert"))):
    records = db.query(KnowledgeBaseEntry).all()
    return [
        KnowledgeEntryOut(
            id=item.id,
            disease=item.disease.name,
            title=item.title,
            content=item.content,
            tags=item.tags,
        )
        for item in records
    ]


@router.get("/products", response_model=list[ProductOut])
def products(db: Session = Depends(get_db), _: User = Depends(require_roles("admin", "expert", "farmer"))):
    return db.query(Product).all()


@router.get("/dataset-images", response_model=list[DatasetImageOut])
def dataset_images(
    source: str | None = None,
    crop: str | None = None,
    disease: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "expert")),
):
    query = db.query(DatasetImage)
    if source:
        query = query.filter(DatasetImage.source == source)
    if crop:
        query = query.filter(DatasetImage.crop.ilike(f"%{crop}%"))
    if disease:
        query = query.filter(DatasetImage.disease.ilike(f"%{disease}%"))
    return query.order_by(DatasetImage.id).limit(min(limit, 500)).all()


@router.get("/dataset-images/stats", response_model=DatasetImageStats)
def dataset_image_stats(db: Session = Depends(get_db), _: User = Depends(require_roles("admin", "expert"))):
    records = db.query(DatasetImage).all()
    by_source: dict[str, int] = {}
    by_disease: dict[str, int] = {}
    for record in records:
        by_source[record.source] = by_source.get(record.source, 0) + 1
        label = record.disease or record.class_label or "unlabeled"
        by_disease[label] = by_disease.get(label, 0) + 1
    return DatasetImageStats(total=len(records), by_source=by_source, by_disease=by_disease)


@router.get("/chat-examples/stats", response_model=ChatExampleStats)
def chat_examples_stats(_: User = Depends(require_roles("admin", "expert"))):
    return chat_example_stats()
