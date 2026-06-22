from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.image_dataset_importer import import_image_datasets
from app.db.product_importer import import_product_catalog
from app.db.session import SessionLocal
from app.models import (
    CropType,
    Disease,
    DiseaseProductMapping,
    KnowledgeBaseEntry,
    Product,
    User,
    UserRole,
)


def seed_database() -> None:
    db = SessionLocal()
    try:
        print(f"DATABASE_URL configured: {'yes' if settings.database_url.strip() else 'no'}", flush=True)
        print(f"DEFAULT_ADMIN_EMAIL configured: {'yes' if settings.default_admin_email.strip() else 'no'}", flush=True)
        print(f"DEFAULT_ADMIN_PASSWORD configured: {'yes' if settings.default_admin_password else 'no'}", flush=True)
        users_count_before_seed = db.query(User).count()
        print(f"users_count_before_seed: {users_count_before_seed}", flush=True)

        _seed_users(db)
        if not db.query(Disease).first():
            diseases = _seed_diseases(db)
            _seed_knowledge(db, diseases)
            products = _seed_products(db)
            _seed_mappings(db, diseases, products)
        _ensure_baseline_reference_data(db)
        db.commit()
        users_count_after_seed = db.query(User).count()
        print(f"users_count_after_seed: {users_count_after_seed}", flush=True)
        import_product_catalog(db)
        import_image_datasets(db)
    finally:
        db.close()


def _seed_users(db: Session) -> None:
    admin_email = settings.default_admin_email.strip().lower()
    admin_password = settings.default_admin_password
    is_production = settings.app_env.strip().lower() in {"production", "prod"}

    if not admin_email or not admin_password:
        message = "DEFAULT_ADMIN_EMAIL and DEFAULT_ADMIN_PASSWORD must be configured to seed the default admin account."
        if is_production:
            raise RuntimeError(message)
        print(f"Skipping default admin seed: {message}", flush=True)
        return

    existing = db.query(User).filter(func.lower(User.email) == admin_email).first()
    if not existing:
        db.add(
            User(
                name="System Admin",
                email=admin_email,
                password_hash=hash_password(admin_password),
                role=UserRole.admin,
                is_active=True,
            )
        )
        print("Default admin account created from environment configuration.", flush=True)
        return

    existing.role = UserRole.admin
    existing.is_active = True
    print("Default admin account already exists; using existing account.", flush=True)


def _seed_diseases(db: Session) -> dict[str, Disease]:
    crop_names = ["Tomato", "Potato", "Rice", "Wheat", "Cucumber"]
    crops = {name: CropType(name=name) for name in crop_names}
    db.add_all(crops.values())
    db.flush()

    disease_rows = [
        (
            "Tomato Early Blight",
            crops["Tomato"],
            "Fungal disease causing concentric brown spots on older leaves.",
            "Warm humid conditions, infected debris, and overhead irrigation.",
            "Bullseye leaf spots, yellowing, lower leaf drop, stem lesions.",
            "Reduces photosynthesis and can lower fruit size and yield.",
        ),
        (
            "Potato Late Blight",
            crops["Potato"],
            "Fast-spreading oomycete disease that can destroy foliage and tubers.",
            "Cool wet weather, wind-blown spores, and infected seed tubers.",
            "Water-soaked lesions, white growth on leaf undersides, tuber rot.",
            "Can cause severe crop loss within days if unmanaged.",
        ),
        (
            "Rice Blast",
            crops["Rice"],
            "Fungal disease affecting leaves, nodes, and panicles.",
            "High humidity, excess nitrogen, dense canopy, and susceptible varieties.",
            "Diamond-shaped leaf lesions, neck blast, broken panicles.",
            "Can sharply reduce grain filling and harvest quality.",
        ),
        (
            "Wheat Rust",
            crops["Wheat"],
            "Rust disease producing orange to brown pustules on leaves or stems.",
            "Airborne spores, mild temperatures, and extended leaf wetness.",
            "Powdery pustules, chlorosis, weak stems, shriveled grain.",
            "Reduces grain weight and marketable yield.",
        ),
        (
            "Cucumber Powdery Mildew",
            crops["Cucumber"],
            "Fungal disease appearing as white powdery patches on leaves.",
            "Crowded plants, humid nights, dry days, and poor airflow.",
            "White powder on leaves, yellowing, leaf curling, early senescence.",
            "Weakens plants and reduces fruit quality.",
        ),
    ]
    diseases = {}
    for name, crop, description, causes, symptoms, impact in disease_rows:
        disease = Disease(
            crop_type_id=crop.id,
            name=name,
            description=description,
            causes=causes,
            symptoms=symptoms,
            impact=impact,
        )
        db.add(disease)
        diseases[name] = disease
    db.flush()
    return diseases


def _seed_knowledge(db: Session, diseases: dict[str, Disease]) -> None:
    entries = [
        ("Tomato Early Blight", "Early blight field response", "Remove infected lower leaves, avoid splashing water, rotate away from solanaceous crops, and apply labeled fungicide at first symptoms.", "tomato early blight fungicide prevention"),
        ("Tomato Early Blight", "Tomato prevention", "Stake plants, improve airflow, mulch soil, sanitize tools, and avoid working wet foliage.", "tomato prevention airflow sanitation"),
        ("Potato Late Blight", "Late blight urgent control", "Scout daily in cool wet weather. Remove heavily infected plants and apply protectant fungicide before rain when disease pressure is high.", "potato late blight urgent copper chlorothalonil"),
        ("Rice Blast", "Rice blast nutrient management", "Avoid excess nitrogen, maintain balanced potassium, select resistant varieties, and manage water depth to reduce stress.", "rice blast nitrogen water resistant"),
        ("Wheat Rust", "Wheat rust protection", "Use resistant cultivars, monitor regional rust alerts, and treat early when pustules appear on upper leaves.", "wheat rust triazole monitoring"),
        ("Cucumber Powdery Mildew", "Powdery mildew suppression", "Increase spacing, prune crowded foliage, avoid excessive nitrogen, and apply sulfur or biological products where labeled.", "cucumber powdery mildew sulfur biological"),
    ]
    for disease_name, title, content, tags in entries:
        db.add(KnowledgeBaseEntry(disease_id=diseases[disease_name].id, title=title, content=content, tags=tags))


def _seed_products(db: Session) -> dict[str, Product]:
    rows = [
        ("BlightGuard SC", "Azoxystrobin", "Apply as a foliar spray at early symptoms. Repeat according to label and local regulations.", "Tomato Early Blight", "Wear gloves and mask. Observe pre-harvest interval.", "tomato early blight azoxystrobin"),
        ("CopperShield 77", "Copper hydroxide", "Use as a protectant spray before wet weather or during early disease pressure.", "Late blight and bacterial spots", "Avoid overuse to reduce copper buildup in soil.", "potato tomato copper late blight"),
        ("RiceSafe BlastCare", "Tricyclazole", "Apply at tillering or booting stage when blast risk is high.", "Rice Blast", "Use only where registered. Keep away from waterways.", "rice blast tricyclazole"),
        ("RustStop Pro", "Propiconazole", "Apply when rust pustules are first observed on upper leaves.", "Wheat Rust", "Rotate fungicide groups to reduce resistance.", "wheat rust propiconazole triazole"),
        ("MildewAway Bio", "Bacillus subtilis", "Spray preventively and maintain coverage on new growth.", "Powdery Mildew", "Low-residue biological option. Follow storage instructions.", "cucumber powdery mildew biological"),
        ("Sulfur Dust 80", "Elemental sulfur", "Apply under suitable temperatures for powdery mildew suppression.", "Powdery Mildew", "Do not apply during high heat or close to oil sprays.", "cucumber powdery mildew sulfur"),
    ]
    products = {}
    for name, active, usage, target, safety, tags in rows:
        product = Product(
            name=name,
            active_ingredient=active,
            usage_instructions=usage,
            target_disease=target,
            safety_notes=safety,
            tags=tags,
        )
        db.add(product)
        products[name] = product
    db.flush()
    return products


def _seed_mappings(db: Session, diseases: dict[str, Disease], products: dict[str, Product]) -> None:
    mappings = [
        ("Tomato Early Blight", "BlightGuard SC", "Designed for fungal leaf blights and mapped directly to tomato early blight."),
        ("Tomato Early Blight", "CopperShield 77", "Useful protectant option when wet weather increases blight pressure."),
        ("Potato Late Blight", "CopperShield 77", "Protectant copper product tagged for potato late blight pressure."),
        ("Rice Blast", "RiceSafe BlastCare", "Mapped to rice blast and suitable for high-risk growth stages."),
        ("Wheat Rust", "RustStop Pro", "Triazole fungicide mapped to wheat rust symptoms."),
        ("Cucumber Powdery Mildew", "MildewAway Bio", "Biological product tagged for cucumber powdery mildew."),
        ("Cucumber Powdery Mildew", "Sulfur Dust 80", "Sulfur product commonly used for powdery mildew suppression."),
    ]
    for disease_name, product_name, reason in mappings:
        db.add(
            DiseaseProductMapping(
                disease_id=diseases[disease_name].id,
                product_id=products[product_name].id,
                match_reason=reason,
            )
        )


def _ensure_baseline_reference_data(db: Session) -> None:
    crop_names = ["Tomato", "Potato", "Rice", "Wheat", "Cucumber"]
    crops = {}
    for name in crop_names:
        crop = db.query(CropType).filter(CropType.name == name).first()
        if not crop:
            crop = CropType(name=name)
            db.add(crop)
            db.flush()
        crops[name] = crop

    disease_rows = [
        ("Tomato Early Blight", "Tomato", "Fungal disease causing concentric brown spots on older leaves.", "Warm humid conditions, infected debris, and overhead irrigation.", "Bullseye leaf spots, yellowing, lower leaf drop, stem lesions.", "Reduces photosynthesis and can lower fruit size and yield."),
        ("Potato Late Blight", "Potato", "Fast-spreading oomycete disease that can destroy foliage and tubers.", "Cool wet weather, wind-blown spores, and infected seed tubers.", "Water-soaked lesions, white growth on leaf undersides, tuber rot.", "Can cause severe crop loss within days if unmanaged."),
        ("Rice Blast", "Rice", "Fungal disease affecting leaves, nodes, and panicles.", "High humidity, excess nitrogen, dense canopy, and susceptible varieties.", "Diamond-shaped leaf lesions, neck blast, broken panicles.", "Can sharply reduce grain filling and harvest quality."),
        ("Wheat Rust", "Wheat", "Rust disease producing orange to brown pustules on leaves or stems.", "Airborne spores, mild temperatures, and extended leaf wetness.", "Powdery pustules, chlorosis, weak stems, shriveled grain.", "Reduces grain weight and marketable yield."),
        ("Cucumber Powdery Mildew", "Cucumber", "Fungal disease appearing as white powdery patches on leaves.", "Crowded plants, humid nights, dry days, and poor airflow.", "White powder on leaves, yellowing, leaf curling, early senescence.", "Weakens plants and reduces fruit quality."),
    ]
    diseases = {}
    for name, crop_name, description, causes, symptoms, impact in disease_rows:
        disease = db.query(Disease).filter(Disease.name == name).first()
        if not disease:
            disease = Disease(crop_type_id=crops[crop_name].id, name=name, description=description, causes=causes, symptoms=symptoms, impact=impact)
            db.add(disease)
        else:
            disease.crop_type_id = crops[crop_name].id
            disease.description = description
            disease.causes = causes
            disease.symptoms = symptoms
            disease.impact = impact
        db.flush()
        diseases[name] = disease

    knowledge_rows = [
        ("Tomato Early Blight", "Early blight field response", "Remove infected lower leaves, avoid splashing water, rotate away from solanaceous crops, and apply labeled fungicide at first symptoms.", "tomato early blight fungicide prevention bullseye spots"),
        ("Potato Late Blight", "Late blight urgent control", "Scout daily in cool wet weather. Remove heavily infected plants and apply protectant fungicide before rain when disease pressure is high.", "potato late blight water-soaked white growth copper chlorothalonil"),
        ("Rice Blast", "Rice blast nutrient management", "Avoid excess nitrogen, maintain balanced potassium, select resistant varieties, and manage water depth to reduce stress.", "rice blast diamond lesions nitrogen water resistant"),
        ("Wheat Rust", "Wheat rust protection", "Use resistant cultivars, monitor regional rust alerts, and treat early when pustules appear on upper leaves.", "wheat rust orange pustules triazole monitoring"),
        ("Cucumber Powdery Mildew", "Powdery mildew suppression", "Increase spacing, prune crowded foliage, avoid excessive nitrogen, and apply sulfur or biological products where labeled.", "cucumber powdery mildew white powder sulfur biological"),
    ]
    for disease_name, title, content, tags in knowledge_rows:
        entry = db.query(KnowledgeBaseEntry).filter(KnowledgeBaseEntry.title == title).first()
        if not entry:
            db.add(KnowledgeBaseEntry(disease_id=diseases[disease_name].id, title=title, content=content, tags=tags))
        else:
            entry.disease_id = diseases[disease_name].id
            entry.content = content
            entry.tags = tags

    product_rows = [
        ("BlightGuard SC", "Azoxystrobin", "Apply as a foliar spray at early symptoms. Repeat according to label and local regulations.", "Tomato Early Blight", "Wear gloves and mask. Observe pre-harvest interval.", "tomato early blight azoxystrobin bullseye spots"),
        ("CopperShield 77", "Copper hydroxide", "Use as a protectant spray before wet weather or during early disease pressure.", "Potato Late Blight", "Avoid overuse to reduce copper buildup in soil.", "potato late blight copper water-soaked lesions"),
        ("RiceSafe BlastCare", "Tricyclazole", "Apply at tillering or booting stage when blast risk is high.", "Rice Blast", "Use only where registered. Keep away from waterways.", "rice blast tricyclazole diamond lesions"),
        ("RustStop Pro", "Propiconazole", "Apply when rust pustules are first observed on upper leaves.", "Wheat Rust", "Rotate fungicide groups to reduce resistance.", "wheat rust propiconazole triazole orange pustules"),
        ("MildewAway Bio", "Bacillus subtilis", "Spray preventively and maintain coverage on new growth.", "Cucumber Powdery Mildew", "Low-residue biological option. Follow storage instructions.", "cucumber powdery mildew biological white powder"),
        ("Sulfur Dust 80", "Elemental sulfur", "Apply under suitable temperatures for powdery mildew suppression.", "Cucumber Powdery Mildew", "Do not apply during high heat or close to oil sprays.", "cucumber powdery mildew sulfur white powder"),
    ]
    products = {}
    for name, active, usage, target, safety, tags in product_rows:
        product = db.query(Product).filter(Product.name == name).first()
        if not product:
            product = Product(name=name, active_ingredient=active, usage_instructions=usage, target_disease=target, safety_notes=safety, tags=tags)
            db.add(product)
        else:
            product.active_ingredient = active
            product.usage_instructions = usage
            product.target_disease = target
            product.safety_notes = safety
            product.tags = tags
        db.flush()
        products[name] = product

    mapping_rows = [
        ("Tomato Early Blight", "BlightGuard SC", "Designed for fungal leaf blights and mapped directly to tomato early blight."),
        ("Potato Late Blight", "CopperShield 77", "Protectant copper product tagged for potato late blight pressure."),
        ("Rice Blast", "RiceSafe BlastCare", "Mapped to rice blast and suitable for high-risk growth stages."),
        ("Wheat Rust", "RustStop Pro", "Triazole fungicide mapped to wheat rust symptoms."),
        ("Cucumber Powdery Mildew", "MildewAway Bio", "Biological product tagged for cucumber powdery mildew."),
        ("Cucumber Powdery Mildew", "Sulfur Dust 80", "Sulfur product commonly used for powdery mildew suppression."),
    ]
    for disease_name, product_name, reason in mapping_rows:
        mapping = (
            db.query(DiseaseProductMapping)
            .filter(DiseaseProductMapping.disease_id == diseases[disease_name].id, DiseaseProductMapping.product_id == products[product_name].id)
            .first()
        )
        if not mapping:
            db.add(DiseaseProductMapping(disease_id=diseases[disease_name].id, product_id=products[product_name].id, match_reason=reason))
        else:
            mapping.match_reason = reason
