# CropKeepAI

AI crop disease diagnosis and crop protection recommendation platform.

## Stack

- Frontend: React + Vite
- Backend: FastAPI
- Database: PostgreSQL
- AI: Groq API key through backend environment variables

## Project Structure

```text
backend/
  app/
    api/          FastAPI route modules
    core/         settings and security helpers
    db/           database session and seed data
    models/       SQLAlchemy entities
    schemas/      Pydantic request/response models
    services/     AI, RAG, recommendation, and auth logic
frontend/
  src/
    components/   Reusable UI components
    pages/        Main app screens
    services/     API client
```

## Run With Docker

1. Copy environment files:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

2. Add your Groq key to `backend/.env`:

```text
GROQ_API_KEY=your_api_key_here
```

3. Start the app:

```bash
docker compose up --build
```

4. Open:

- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs

## Default Demo Users

The database is seeded on backend startup.

| Email | Password | Role |
| --- | --- | --- |
| farmer@cropkeepai.local | password123 | farmer |
| expert@cropkeepai.local | password123 | expert |
| admin@cropkeepai.local | password123 | admin |

## Notes

- Upload supports JPG and PNG.
- Diagnosis uses Groq when `GROQ_API_KEY` is configured.
- RAG is implemented over PostgreSQL knowledge-base entries using keyword relevance, keeping the MVP simple while still separated behind a service.
- Product recommendations are rule/tag based through disease-product mappings.
- Product catalog data is imported from JSON files in `backend/app/data/`, generated from the provided Excel catalogs.
- Image training/test metadata is imported from `backend/app/data/crop_image_annotations.json`; the image folders are mounted read-only in Docker under `/datasets`.

## Dataset Endpoints

Expert/admin users can inspect indexed image samples:

- `GET /api/catalog/dataset-images/stats`
- `GET /api/catalog/dataset-images?source=cropkeepai_annotation&limit=100`
- `GET /api/catalog/dataset-images?source=plantvillage_sample&limit=100`

The current image integration indexes labeled images for testing, evaluation, and future CV training workflows. The MVP uses Groq's OpenAI-compatible API endpoint for diagnosis.

## Chat Style Data

Chat behavior examples are imported into `backend/app/data/chat_examples.json` from the provided fine-tuning files. The backend retrieves relevant examples for each follow-up chat request and uses them as response-style guidance.

- `GET /api/catalog/chat-examples/stats`
