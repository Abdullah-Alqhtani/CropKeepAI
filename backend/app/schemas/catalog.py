from pydantic import BaseModel


class DiseaseOut(BaseModel):
    id: int
    crop_type: str
    name: str
    description: str


class KnowledgeEntryOut(BaseModel):
    id: int
    disease: str
    title: str
    content: str
    tags: str


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


class DatasetImageOut(BaseModel):
    id: int
    source: str
    filename: str
    image_url: str
    crop: str | None = None
    disease: str | None = None
    disease_type: str | None = None
    class_label: str | None = None

    class Config:
        from_attributes = True


class DatasetImageStats(BaseModel):
    total: int
    by_source: dict[str, int]
    by_disease: dict[str, int]


class ChatExampleStats(BaseModel):
    total: int
    by_source: dict[str, int]
    by_type: dict[str, int]
