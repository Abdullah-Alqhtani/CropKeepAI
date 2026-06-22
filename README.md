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

## Default Admin Account

Public demo credentials are not hardcoded in the repository.

The first admin account is created from backend environment variables:

```text
DEFAULT_ADMIN_EMAIL=your-admin-email@example.com
DEFAULT_ADMIN_PASSWORD=your-secure-admin-password
```

For local development, set these values in `backend/.env`.

For production, `DEFAULT_ADMIN_EMAIL` and `DEFAULT_ADMIN_PASSWORD` must be configured before startup. If `APP_ENV=production` and the default admin password is missing, the backend fails startup with a clear error.

After the first admin login, create farmer and expert users from the Admin User Management page.

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

Configure the default admin account in `backend/.env`:

```text
DEFAULT_ADMIN_EMAIL=your-admin-email@example.com
DEFAULT_ADMIN_PASSWORD=your-secure-admin-password
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

## Deploy On Railway

Deploy the backend, frontend, and PostgreSQL database as three Railway services.

1. Create a Railway project from this GitHub repository.
2. Add a PostgreSQL service named `Postgres`.
3. Add a backend service from this repository. In its **Build** settings, set the root directory to `backend`, then generate a public domain under **Networking**.
4. Add a frontend service from this repository. In its **Build** settings, set the root directory to `frontend`, then generate a public domain.
5. Set these backend variables:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
APP_ENV=production
JWT_SECRET=<long-random-secret>
JWT_EXPIRE_MINUTES=1440
GROQ_API_KEY=<your-groq-api-key>
GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
GROQ_TEXT_MODEL=llama-3.3-70b-versatile
DEFAULT_ADMIN_EMAIL=<admin-email>
DEFAULT_ADMIN_PASSWORD=<strong-admin-password>
FRONTEND_ORIGIN=https://<frontend-domain>
UPLOAD_DIR=uploads
```

6. Set `VITE_API_BASE_URL=https://<backend-domain>` for the frontend as a Railway Docker build argument. The Vite build embeds this public API URL into the production frontend bundle.
7. Deploy both services. Railway supplies `PORT` automatically; the backend listens on it, and the frontend serves its built `dist` directory on it.

Do not add the local dataset-path variables from `backend/.env.example` to Railway. The mounted local datasets used by Docker Compose are unavailable on Railway; dataset importing is skipped when those directories are absent. Uploaded images are stored locally by default, so add a Railway Volume or use object storage if uploads must persist through redeployments.

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
