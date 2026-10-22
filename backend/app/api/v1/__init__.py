"""API v1 Router aggregation."""
from fastapi import APIRouter
from app.api.v1.endpoints import users, question_bank

api_v1_router = APIRouter()
api_v1_router.include_router(users.router)
api_v1_router.include_router(question_bank.router)

__all__ = ["api_v1_router"]

