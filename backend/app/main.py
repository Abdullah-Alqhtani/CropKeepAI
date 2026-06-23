"""Start and configure the CropKeepAI FastAPI application.

This module connects routes, CORS, database setup, seed data, and static image
folders before the API begins accepting requests.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api import auth, diagnosis, chat, catalog
from app.core.config import settings
from app.db.schema import ensure_schema
from app.db.session import Base, engine
from app.db.seed import seed_database

app = FastAPI(title="CropKeepAI API", version="1.0.0")


def _allowed_origins() -> list[str]:
    # Production may have more than one frontend URL, so accept a comma-separated allowlist.
    origins = [origin.strip().rstrip("/") for origin in settings.frontend_origin.split(",") if origin.strip()]
    if "*" in origins:
        raise RuntimeError("FRONTEND_ORIGIN cannot include '*' when CORS credentials are enabled.")
    return origins


allowed_origins = _allowed_origins()
print(f"CORS allowed origins: {allowed_origins}", flush=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create missing tables first, then add the initial reference data and default admin.
Base.metadata.create_all(bind=engine)
ensure_schema()
seed_database()

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

if Path(settings.cropkeepai_image_dataset_dir).exists():
    app.mount(
        "/dataset-images/cropkeepai",
        StaticFiles(directory=settings.cropkeepai_image_dataset_dir),
        name="cropkeepai_dataset_images",
    )

if Path(settings.plantvillage_image_dataset_dir).exists():
    app.mount(
        "/dataset-images/plantvillage",
        StaticFiles(directory=settings.plantvillage_image_dataset_dir),
        name="plantvillage_dataset_images",
    )

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(diagnosis.router, prefix="/api/diagnoses", tags=["diagnoses"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(catalog.router, prefix="/api/catalog", tags=["catalog"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
