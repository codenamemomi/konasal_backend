from fastapi import APIRouter
from api.v1.routes.auth import auth
from api.v1.routes.course import course_router
from api.v1.routes.user import router as user_router  # Import user router

api_version_one = APIRouter(prefix="/api/v1")
api_version_one.include_router(auth)
api_version_one.include_router(course_router)
api_version_one.include_router(user_router)  # Add user router