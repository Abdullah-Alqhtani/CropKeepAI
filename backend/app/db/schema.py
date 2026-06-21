from sqlalchemy import text

from app.db.session import engine


def ensure_schema() -> None:
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS product_code VARCHAR(80)",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS english_name VARCHAR(180)",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS product_type VARCHAR(120)",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS crops TEXT",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS specification VARCHAR(180)",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS source VARCHAR(180)",
        "ALTER TABLE products ALTER COLUMN target_disease TYPE TEXT",
        "ALTER TABLE products ALTER COLUMN tags TYPE TEXT",
        "CREATE INDEX IF NOT EXISTS ix_products_product_code ON products (product_code)",
        """
        CREATE TABLE IF NOT EXISTS dataset_images (
            id SERIAL PRIMARY KEY,
            source VARCHAR(80) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            relative_path VARCHAR(600) NOT NULL,
            image_url VARCHAR(700) NOT NULL,
            crop VARCHAR(160),
            disease VARCHAR(180),
            disease_type VARCHAR(160),
            class_label VARCHAR(180),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_dataset_image_source_path UNIQUE (source, relative_path)
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_dataset_images_source ON dataset_images (source)",
        "CREATE INDEX IF NOT EXISTS ix_dataset_images_crop ON dataset_images (crop)",
        "CREATE INDEX IF NOT EXISTS ix_dataset_images_disease ON dataset_images (disease)",
        "UPDATE dataset_images SET source = 'cropkeepai_annotation' WHERE source = 'agromind_annotation'",
        "UPDATE dataset_images SET image_url = REPLACE(image_url, '/dataset-images/agromind/', '/dataset-images/cropkeepai/') WHERE image_url LIKE '/dataset-images/agromind/%'",
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
