from sqlalchemy import Column, String, Float, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from api.v1.models.base_class import Base

class Course(Base):
    __tablename__ = "courses"

    # This should be UUID, not Integer
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False)
    duration = Column(String, nullable=True)
    summary = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    image = Column(String, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    courseobjectives = Column(JSON, nullable=True)
    curriculum = Column(JSON, nullable=True)
    targetaudience = Column(JSON, nullable=True)
    coursebenefits = Column(JSON, nullable=True)
    coursecompletion = Column(JSON, nullable=True)

    enrollments = relationship("Enrollment", back_populates="course")