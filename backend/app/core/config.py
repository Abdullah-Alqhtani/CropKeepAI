from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_expire_minutes: int = 1440
    app_env: str = "development"
    groq_api_key: str = ""
    groq_vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    groq_text_model: str = "llama-3.3-70b-versatile"
    default_admin_email: str = ""
    default_admin_password: str = ""
    upload_dir: str = "uploads"
    frontend_origin: str = "http://localhost:5173"
    cropkeepai_image_dataset_dir: str = "/datasets/cropkeepai-crop"
    plantvillage_image_dataset_dir: str = "/datasets/plantvillage"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
