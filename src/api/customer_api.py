from fastapi import FastAPI, Header, HTTPException, Depends, Security
from fastapi.security import OAuth2AuthorizationCodeBearer
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import json

# Internal imports
# from src.core.tenant_manager import tenant_manager

app = FastAPI(title="AVA Customer API (Azure AD Secured)", version="1.1.0")

# --- Azure AD Configuration ---
# These should be set in your .env file
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "common")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
AZURE_OPENID_CONFIG_URL = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/v2.0/.well-known/openid-configuration"

# oauth2_scheme = OAuth2AuthorizationCodeBearer(
#     authorizationUrl=f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/authorize",
#     tokenUrl=f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token",
# )

class CallLog(BaseModel):
    id: str
    caller_number: str
    start_time: datetime
    duration_seconds: float
    outcome: str
    transcript: Optional[str]

class TenantSettings(BaseModel):
    greeting: str
    prompt: str
    transfer_number: str

async def get_current_tenant_id(
    # In a real environment, you would use fastapi-azure-auth here:
    # azure_user: User = Security(azure_scheme)
    authorization: str = Header(...)
):
    """
    Security Middleware: Validates Azure AD Token and maps to internal tenant_id.
    """
    # 1. Validate Token (Pseudo-code for template)
    # token = authorization.replace("Bearer ", "")
    # claims = validate_azure_token(token) # Using msal or fastapi-azure-auth
    
    # Let's assume 'oid' (Object ID) is the unique identifier for the user in Azure
    # azure_oid = claims.get("oid")
    
    # For demonstration/template purposes:
    azure_oid = "azure-user-123" # This would come from the token
    
    # 2. Map Azure OID to local tenant_id
    # t_id = await tenant_manager.resolve_tenant_by_azure_oid(azure_oid)
    t_id = "local-tenant-abc" # Mocked for template
    
    if not t_id:
        raise HTTPException(
            status_code=403, 
            detail="Azure account is not linked to any AVA Tenant. Please contact support."
        )
    
    return t_id

@app.get("/calls", response_model=List[CallLog])
async def list_calls(tenant_id: str = Depends(get_current_tenant_id)):
    """Fetch call history only for the tenant linked to the Azure account."""
    return [
        {
            "id": "call-azure-1",
            "caller_number": "+66810000000",
            "start_time": datetime.now(),
            "duration_seconds": 120.0,
            "outcome": "completed",
            "transcript": "User: ขอคุยกับพนักงานครับ AI: ได้ค่ะ กำลังโอนสายไปที่..."
        }
    ]

@app.get("/settings", response_model=TenantSettings)
async def get_settings(tenant_id: str = Depends(get_current_tenant_id)):
    """View settings for the linked tenant."""
    return {
        "greeting": "ยินดีต้อนรับสู่บริการ Voice AI ของเราค่ะ",
        "prompt": "You are a professional receptionist.",
        "transfer_number": "+66800000000"
    }

@app.patch("/settings")
async def update_settings(settings: TenantSettings, tenant_id: str = Depends(get_current_tenant_id)):
    """Update settings for the linked tenant."""
    # Logic to update database via tenant_manager
    return {"status": "success", "message": f"Settings updated for tenant {tenant_id}"}

@app.get("/auth/login-url")
async def get_login_url():
    """Returns the Azure AD login URL for the frontend."""
    scope = "openid profile email"
    return {
        "url": f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/authorize?client_id={AZURE_CLIENT_ID}&response_type=code&redirect_uri={os.getenv('AZURE_REDIRECT_URI')}&scope={scope}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
