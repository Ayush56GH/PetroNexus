from fastapi import APIRouter
from backend.app.api.auth import router as auth_router
from backend.app.api.wells import router as wells_router
from backend.app.api.current_well import router as current_well_router
from backend.app.api.intelligence import router as intelligence_router
from backend.app.api.alerts import router as alerts_router
from backend.app.api.documents import router as documents_router
from backend.app.api.ai import router as ai_router
from backend.app.api.reports import router as reports_router
from backend.app.api.quality import router as quality_router
from backend.app.api.audit import router as audit_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(wells_router)
api_router.include_router(current_well_router)
api_router.include_router(intelligence_router)
api_router.include_router(alerts_router)
api_router.include_router(documents_router)
api_router.include_router(ai_router)
api_router.include_router(reports_router)
api_router.include_router(quality_router)
api_router.include_router(audit_router)
