import uuid
from datetime import datetime
from sqlalchemy import Column, Time, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import as_declarative, declared_attr

@as_declarative()
class Base:
    id: UUID

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

class BaseModel(Base):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    time_created = Column(Time(timezone=True), default=lambda: datetime.now().astimezone())
    time_updated = Column(
        Time(timezone=True), 
        default=lambda: datetime.now().astimezone(), 
        onupdate=lambda: datetime.now().astimezone()
    )

    date_created = Column(Date, default=lambda: datetime.now().astimezone().date())
    date_updated = Column(
        Date, 
        default=lambda: datetime.now().astimezone().date(), 
        onupdate=lambda: datetime.now().astimezone().date()
    )
