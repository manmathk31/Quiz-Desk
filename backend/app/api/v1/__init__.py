"""API v1 Router aggregation."""
from fastapi import APIRouter
from app.api.v1.endpoints import users, question_bank, quizzes, roster, student_quiz, teacher_results, admin

api_v1_router = APIRouter()
api_v1_router.include_router(users.router)
api_v1_router.include_router(question_bank.router)
api_v1_router.include_router(quizzes.router)
api_v1_router.include_router(roster.router)
api_v1_router.include_router(student_quiz.router)
api_v1_router.include_router(teacher_results.router)
api_v1_router.include_router(admin.router)

__all__ = ["api_v1_router"]


