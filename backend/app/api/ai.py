import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import Profile
from backend.app.models.conversation import Conversation, Message
from backend.app.models.audit import AuditLog
from backend.app.rag.langchain_service import LangChainRAGService
from backend.app.services.auth_service import get_current_user, get_optional_current_user

router = APIRouter(prefix="/ai", tags=["AI Drilling Assistant"])
rag_service = LangChainRAGService()

class AIQueryRequest(BaseModel):
    query: str
    well_id: Optional[int] = 23
    current_depth: Optional[float] = None
    conversation_id: Optional[str] = None

class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: List[str] = []
    created_at: str

class ConversationOut(BaseModel):
    id: str
    title: str
    active_well_id: Optional[int]
    created_at: str
    updated_at: str
    message_count: int

@router.post("/query")
async def ask_assistant(
    req: AIQueryRequest,
    current_user: Optional[Profile] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    if not req.query or len(req.query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Resolve user identity (authenticated user or default demo engineer persona)
    effective_user = current_user
    if not effective_user:
        effective_user = db.query(Profile).filter(Profile.email == "engineer@oilindia.in").first()

    user_id = current_user.id if current_user else (effective_user.id if effective_user else None)

    # Handle Conversation Session
    conv = None
    conversation_context = []
    if effective_user:
        if req.conversation_id:
            try:
                c_uuid = uuid.UUID(req.conversation_id)
                conv = db.query(Conversation).filter(
                    Conversation.id == c_uuid,
                    Conversation.user_id == effective_user.id
                ).first()
            except ValueError:
                pass

        if not conv:
            conv = Conversation(
                user_id=effective_user.id,
                title=req.query[:45] + ("..." if len(req.query) > 45 else ""),
                active_well_id=req.well_id or 23
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)

        # Retrieve recent conversation history for follow-up contextual understanding
        recent_msgs = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at.asc()).all()

        for m in recent_msgs[-6:]:
            conversation_context.append({"role": m.role, "content": m.content})

        # Save user message to persistent history
        user_msg = Message(
            conversation_id=conv.id,
            user_id=effective_user.id,
            role="user",
            content=req.query
        )
        db.add(user_msg)
        db.commit()

    # Execute permission-aware RAG pipeline
    result = await rag_service.answer_drilling_query(
        db,
        active_well_id=req.well_id or 23,
        user_query=req.query,
        requesting_user_id=user_id,
        current_depth_override=req.current_depth,
        conversation_context=conversation_context if conversation_context else None
    )

    # Save assistant response to conversation history
    if conv and effective_user:
        assistant_msg = Message(
            conversation_id=conv.id,
            user_id=effective_user.id,
            role="assistant",
            content=result["response"],
            citations=result.get("sources", [])
        )
        db.add(assistant_msg)
        db.commit()
        result["conversation_id"] = str(conv.id)

    # Audit log (resilient, never blocks user response)
    try:
        audit = AuditLog(
            user_id=user_id,
            user_email=current_user.email if current_user else "engineer@oilindia.in",
            action="AI_QUERY",
            resource=f"well:{req.well_id}",
            details={"query": req.query, "sources_count": len(result.get("sources", []))}
        )
        db.add(audit)
        db.commit()
    except Exception as audit_err:
        logger.warning(f"Failed to record audit log for AI query: {audit_err}")
        db.rollback()

    return result

@router.get("/conversations", response_model=List[ConversationOut])
def list_conversations(
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns persistent conversation sessions isolated to the authenticated user"""
    convs = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()

    return [
        {
            "id": str(c.id),
            "title": c.title,
            "active_well_id": c.active_well_id,
            "created_at": c.created_at.isoformat() if c.created_at else "",
            "updated_at": c.updated_at.isoformat() if c.updated_at else "",
            "message_count": len(c.messages)
        }
        for c in convs
    ]

@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: str,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves messages for a specific conversation, strictly enforcing ownership"""
    try:
        c_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation UUID")

    conv = db.query(Conversation).filter(
        Conversation.id == c_uuid,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")

    msgs = db.query(Message).filter(
        Message.conversation_id == conv.id
    ).order_by(Message.created_at.asc()).all()

    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "citations": m.citations or [],
            "created_at": m.created_at.isoformat() if m.created_at else ""
        }
        for m in msgs
    ]
