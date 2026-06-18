import json
from pathlib import Path
from urllib.parse import quote

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import DatasetImage

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ANNOTATION_FILE = DATA_DIR / "crop_image_annotations.json"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}


def import_image_datasets(db: Session) -> None:
    _import_cropkeepai_annotations(db)
    _import_plantvillage_samples(db)
    db.commit()


def _import_cropkeepai_annotations(db: Session) -> None:
    root = Path(settings.cropkeepai_image_dataset_dir)
    if not root.exists() or not ANNOTATION_FILE.exists():
        return

    image_paths = [path for path in root.rglob("*") if path.is_file() and path.suffix in IMAGE_EXTENSIONS]
    file_lookup = {path.name: path for path in image_paths}
    stem_lookup = {path.stem: path for path in image_paths}
    rows = json.loads(ANNOTATION_FILE.read_text(encoding="utf-8-sig"))

    for row in rows:
        filename = _clean(row.get("Filename"))
        path = file_lookup.get(filename) or stem_lookup.get(filename)
        if not path:
            continue
        relative_path = path.relative_to(root).as_posix()
        _upsert_dataset_image(
            db,
            source="cropkeepai_annotation",
            filename=filename,
            relative_path=relative_path,
            image_url=f"/dataset-images/cropkeepai/{quote(relative_path)}",
            crop=_clean(row.get("Crop")),
            disease=_clean(row.get("Disease")),
            disease_type=_clean(row.get("Disease Type")),
            class_label=None,
        )


def _import_plantvillage_samples(db: Session) -> None:
    root = Path(settings.plantvillage_image_dataset_dir)
    if not root.exists():
        return

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in IMAGE_EXTENSIONS:
            continue
        relative_path = path.relative_to(root).as_posix()
        class_label = path.parent.name
        _upsert_dataset_image(
            db,
            source="plantvillage_sample",
            filename=path.name,
            relative_path=relative_path,
            image_url=f"/dataset-images/plantvillage/{quote(relative_path)}",
            crop=None,
            disease=None,
            disease_type=None,
            class_label=f"class_{class_label}",
        )


def _upsert_dataset_image(
    db: Session,
    source: str,
    filename: str,
    relative_path: str,
    image_url: str,
    crop: str | None,
    disease: str | None,
    disease_type: str | None,
    class_label: str | None,
) -> None:
    existing = (
        db.query(DatasetImage)
        .filter(DatasetImage.source == source, DatasetImage.relative_path == relative_path)
        .first()
    )
    payload = {
        "source": source,
        "filename": filename,
        "relative_path": relative_path,
        "image_url": image_url,
        "crop": crop,
        "disease": disease,
        "disease_type": disease_type,
        "class_label": class_label,
    }
    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
    else:
        db.add(DatasetImage(**payload))


def _clean(value) -> str:
    if value is None:
        return ""
    return str(value).strip()
