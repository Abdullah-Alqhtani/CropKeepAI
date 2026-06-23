"""Load typed application settings from environment variables.

This file keeps configuration in one place so the API, database, and services use
the same values without hard-coding deployment-specific details.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Required connection and signing settings are supplied by the deployment environment.
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

    # A local .env file is convenient for development; deployed platforms use real environment variables.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Create one shared settings object for the rest of the backend.
settings = Settings()
