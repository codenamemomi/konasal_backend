# api/v1/models/payment.py
from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from api.v1.models.base_class import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    paypal_order_id = Column(String(255), unique=True)
    paypal_payment_id = Column(String(255))
    status = Column(String(50), default="pending")  # pending, completed, failed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="payments")
    course = relationship("Course", back_populates="payments")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "course_id": str(self.course_id),
            "amount": self.amount,
            "currency": self.currency,
            "paypal_order_id": self.paypal_order_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }