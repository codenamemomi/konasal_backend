from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from api.v1.models.course import Course
from fastapi import HTTPException

class CourseService:
    @staticmethod
    async def get_all_courses(db: AsyncSession, category: str | None = None, search: str | None = None):
        query = select(Course)
        if category:
            query = query.filter(Course.category == category)
        if search:
            query = query.filter(
                (Course.name.ilike(f"%{search}%")) | (Course.description.ilike(f"%{search}%"))
            )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_course_by_id(db: AsyncSession, course_id: int):
        query = select(Course).filter(Course.id == course_id)
        result = await db.execute(query)
        course = result.scalars().first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course