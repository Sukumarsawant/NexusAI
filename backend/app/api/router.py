from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router
from app.api.v1.chat import router as chat_router
from app.api.v1.retrieval import router as retrieval_router
from app.api.v1.observability import router as observability_router
from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.system import router as system_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(documents_router)
api_router.include_router(chat_router)
api_router.include_router(retrieval_router)
api_router.include_router(observability_router)
api_router.include_router(evaluation_router)
api_router.include_router(system_router)
