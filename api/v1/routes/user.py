from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from api.v1.schemas.auth import UserResponse, UserUpdate, GenderEnum
from api.v1.schemas.course import UpdateProgress
from api.v1.models.user import User
from api.v1.models.enrollment import Enrollment
from api.v1.models.course import Course
from api.db.session import get_db
from api.v1.services.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["Users"])

class EnrolledCourseResponse(BaseModel):
    id: int
    name: str
    summary: str
    category: str
    image: str | None
    progress: float | None

    class Config:
        orm_mode = True

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # The UserResponse model will automatically handle UUID serialization
    return UserResponse(
        id=current_user.id,  # This is UUID, but the serializer will convert to string
        email=current_user.email,
        is_verified=current_user.is_verified,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone_number=current_user.phone_number,
        date_of_birth=current_user.date_of_birth,
        gender=current_user.gender,
        profile_picture=current_user.profile_picture
    )

@router.get("/enrollments", response_model=List[EnrolledCourseResponse])
async def get_enrolled_courses(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Course, Enrollment.progress)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(Enrollment.user_id == current_user.id)
    )
    courses = result.all()
    return [
        {
            "id": course.id,
            "name": course.name,
            "summary": course.summary,
            "category": course.category,
            "image": course.image,
            "progress": progress
        }
        for course, progress in courses
    ]

@router.post("/courses/{course_id}/progress")
async def update_progress(
    course_id: int,
    progress_data: UpdateProgress,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Enrollment).where(Enrollment.user_id == current_user.id, Enrollment.course_id == course_id)
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    enrollment.progress = min(max(progress_data.progress, 0.0), 100.0)
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return {"message": "Progress updated"}

@router.post("/profile/picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    file_path = f"uploads/{current_user.id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    current_user.profile_picture = file_path
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return {"message": "Profile picture updated"}

@router.put("/profile")
async def update_profile(
    user_data: UserUpdate,  # Remove Depends() - it's not a dependency
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Remove the file parameter from here - it should be in a separate endpoint
    for field, value in user_data.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return {"message": "Profile updated successfully"}