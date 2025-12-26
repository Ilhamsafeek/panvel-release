"""
OTP API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, validator
import re

from app.services.otp_service import otp_service

router = APIRouter()


class OTPRequest(BaseModel):
    identifier: str  # phone or email
    identifier_type: str  # 'phone' or 'email'
    purpose: str = 'registration'  # 'registration', 'login', 'password_reset'
    
    @validator('identifier_type')
    def validate_identifier_type(cls, v):
        if v not in ['phone', 'email']:
            raise ValueError('identifier_type must be "phone" or "email"')
        return v
    
    @validator('identifier')
    def validate_identifier(cls, v, values):
        if 'identifier_type' in values:
            if values['identifier_type'] == 'phone':
                # Validate phone format (E.164 format expected)
                if not re.match(r'^\+?[1-9]\d{1,14}$', v):
                    raise ValueError('Invalid phone number format')
            elif values['identifier_type'] == 'email':
                # Basic email validation
                if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v):
                    raise ValueError('Invalid email format')
        return v


class OTPVerification(BaseModel):
    identifier: str
    otp_code: str
    purpose: str = 'registration'


@router.post("/send", summary="Send OTP via SMS or Email")
async def send_otp(request: OTPRequest, req: Request):
    """
    Send OTP to phone or email
    """
    # Handle proxy IP addresses
    ip_address = req.client.host if req.client else "unknown"
    
    # Check for real IP behind proxy
    if 'x-forwarded-for' in req.headers:
        ip_address = req.headers['x-forwarded-for'].split(',')[0].strip()
    elif 'x-real-ip' in req.headers:
        ip_address = req.headers['x-real-ip']
    
    result = otp_service.create_otp(
        identifier=request.identifier,
        identifier_type=request.identifier_type,
        purpose=request.purpose,
        ip_address=ip_address
    )
    
    if result['success']:
        return {
            "success": True,
            "message": result['message'],
            "expires_in_minutes": result['expires_in_minutes']
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS 
            if 'wait' in result['error'].lower() or 'locked' in result['error'].lower()
            else status.HTTP_400_BAD_REQUEST,
            detail=result['error']
        )


@router.post("/verify", summary="Verify OTP code")
async def verify_otp(verification: OTPVerification):
    """
    Verify OTP code
    """
    result = otp_service.verify_otp(
        identifier=verification.identifier,
        otp_code=verification.otp_code,
        purpose=verification.purpose
    )
    
    if result['success']:
        return {
            "success": True,
            "message": result['message'],
            "verified": True
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result['error']
        )


@router.post("/resend", summary="Resend OTP")
async def resend_otp(request: OTPRequest, req: Request):
    """
    Resend OTP (same as send, but with different endpoint for clarity)
    """
    return await send_otp(request, req)