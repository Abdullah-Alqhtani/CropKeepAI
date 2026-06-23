"""Handle follow-up questions about a saved diagnosis.

Each user gets a separate chat session per diagnosis, and the AI receives the
diagnosis, relevant knowledge-base entries, and recent conversation context.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import ChatMessage, ChatSession, DiagnosisResult, User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_service import answer_followup
from app.services.auth_service import get_current_user
from app.services.rag_service import build_knowledge_context, retrieve_knowledge

router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Users may only chat about their own diagnosis records.
    diagnosis = db.query(DiagnosisResult).filter(DiagnosisResult.id == payload.diagnosis_id).first()
    if not diagnosis or diagnosis.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis not found")

    session = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user.id, ChatSession.diagnosis_id == diagnosis.id)
        .first()
    )
    if not session:
        session = ChatSession(user_id=user.id, diagnosis_id=diagnosis.id)
        db.add(session)
        db.commit()
        db.refresh(session)

    user_message = ChatMessage(session_id=session.id, role="user", content=payload.message)
    db.add(user_message)
    db.commit()

    # Build focused context instead of sending the entire database to the AI service.
    history = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at).all()
    entries = retrieve_knowledge(db, diagnosis.crop_type, diagnosis.disease_name)
    diagnosis_context = (
        f"Crop: {diagnosis.crop_type}\nDisease: {diagnosis.disease_name}\n"
        f"Severity: {diagnosis.severity}\nTreatment: {diagnosis.treatment_steps}"
    )
    try:
        answer = answer_followup(
            payload.message,
            diagnosis_context,
            build_knowledge_context(entries),
            [{"role": item.role, "content": item.content} for item in history],
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    assistant_message = ChatMessage(session_id=session.id, role="assistant", content=answer)
    db.add(assistant_message)
    db.commit()

    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at).all()
    return ChatResponse(session_id=session.id, messages=messages)
