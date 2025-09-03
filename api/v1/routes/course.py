from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.v1.services.course_service import CourseService
from api.v1.models.course import Course
from api.v1.models.enrollment import Enrollment
from api.v1.models.user import User
from api.db.session import get_db
from api.v1.services.auth import get_current_user

course_router = APIRouter(prefix="/courses", tags=["Courses"])

@course_router.get("/")
async def get_courses(category: str = None, search: str = None, db: AsyncSession = Depends(get_db)):
    courses = await CourseService.get_all_courses(db, category, search)
    return courses

@course_router.get("/{course_id}")
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    course = await CourseService.get_course_by_id(db, course_id)
    return course

@course_router.post("/enroll/{course_id}", response_model=dict)
async def enroll_course(course_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Check if course exists using CourseService
    course = await CourseService.get_course_by_id(db, course_id)  # Raises 404 if not found

    # Check if already enrolled
    result = await db.execute(
        select(Enrollment).where(Enrollment.user_id == current_user.id, Enrollment.course_id == course_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already enrolled in this course")

    # Create enrollment
    enrollment = Enrollment(user_id=current_user.id, course_id=course_id)
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return {"message": f"Enrolled in course {course.name} successfully"}