#!/usr/bin/env python3
import httpx
import os
import sys
from core.config.settings import settings

async def test_paypal_credentials():
    """Test PayPal credentials by getting an access token"""
    print("Testing PayPal credentials...")
    print(f"Client ID: {settings.PAYPAL_CLIENT_ID}")
    print(f"Client Secret: {settings.PAYPAL_CLIENT_SECRET[:10]}...")  # Show first 10 chars for security
    
    base_url = "https://api-m.sandbox.paypal.com"
    
    try:
        auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
        data = {"grant_type": "client_credentials"}
        headers = {"Accept": "application/json", "Accept-Language": "en_US"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/v1/oauth2/token",
                auth=auth,
                data=data,
                headers=headers,
                timeout=30.0
            )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Success! PayPal credentials are valid.")
            print(f"Access Token: {token_data['access_token'][:50]}...")
            return True
        else:
            print("❌ Failed! PayPal credentials are invalid.")
            return False
            
    except Exception as e:
        print(f"❌ Error testing PayPal credentials: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_paypal_credentials())
    sys.exit(0 if success else 1)