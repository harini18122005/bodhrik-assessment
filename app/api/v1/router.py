from fastapi import APIRouter

from app.api.v1.endpoints import auth, evaluations, sessions

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_v1_router.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])
