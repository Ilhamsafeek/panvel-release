import pytest
from app.services.otp_service import otp_service


def test_otp_generation():
    otp, hash_val = otp_service.generate_otp()
    assert len(otp) == 6
    assert otp.isdigit()
    assert len(hash_val) == 64  # SHA256 hash


def test_rate_limiting():
    # Test phone rate limiting
    result1 = otp_service.create_otp('+15551234567', 'phone', 'test')
    result2 = otp_service.create_otp('+15551234567', 'phone', 'test')
    
    assert result1['success']
    assert not result2['success']
    assert 'wait' in result2['error'].lower()


def test_otp_verification():
    # Create OTP
    result = otp_service.create_otp('+15551234567', 'phone', 'test')
    assert result['success']
    
    # Get OTP from database (for testing only)
    # In production, user receives OTP via SMS
    
    # Verify correct OTP
    verify_result = otp_service.verify_otp('+15551234567', 'correct_otp', 'test')
    assert verify_result['success']
    
    # Verify wrong OTP
    verify_result2 = otp_service.verify_otp('+15551234567', '000000', 'test')
    assert not verify_result2['success']