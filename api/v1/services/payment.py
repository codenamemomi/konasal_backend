# api/v1/services/payment.py
import os
import httpx
from core.config.settings import settings
from typing import Dict, Optional
import logging
import json

logger = logging.getLogger(__name__)

class PayPalService:
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.base_url = "https://api-m.sandbox.paypal.com"  # Sandbox
        # self.base_url = "https://api-m.paypal.com"  # Production
        self.access_token = None
    
    async def get_access_token(self) -> str:
        """Get PayPal access token"""
        try:
            logger.info(f"Getting PayPal access token with client_id: {self.client_id[:10]}...")
            auth = (self.client_id, self.client_secret)
            data = {"grant_type": "client_credentials"}
            headers = {"Accept": "application/json", "Accept-Language": "en_US"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/oauth2/token",
                    auth=auth,
                    data=data,
                    headers=headers,
                    timeout=30.0
                )
            
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data["access_token"]
            logger.info("Successfully obtained PayPal access token")
            return self.access_token
            
        except httpx.HTTPError as e:
            error_detail = f"HTTP error getting PayPal access token: {e}"
            if e.response:
                error_detail += f"\nStatus: {e.response.status_code}"
                error_detail += f"\nResponse: {e.response.text}"
            logger.error(error_detail)
            raise Exception(f"Failed to get PayPal access token: {error_detail}")
        except Exception as e:
            logger.error(f"Error getting PayPal access token: {e}")
            raise Exception(f"Failed to get PayPal access token: {e}")
    
    async def get_headers(self) -> Dict:
        """Get headers with authorization"""
        if not self.access_token:
            await self.get_access_token()
        
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Prefer": "return=representation"
        }
    
    async def create_order(self, amount: float, currency: str = "USD", 
                         course_id: str = None, user_id: str = None) -> Dict:
        """Create a PayPal order"""
        try:
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": currency,
                        "value": f"{amount:.2f}"
                    },
                    "description": f"Course Purchase - {course_id}" if course_id else "Course Purchase",
                    "custom_id": f"user_{user_id}_course_{course_id}" if user_id and course_id else None
                }],
                "application_context": {
                    "return_url": "http://127.0.0.1:5500/checkout/success", #"https://www.konasalti.com/checkout/success",
                    "cancel_url": "http://127.0.0.1:5500/checkout/cancel", #"https://www.konasalti.com/checkout/cancel",
                    "brand_name": "Konasal Training Institute",
                    "user_action": "PAY_NOW",
                    "shipping_preference": "NO_SHIPPING"
                }
            }
            
            headers = await self.get_headers()
            
            logger.info(f"Creating PayPal order with payload: {json.dumps(payload, indent=2)}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v2/checkout/orders",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
            
            # Log the full response for debugging
            logger.info(f"PayPal API response status: {response.status_code}")
            logger.info(f"PayPal API response: {response.text}")
            
            response.raise_for_status()
            order_data = response.json()
            logger.info(f"Successfully created PayPal order: {order_data.get('id')}")
            return order_data
            
        except httpx.HTTPError as e:
            error_detail = f"HTTP error creating PayPal order: {e}"
            if e.response:
                error_detail += f"\nStatus: {e.response.status_code}"
                error_detail += f"\nResponse: {e.response.text}"
            logger.error(error_detail)
            raise Exception(f"Failed to create PayPal order: {error_detail}")
        except Exception as e:
            logger.error(f"Error creating PayPal order: {e}")
            raise Exception(f"Failed to create PayPal order: {e}")
    
    async def capture_order(self, order_id: str) -> Dict:
        """Capture a PayPal payment"""
        try:
            headers = await self.get_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                    headers=headers,
                    timeout=30.0
                )
            
            response.raise_for_status()
            capture_data = response.json()
            logger.info(f"Successfully captured PayPal order: {order_id}")
            return capture_data
            
        except httpx.HTTPError as e:
            error_detail = f"HTTP error capturing PayPal order: {e}"
            if e.response:
                error_detail += f"\nStatus: {e.response.status_code}"
                error_detail += f"\nResponse: {e.response.text}"
            logger.error(error_detail)
            raise Exception(f"Failed to capture PayPal payment: {error_detail}")
        except Exception as e:
            logger.error(f"Error capturing PayPal order: {e}")
            raise Exception(f"Failed to capture PayPal payment: {e}")
    
    async def get_order(self, order_id: str) -> Dict:
        """Get order details"""
        try:
            headers = await self.get_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v2/checkout/orders/{order_id}",
                    headers=headers,
                    timeout=30.0
                )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            error_detail = f"HTTP error getting PayPal order: {e}"
            if e.response:
                error_detail += f"\nStatus: {e.response.status_code}"
                error_detail += f"\nResponse: {e.response.text}"
            logger.error(error_detail)
            raise Exception(f"Failed to get PayPal order details: {error_detail}")
        except Exception as e:
            logger.error(f"Error getting PayPal order: {e}")
            raise Exception(f"Failed to get PayPal order details: {e}")