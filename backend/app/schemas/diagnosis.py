from datetime import datetime

from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    product_code: str | None = None
    name: str
    english_name: str | None = None
    product_type: str | None = None
    active_ingredient: str
    usage_instructions: str
    target_disease: str
    safety_notes: str
    tags: str
    crops: str | None = None
    specification: str | None = None
    source: str | None = None

    class Config:
        from_attributes = True


class ProductRecommendationOut(BaseModel):
    id: int
    product_id: int | None = None
    product_name: str | None = None
    score: float | None = None
    reason: str
    usage_note: str
    safety_note: str
    product: ProductOut

    class Config:
        from_attributes = True


class DiagnosisOut(BaseModel):
    id: int
    crop_type: str
    disease_name: str
    confidence: str
    severity: str
    description: str
    causes: str
    symptoms: str
    impact: str
    treatment_steps: str
    preventive_actions: str
    environmental_considerations: str
    created_at: datetime
    image_url: str
    recommendations: list[ProductRecommendationOut]


class DiagnosisHistoryItem(BaseModel):
    id: int
    crop_type: str
    disease_name: str
    confidence: str
    severity: str
    created_at: datetime
    image_url: str
