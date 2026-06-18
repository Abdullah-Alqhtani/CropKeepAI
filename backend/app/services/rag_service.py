import re

from sqlalchemy.orm import Session

from app.models import KnowledgeBaseEntry


def retrieve_knowledge(
    db: Session,
    crop_type: str,
    disease_name: str,
    symptoms: str = "",
    tags: list[str] | None = None,
    limit: int = 4,
) -> list[KnowledgeBaseEntry]:
    entries = db.query(KnowledgeBaseEntry).all()
    query_text = " ".join([crop_type or "", disease_name or "", symptoms or "", " ".join(tags or [])])
    query_terms = {term for term in re.findall(r"[a-z0-9]+", query_text.lower()) if len(term) > 2 and term != "unknown"}
    if not query_terms:
        print("RAG retrieval skipped: no crop/disease/symptom/tag terms yet.", flush=True)
        return []

    def score(entry: KnowledgeBaseEntry) -> int:
        text = " ".join([entry.title, entry.content, entry.tags, entry.disease.name, entry.disease.crop_type.name]).lower()
        value = sum(1 for term in query_terms if term in text)
        disease = (disease_name or "").lower()
        crop = (crop_type or "").lower()
        if disease and disease != "unknown" and disease in text:
            value += 6
        if crop and crop != "unknown" and crop in text:
            value += 3
        return value

    ranked = [(score(entry), entry) for entry in entries]
    matches = [(value, entry) for value, entry in ranked if value > 0]
    selected = [entry for value, entry in sorted(matches, key=lambda item: item[0], reverse=True)[:limit]]
    print(
        "RAG retrieved entries:",
        [
            {
                "id": entry.id,
                "title": entry.title,
                "disease": entry.disease.name,
                "score": next(value for value, item in matches if item.id == entry.id),
            }
            for entry in selected
        ],
        flush=True,
    )
    return selected


def build_knowledge_context(entries: list[KnowledgeBaseEntry]) -> str:
    if not entries:
        return "No matching knowledge-base entry was found."
    return "\n\n".join(f"{entry.title}\n{entry.content}" for entry in entries)
