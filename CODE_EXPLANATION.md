# Code Explanation

This document explains the main diagnosis, treatment, and recommendation code in CropKeep AI.

It is written for project review, GitHub, and presentation use. Instead of adding comments to every source line, the explanation is kept here so the production code stays clean.

## `backend/app/api/diagnosis.py`

This file contains the API routes for creating, listing, and viewing crop diagnosis results.

### Imports

```python
from pathlib import Path
```

Imports `Path`, which is used to work with file paths safely, especially uploaded image paths.

```python
from uuid import uuid4
```

Imports `uuid4`, which is used to generate unique filenames for uploaded images.

```python
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
```

Imports FastAPI tools:

- `APIRouter` creates the diagnosis route group.
- `Depends` injects dependencies like the database session and current user.
- `File` declares file upload input.
- `HTTPException` returns API errors.
- `UploadFile` represents the uploaded image.
- `status` provides HTTP status constants.

```python
from sqlalchemy.orm import Session
```

Imports SQLAlchemy `Session`, used for database queries and commits.

```python
from app.core.config import settings
```

Imports app settings, including the upload directory.

```python
from app.db.session import get_db
```

Imports the database dependency used by FastAPI routes.

```python
from app.models import DiagnosisResult, ImageUpload, ProductRecommendation, User
```

Imports database models used by this API:

- `DiagnosisResult` stores diagnosis output.
- `ImageUpload` stores uploaded image metadata.
- `ProductRecommendation` stores product recommendations for a diagnosis.
- `User` represents the authenticated user.

```python
from app.schemas.diagnosis import DiagnosisHistoryItem, DiagnosisOut, ProductRecommendationOut
```

Imports response schemas used to shape API responses.

```python
from app.services.ai_service import diagnose_crop_image
```

Imports the Groq image classifier function.

```python
from app.services.auth_service import get_current_user
```

Imports the JWT authentication dependency.

```python
from app.services.recommendation_service import create_product_recommendations
```

Imports the function that creates database `ProductRecommendation` rows.

```python
from app.services.treatment_service import (
    build_database_diagnosis,
    knowledge_for_disease,
    match_database_disease,
)
```

Imports treatment and disease matching helpers:

- `match_database_disease` matches AI output to database diseases.
- `knowledge_for_disease` loads treatment/prevention knowledge entries.
- `build_database_diagnosis` builds the final diagnosis response data.

### Router Setup

```python
router = APIRouter()
```

Creates the FastAPI router for diagnosis endpoints.

```python
ALLOWED_TYPES = {"image/jpeg", "image/png"}
```

Allows only JPG and PNG uploads.

### Create Diagnosis Endpoint

```python
@router.post("", response_model=DiagnosisOut)
```

Defines the POST diagnosis endpoint and declares that it returns `DiagnosisOut`.

```python
async def create_diagnosis(...)
```

Creates a new diagnosis from an uploaded image.

```python
image: UploadFile = File(...)
```

Requires the request to include an uploaded image file.

```python
db: Session = Depends(get_db)
```

Injects a database session.

```python
user: User = Depends(get_current_user)
```

Requires the request to be authenticated with a valid JWT.

```python
if image.content_type not in ALLOWED_TYPES:
```

Checks whether the uploaded file is JPG or PNG.

```python
raise HTTPException(...)
```

Rejects unsupported file types with a clear API error.

```python
upload = await _save_upload(db, user, image)
```

Saves the image to disk and stores its metadata in the database.

```python
try:
    classifier_data = diagnose_crop_image(...)
```

Attempts to call Groq to classify the uploaded image.

```python
"No treatment or product knowledge is provided..."
```

This prompt tells Groq to identify only crop, disease, symptoms, confidence, and tags. Treatment and products come from the database, not from Groq.

```python
except RuntimeError as exc:
```

Handles Groq failures without stopping the diagnosis flow.

```python
print("Groq diagnosis unavailable...", ...)
```

Logs the AI failure in the backend only.

```python
classifier_data = _unknown_classifier_data()
```

Uses safe unknown classifier data so the database fallback can still run.

```python
tags = classifier_data.pop("tags", [])
```

Removes tags from the classifier data and keeps them separately for matching/recommendations.

```python
detected_crop = classifier_data.get("crop_type", "Unknown")
```

Reads the crop detected by the AI.

```python
detected_disease = classifier_data.get("disease_name", "Unknown")
```

Reads the disease detected by the AI.

```python
detected_symptoms = classifier_data.get("symptoms", "")
```

Reads symptoms detected by the AI.

```python
matched_disease, normalized_disease, fuzzy_match_score = match_database_disease(...)
```

Attempts to match the AI result to a disease stored in the database.

```python
print("Database disease matching:", ...)
```

Logs diagnosis matching details for debugging:

- Groq disease
- Groq confidence
- detected crop
- detected disease
- normalized disease
- fuzzy match score
- matched database disease
- symptoms
- tags

```python
entries = knowledge_for_disease(db, matched_disease)
```

Loads treatment and prevention knowledge entries for the matched disease.

```python
print("Database knowledge entries:", ...)
```

Logs which knowledge entries were retrieved.

```python
diagnosis_data = build_database_diagnosis(...)
```

Builds the final diagnosis fields from database disease data or fallback general guidance.

```python
diagnosis = DiagnosisResult(...)
```

Creates a database diagnosis record.

```python
db.add(diagnosis)
db.commit()
db.refresh(diagnosis)
```

Saves the diagnosis and refreshes it so generated fields like `id` are available.

```python
recommendations = create_product_recommendations(db, diagnosis, tags)
```

Creates product recommendation rows for the diagnosis.

```python
products_created_count = (...)
```

Counts how many `ProductRecommendation` rows were created.

```python
print("Diagnosis recommendation summary:", ...)
```

Logs the final recommendation summary, including `products_created_count`.

```python
return _diagnosis_out(db, diagnosis)
```

Returns the complete diagnosis response to the frontend.

### List Diagnosis History

```python
@router.get("", response_model=list[DiagnosisHistoryItem])
```

Defines the endpoint for listing the current user's diagnosis history.

```python
diagnoses = db.query(DiagnosisResult)...
```

Loads diagnosis records that belong only to the authenticated user.

```python
.order_by(DiagnosisResult.created_at.desc())
```

Shows the newest diagnoses first.

```python
return [...]
```

Converts database rows into `DiagnosisHistoryItem` response objects.

### Get One Diagnosis

```python
@router.get("/{diagnosis_id}", response_model=DiagnosisOut)
```

Defines the endpoint for retrieving one diagnosis by ID.

```python
diagnosis = db.query(DiagnosisResult)...
```

Finds the diagnosis record.

```python
if not diagnosis or diagnosis.user_id != user.id:
```

Prevents users from viewing diagnoses that do not belong to them.

```python
raise HTTPException(...)
```

Returns `404` when the diagnosis does not exist or belongs to another user.

```python
return _diagnosis_out(db, diagnosis)
```

Returns the complete diagnosis response.

### Save Upload Helper

```python
async def _save_upload(...)
```

Saves the uploaded image file and creates an `ImageUpload` database row.

```python
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
```

Creates the upload directory if it does not already exist.

```python
extension = ".png" if image.content_type == "image/png" else ".jpg"
```

Chooses the file extension based on the uploaded image type.

```python
filename = f"{uuid4().hex}{extension}"
```

Creates a unique filename.

```python
file_path = Path(settings.upload_dir) / filename
```

Builds the full path for the saved file.

```python
file_path.write_bytes(await image.read())
```

Reads the uploaded file and writes it to disk.

```python
upload = ImageUpload(...)
```

Creates the database record for the uploaded file.

```python
db.add(upload)
db.commit()
db.refresh(upload)
```

Saves the upload record and refreshes it.

```python
return upload
```

Returns the saved upload record.

### Unknown Classifier Data

```python
def _unknown_classifier_data() -> dict:
```

Creates fallback classifier data when Groq fails.

```python
"crop_type": "Unknown"
```

Marks the crop as unknown.

```python
"disease_name": "Unknown"
```

Marks the disease as unknown.

```python
"confidence": "Low"
```

Marks the diagnosis confidence as low.

```python
"tags": []
```

Returns an empty tag list when no AI tags are available.

### Diagnosis Output Helper

```python
def _diagnosis_out(...)
```

Builds the API response object for one diagnosis.

```python
recommendation_rows = db.query(ProductRecommendation)...
```

Loads all product recommendations linked to this diagnosis.

```python
recommendations = [...]
```

Converts recommendation database rows into API response objects.

```python
safety_note=item.product.safety_notes
```

Uses the product catalog safety notes in the recommendation output.

```python
return DiagnosisOut(...)
```

Returns the final response with diagnosis details, image URL, and recommendations.

## `backend/app/services/treatment_service.py`

This file matches detected diseases to database diseases and builds treatment output.

### Purpose

The treatment service keeps treatment logic database-driven. Groq does not create treatment text. If a disease is matched, treatment comes from database records. If no disease is matched, the service returns safe general plant-care guidance.

### Main Constants

```python
UNKNOWN_DESCRIPTION
```

User-friendly message shown when the disease cannot be confidently identified.

```python
UNKNOWN_TREATMENT
```

General treatment steps used for unknown diagnoses.

```python
UNKNOWN_PREVENTION
```

General prevention steps used for unknown diagnoses.

```python
UNKNOWN_ENVIRONMENT
```

General environmental advice used for unknown diagnoses.

### `normalize_disease_name`

This function prepares disease names for matching.

It:

- converts text to lowercase
- removes punctuation
- removes generic words like `disease`, `plant`, `crop`, `leaf`, and `leaves`
- removes crop words from the disease name
- trims extra spaces

This helps match names like `Tomato Early Blight`, `early-blight`, and `Early blight disease`.

### `match_database_disease`

This function tries to match Groq output to a disease in the database.

It receives:

- database session
- detected crop
- detected disease
- detected symptoms
- detected tags

The matching process:

1. Normalize the detected disease.
2. Load all diseases from the database.
3. Try exact normalized matching.
4. If exact matching fails, calculate fuzzy scores.
5. Compare disease name similarity.
6. Compare symptom and tag overlap.
7. Add score when the crop matches.
8. Log candidate scores.
9. Return the best disease if the score is strong enough.
10. Return `None` if no reliable match is found.

### `knowledge_for_disease`

This function loads treatment and prevention knowledge entries for a matched disease.

If no disease is matched, it returns an empty list.

### `build_database_diagnosis`

This function builds the final diagnosis data saved to the database.

If no disease is matched:

- crop comes from the classifier if available
- disease is set to `Unknown`
- confidence is set to `Low`
- description uses `UNKNOWN_DESCRIPTION`
- treatment uses `UNKNOWN_TREATMENT`
- prevention uses `UNKNOWN_PREVENTION`
- environment uses `UNKNOWN_ENVIRONMENT`

If a disease is matched:

- crop comes from the matched database disease
- disease name comes from the database
- description comes from the database
- causes come from the database
- symptoms come from the database
- impact comes from the database
- treatment comes from knowledge-base entries
- prevention comes from knowledge-base entries
- environment uses safety and label guidance

### Helper Functions

```python
_database_terms
```

Collects searchable terms from:

- disease name
- crop name
- disease description
- causes
- symptoms
- impact
- knowledge entries
- mapped products

```python
_treatment_and_prevention_from_entries
```

Splits knowledge-base entries into treatment and prevention items.

```python
_is_prevention_entry
```

Detects whether a knowledge entry is prevention-related.

```python
_split_items
```

Splits stored knowledge text into clean recommendation items.

```python
_dedupe
```

Removes duplicate treatment or prevention items.

```python
_terms
```

Extracts useful searchable keywords from text.

```python
_overlap_score
```

Calculates keyword overlap between two sets of terms.

```python
_log_treatment_output
```

Logs the final treatment and prevention output for backend debugging.

## `backend/app/services/recommendation_service.py`

This file creates product recommendation rows after a diagnosis.

### Purpose

The recommendation service guarantees that product recommendations are saved in the database after diagnosis.

It follows this rule:

- use disease-specific mapped products when a disease is matched
- use general catalog fallback products when no disease is matched or fewer than two mapped products exist

### Constants

```python
GENERAL_REASON
```

Reason shown for fallback product recommendations.

```python
PREFERRED_FALLBACK_TERMS
```

Keywords used to choose safer general fallback products from the catalog.

### `create_product_recommendations`

This is the main function.

It:

1. Gets disease-specific recommendations from mappings.
2. Checks whether fewer than two products were found.
3. Adds fallback catalog products if needed.
4. Saves all recommendations to the database.
5. Refreshes saved rows.
6. Logs `products_created_count`.
7. Returns the created recommendations.

### `_mapped_recommendations`

This function creates product recommendations from disease-product mappings.

If the diagnosis disease is `Unknown`, it returns an empty list.

If the diagnosis disease is known, it:

- queries `DiseaseProductMapping`
- finds mappings for the disease
- logs how many mappings were found
- creates `ProductRecommendation` objects

### `_fill_with_general_catalog_recommendations`

This function adds fallback products from the existing product catalog.

It:

- loads all products
- avoids duplicate product IDs
- prefers products that match general/preventive/fungal keywords
- selects enough products to reach at least two recommendations
- logs which fallback products were selected
- returns the original recommendations plus fallback recommendations

### `_is_preferred_general_product`

This function checks whether a product is a good fallback option.

It searches product text fields such as:

- name
- English name
- product type
- active ingredient
- target disease
- usage instructions
- safety notes
- tags
- crops

If the product contains fallback keywords, it is preferred.

## Why This Design Was Chosen

The system separates responsibilities clearly:

- Groq classifies the image.
- The database stores trusted disease and product knowledge.
- The treatment service matches diseases and builds treatment output.
- The recommendation service creates product recommendation rows.
- The API file connects the upload, AI classifier, database matching, treatment, and product recommendation flow.

This avoids invented treatments or invented product names while still giving useful output when the AI result is uncertain.

## Demo Reliability

The latest backend behavior is demo-safe:

- Diagnosis does not stop when Groq fails.
- Unknown diseases still show useful treatment guidance.
- Product recommendations are always created when catalog products exist.
- Backend logs show disease matching and product creation details.
- The frontend can display treatment and product recommendations from the diagnosis response.
