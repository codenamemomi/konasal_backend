from pydantic import BaseModel
from typing import Optional, List

class Course(BaseModel):
    id: int
    name: str
    category: str
    duration: Optional[str] = None
    summary: Optional[str] = None
    image: Optional[str] = None
    price: float
    description: Optional[str] = None
    courseObjectives: Optional[List] = None
    curriculum: Optional[List] = None
    targetAudience: Optional[List] = None
    courseBenefits: Optional[List] = None
    courseCompletion: Optional[List] = None

    class Config:
        from_attributes = True

class EnrollResponse(BaseModel):
    message: str

class UpdateProgress(BaseModel):
    progress: float