from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.rag.langchain_service import LangChainRAGService
from backend.app.models.audit import AuditLog

router = APIRouter(prefix="/ai", tags=["AI Drilling Assistant"])
rag_service = LangChainRAGService()

class AIQueryRequest(BaseModel):
    query: str
    well_id: Optional[int] = 23
    current_depth: Optional[float] = None

@router.post("/query")
async def ask_assistant(req: AIQueryRequest, db: Session = Depends(get_db)):
    if not req.query or len(req.query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    result = await rag_service.answer_drilling_query(
        db,
        active_well_id=req.well_id or 23,
        user_query=req.query,
        current_depth_override=req.current_depth
    )

    # Audit log
    audit = AuditLog(
        action="AI_QUERY",
        resource=f"well:{req.well_id}",
        details={"query": req.query, "sources_count": len(result.get("sources", []))}
    )
    db.add(audit)
    db.commit()

    return result
