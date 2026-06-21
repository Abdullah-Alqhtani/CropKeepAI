from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class UserRole(str, Enum):
    farmer = "farmer"
    expert = "expert"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.farmer)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CropType(Base):
    __tablename__ = "crop_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)


class Disease(Base):
    __tablename__ = "diseases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crop_type_id: Mapped[int] = mapped_column(ForeignKey("crop_types.id"))
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    causes: Mapped[str] = mapped_column(Text)
    symptoms: Mapped[str] = mapped_column(Text)
    impact: Mapped[str] = mapped_column(Text)

    crop_type: Mapped[CropType] = relationship()


class KnowledgeBaseEntry(Base):
    __tablename__ = "knowledge_base_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    disease_id: Mapped[int] = mapped_column(ForeignKey("diseases.id"))
    title: Mapped[str] = mapped_column(String(180))
    content: Mapped[str] = mapped_column(Text)
    tags: Mapped[str] = mapped_column(String(300), default="")

    disease: Mapped[Disease] = relationship()


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(180))
    english_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    active_ingredient: Mapped[str] = mapped_column(String(180))
    usage_instructions: Mapped[str] = mapped_column(Text)
    target_disease: Mapped[str] = mapped_column(Text)
    safety_notes: Mapped[str] = mapped_column(Text)
    tags: Mapped[str] = mapped_column(Text, default="")
    crops: Mapped[str | None] = mapped_column(Text, nullable=True)
    specification: Mapped[str | None] = mapped_column(String(180), nullable=True)
    source: Mapped[str | None] = mapped_column(String(180), nullable=True)


class DiseaseProductMapping(Base):
    __tablename__ = "disease_product_mappings"
    __table_args__ = (UniqueConstraint("disease_id", "product_id", name="uq_disease_product"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    disease_id: Mapped[int] = mapped_column(ForeignKey("diseases.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    match_reason: Mapped[str] = mapped_column(Text)

    disease: Mapped[Disease] = relationship()
    product: Mapped[Product] = relationship()


class ImageUpload(Base):
    __tablename__ = "image_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(80))
    file_path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DiagnosisResult(Base):
    __tablename__ = "diagnosis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    image_upload_id: Mapped[int] = mapped_column(ForeignKey("image_uploads.id"))
    crop_type: Mapped[str] = mapped_column(String(120))
    disease_name: Mapped[str] = mapped_column(String(160))
    confidence: Mapped[str] = mapped_column(String(40), default="Medium")
    severity: Mapped[str] = mapped_column(String(40), default="Unknown")
    description: Mapped[str] = mapped_column(Text)
    causes: Mapped[str] = mapped_column(Text)
    symptoms: Mapped[str] = mapped_column(Text)
    impact: Mapped[str] = mapped_column(Text)
    treatment_steps: Mapped[str] = mapped_column(Text)
    preventive_actions: Mapped[str] = mapped_column(Text)
    environmental_considerations: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    image_upload: Mapped[ImageUpload] = relationship()


class ProductRecommendation(Base):
    __tablename__ = "product_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    diagnosis_id: Mapped[int] = mapped_column(ForeignKey("diagnosis_results.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    score: Mapped[float] = mapped_column(Float, default=1.0)
    reason: Mapped[str] = mapped_column(Text)

    product: Mapped[Product] = relationship()

    @property
    def usage_note(self) -> str:
        return self.product.usage_instructions if self.product else ""


class DatasetImage(Base):
    __tablename__ = "dataset_images"
    __table_args__ = (UniqueConstraint("source", "relative_path", name="uq_dataset_image_source_path"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(80), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    relative_path: Mapped[str] = mapped_column(String(600))
    image_url: Mapped[str] = mapped_column(String(700))
    crop: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    disease: Mapped[str | None] = mapped_column(String(180), nullable=True, index=True)
    disease_type: Mapped[str | None] = mapped_column(String(160), nullable=True)
    class_label: Mapped[str | None] = mapped_column(String(180), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    diagnosis_id: Mapped[int] = mapped_column(ForeignKey("diagnosis_results.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
