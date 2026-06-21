# CropKeep AI

CropKeep AI is a full-stack smart agriculture platform for crop disease diagnosis and crop protection recommendations.

Users upload a plant image, the backend classifies the crop and disease, then the system matches the result with database disease records, knowledge-base entries, and product mappings to return treatment steps, prevention guidance, environmental advice, and catalog-based product recommendations.

The application is built for a crop support workflow where users, experts, and admins can work with diagnosis history, product catalog data, and controlled user accounts.

## Features

- Image-based crop disease diagnosis
- AI-assisted crop, disease, symptom, confidence, and tag detection
- Database-backed disease matching
- Treatment and prevention recommendations from stored disease knowledge
- Product recommendations from the existing product catalog
- Fallback recommendations when the disease cannot be confidently identified
- Diagnosis history
- Product catalog
- Chat support for follow-up questions
- JWT authentication
- Admin-controlled user management
- Role-based access control
- Docker Compose deployment

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite |
| Backend | FastAPI, Python |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Authentication | JWT |
| AI Classifier | Groq API |
| Deployment | Docker, Docker Compose |

## Project Structure

```text
backend/
  app/
    api/          FastAPI route modules
    core/         settings and security helpers
    data/         seed/catalog/demo data
    db/           database session, schema, and seed logic
    models/       SQLAlchemy models
    schemas/      Pydantic request and response schemas
    services/     AI, auth, treatment, recommendation, and chat logic

frontend/
  src/
    components/   Reusable UI components
    pages/        Main application pages
    services/     API client logic
```

## Main Backend Flow

1. A user uploads a JPG or PNG plant image.
2. Groq is used only to classify the image and return:
   - crop
   - disease
   - symptoms
   - confidence
   - tags
3. The backend normalizes the detected disease name.
4. The backend searches the database for a matching disease using:
   - exact disease name
   - normalized disease name
   - fuzzy matching
   - symptom overlap
   - tag overlap
   - crop and symptom matching
   - knowledge-base text
   - product target disease and tags
5. If a disease is matched:
   - disease description, causes, symptoms, and impact come from the database
   - treatment and prevention come from knowledge-base entries
   - product recommendations come from disease-product mappings
6. If no disease is confidently matched:
   - the system returns general plant-care treatment
   - the system returns general prevention and environment guidance
   - the system recommends safe general products from the existing catalog

The backend does not invent product names. Product recommendations are selected only from products already stored in the database.

## Recommendation Behavior

CropKeep AI uses database-driven recommendations instead of generating treatment and product recommendations freely from AI.

If the disease is matched, the system uses disease-specific data:

- disease description
- causes
- symptoms
- impact
- treatment steps
- preventive actions
- environmental considerations
- mapped catalog products

If the disease is unknown or low confidence, the system still provides useful general guidance:

- remove heavily affected leaves if safe
- isolate affected plants
- avoid overhead watering
- improve airflow
- monitor symptoms for 48 to 72 hours
- consult an agricultural expert if symptoms spread

The product fallback chooses products from the catalog and prefers products tagged as:

- general
- fungal
- leaf spot
- preventive
- broad-spectrum

## Authentication And Roles

Public self-registration is disabled. Account creation is controlled by admins only.

Supported roles:

- `admin`
- `farmer`
- `expert`

Admins can:

- create user accounts
- set email, name, password, and role
- enable or disable users
- delete users
- reset passwords
- change user roles

Disabled users cannot log in. Non-admin users cannot access the User Management page or admin-only API routes.

## Default Demo Accounts

The database seed creates demo users for local development.

| Email | Password | Role |
| --- | --- | --- |
| admin@cropkeepai.local | password123 | admin |
| farmer@cropkeepai.local | password123 | farmer |
| expert@cropkeepai.local | password123 | expert |

Change these passwords before using the app outside local demo or development.

## Environment Variables

Create local environment files from the examples:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Add your Groq API key to `backend/.env`:

```text
GROQ_API_KEY=your_api_key_here
```

Do not commit `.env` files. They are ignored by Git.

## Run With Docker

From the project root:

```bash
docker compose up --build
```

Open the app:

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs

To stop the app:

```bash
docker compose down
```

## Local Backend Compile Check

To check backend syntax:

```bash
python -m compileall backend/app
```

## Database Seed Data

The app seeds demo data for local development, including:

- users
- diseases
- knowledge-base treatment entries
- product catalog records
- disease-product mappings
- chat examples
- image metadata

Example diseases:

- Tomato Early Blight
- Potato Late Blight
- Rice Blast
- Wheat Rust
- Cucumber Powdery Mildew

Example products:

- BlightGuard SC
- CopperShield 77
- RiceSafe BlastCare
- RustStop Pro
- MildewAway Bio

## Dataset And Catalog Endpoints

Expert and admin users can inspect indexed dataset records:

```text
GET /api/catalog/dataset-images/stats
GET /api/catalog/dataset-images?source=cropkeepai_annotation&limit=100
GET /api/catalog/dataset-images?source=plantvillage_sample&limit=100
GET /api/catalog/chat-examples/stats
```

## Security Notes

The project `.gitignore` is configured to avoid committing local and sensitive files, including:

- `.env` files
- backend and frontend environment files
- Python cache files
- virtual environments
- `node_modules`
- VS Code settings
- logs
- local database files
- operating system files

Passwords are hashed before storage. API keys must stay in local environment files and should never be committed to GitHub.

## Recent Improvements

This version includes several important updates:

- removed public account registration
- added admin-only user management
- added user activation and disabling
- added role-based access control
- kept JWT authentication working
- improved disease matching with normalization and fuzzy matching
- moved treatment and prevention recommendations to database-backed logic
- fixed product recommendations so they are created after diagnosis
- added fallback treatment and catalog product recommendations
- added backend logs for diagnosis matching and product recommendation counts
- verified Docker Compose startup for backend, frontend, and PostgreSQL

## License

This project is intended for educational and demo purposes.
