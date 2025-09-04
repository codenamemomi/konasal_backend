from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict
from uuid import UUID
from api.db.session import get_db
from api.v1.services.auth import get_current_user
from api.v1.models.user import User
from api.v1.models.payment import Payment
from api.v1.models.course import Course
from api.v1.services.payment import PayPalService
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])

class CreateOrderRequest(BaseModel):
    course_id: int
    amount: float
    currency: str = "USD"

class CreateOrderResponse(BaseModel):
    order_id: str
    approval_url: str
    status: str

@router.post("/create-order", response_model=CreateOrderResponse)
async def create_paypal_order(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a PayPal order for course purchase"""
    paypal_service = PayPalService()
    
    try:
        # Validate course_id as an integer
        try:
            course_id_int = int(request.course_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid course ID format: must be an integer"
            )
        
        # Fetch course to get its UUID
        result = await db.execute(
            select(Course).where(Course.id == course_id_int)
        )
        course = result.scalar_one_or_none()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        course_id_uuid = course.id  # Course.id is a UUID
        
        # Create order in PayPal
        order_data = await paypal_service.create_order(
            amount=request.amount,
            currency=request.currency,
            course_id=str(course_id_int),  # Send integer as string to PayPal
            user_id=str(current_user.id)
        )
        
        # Save payment record in database
        payment = Payment(
            user_id=current_user.id,
            course_id=request.course_id,
            amount=request.amount,
            currency=request.currency,
            paypal_order_id=order_data["id"],
            status="pending"
        )
        
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        
        # Find approval URL
        approval_url = None
        for link in order_data.get("links", []):
            if link.get("rel") == "approve":
                approval_url = link.get("href")
                break
        
        if not approval_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No approval URL found in PayPal response"
            )
        
        return CreateOrderResponse(
            order_id=order_data["id"],
            approval_url=approval_url,
            status=order_data["status"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create order: {str(e)}"
        )

@router.post("/capture/{order_id}")
async def capture_paypal_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Capture a PayPal order"""
    paypal_service = PayPalService()
    
    try:
        # Fetch payment record
        result = await db.execute(
            select(Payment).where(Payment.paypal_order_id == order_id)
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Capture order in PayPal
        capture_data = await paypal_service.capture_order(order_id)
        
        # Update payment status
        payment.status = capture_data["status"].lower()
        await db.commit()
        await db.refresh(payment)
        
        return {
            "order_id": order_id,
            "status": capture_data["status"],
            "details": capture_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to capture order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to capture order: {str(e)}"
        )