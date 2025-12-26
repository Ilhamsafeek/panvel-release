"""
OTP Service for Email and SMS verification
"""
import random
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import pymysql
from twilio.rest import Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings
from app.core.security import get_db_connection


class OTPService:
    """Handles OTP generation, delivery, and verification"""
    
    def __init__(self):
        # Twilio configuration
        self.twilio_client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        self.twilio_phone = settings.TWILIO_PHONE_NUMBER
        
        # Rate limiting
        self.MAX_ATTEMPTS = 5
        self.RATE_LIMIT_WINDOW = 90  # seconds between OTP requests
        self.OTP_EXPIRY_MINUTES = 10
        self.BLACKLIST_DURATION_HOURS = 24
    
    def generate_otp(self, length: int = 6) -> Tuple[str, str]:
        """
        Generate cryptographically secure OTP
        Returns: (otp_code, otp_hash)
        """
        otp = ''.join([str(random.SystemRandom().randint(0, 9)) for _ in range(length)])
        
        # Create HMAC hash for secure storage
        salt = settings.SECRET_KEY.encode()
        otp_hash = hmac.new(salt, otp.encode(), hashlib.sha256).hexdigest()
        
        return otp, otp_hash
    
    def check_rate_limit(self, identifier: str, identifier_type: str) -> Dict:
        """Check if identifier is rate-limited"""
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        try:
            # Check blacklist
            cursor.execute("""
                SELECT * FROM otp_blacklist 
                WHERE identifier = %s 
                AND identifier_type = %s 
                AND blocked_until > NOW()
            """, (identifier, identifier_type))
            
            if cursor.fetchone():
                return {
                    'allowed': False,
                    'reason': 'Too many failed attempts. Try again later.'
                }
            
            # Check recent OTP requests (rate limiting)
            cursor.execute("""
                SELECT created_at FROM otp_verifications 
                WHERE (phone = %s OR email = %s)
                ORDER BY created_at DESC 
                LIMIT 1
            """, (identifier, identifier))
            
            recent = cursor.fetchone()
            if recent:
                time_diff = (datetime.now() - recent['created_at']).total_seconds()
                if time_diff < self.RATE_LIMIT_WINDOW:
                    return {
                        'allowed': False,
                        'reason': f'Please wait {int(self.RATE_LIMIT_WINDOW - time_diff)} seconds before requesting another OTP.'
                    }
            
            return {'allowed': True}
            
        finally:
            cursor.close()
            connection.close()

    def send_sms_otp(self, phone: str, otp: str, purpose: str = 'verification') -> Dict:
        """Send OTP via SMS using Twilio"""
        try:
            print(f"📱 [SMS OTP] Attempting to send OTP to: {phone}")
            print(f"📱 [SMS OTP] OTP Code: {otp}")
            print(f"📱 [SMS OTP] Twilio Config:")
            print(f"   - Account SID: {settings.TWILIO_ACCOUNT_SID[:10]}..." if settings.TWILIO_ACCOUNT_SID else "   - Account SID: NOT SET")
            print(f"   - Auth Token: {'SET' if settings.TWILIO_AUTH_TOKEN else 'NOT SET'}")
            print(f"   - From Number: {settings.TWILIO_PHONE_NUMBER}")
            
            message = self.twilio_client.messages.create(
                body=f"Your PanvelIQ verification code is: {otp}. Valid for {self.OTP_EXPIRY_MINUTES} minutes. Do not share this code.",
                from_=self.twilio_phone,
                to=phone
            )
            
            print(f"✅ [SMS OTP] SMS sent successfully. Message SID: {message.sid}")
            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status
            }
            
        except Exception as e:
            print(f"❌ [SMS OTP] Failed to send: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
            

    def send_email_otp(self, email: str, otp: str, purpose: str = 'verification') -> Dict:
        """Send OTP via Email"""
        try:
            print(f"📧 [EMAIL OTP] Attempting to send OTP to: {email}")
            print(f"📧 [EMAIL OTP] OTP Code: {otp}")
            print(f"📧 [EMAIL OTP] SMTP Config:")
            print(f"   - Host: {settings.SMTP_HOST}")
            print(f"   - Port: {settings.SMTP_PORT}")
            print(f"   - Username: {settings.SMTP_USERNAME}")
            print(f"   - Password: {'SET' if settings.SMTP_PASSWORD else 'NOT SET'}")
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'PanvelIQ Verification Code - {otp}'
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = email
            
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #9926F3, #1DD8FC); padding: 40px; border-radius: 10px;">
                    <h1 style="color: white; text-align: center;">PanvelIQ Verification</h1>
                    <div style="background: white; padding: 30px; border-radius: 8px; margin-top: 20px;">
                        <p>Your verification code is:</p>
                        <h2 style="text-align: center; font-size: 36px; letter-spacing: 8px; color: #9926F3;">{otp}</h2>
                        <p style="color: #666; font-size: 14px;">This code will expire in {self.OTP_EXPIRY_MINUTES} minutes.</p>
                        <p style="color: #666; font-size: 14px;">If you didn't request this code, please ignore this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            print(f"📧 [EMAIL OTP] Connecting to SMTP server...")
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                print(f"📧 [EMAIL OTP] Starting TLS...")
                server.starttls()
                print(f"📧 [EMAIL OTP] Logging in...")
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                print(f"📧 [EMAIL OTP] Sending email...")
                server.send_message(msg)
            
            print(f"✅ [EMAIL OTP] Email sent successfully to {email}")
            return {'success': True}
            
        except Exception as e:
            print(f"❌ [EMAIL OTP] Failed to send: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def create_otp(
        self,
        identifier: str,
        identifier_type: str,
        purpose: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> Dict:
        """
        Create and send OTP
        identifier_type: 'phone' or 'email'
        """
        # Rate limit check
        rate_check = self.check_rate_limit(identifier, identifier_type)
        if not rate_check['allowed']:
            return {'success': False, 'error': rate_check['reason']}
        
        # Generate OTP
        otp_code, otp_hash = self.generate_otp()
        expires_at = datetime.now() + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
        
        # Save to database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO otp_verifications 
                (user_id, phone, email, otp_code, otp_hash, purpose, expires_at, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                identifier if identifier_type == 'phone' else None,
                identifier if identifier_type == 'email' else None,
                otp_code,  # Store for development; remove in production
                otp_hash,
                purpose,
                expires_at,
                ip_address
            ))
            connection.commit()
            otp_id = cursor.lastrowid
            
            # Send OTP
            if identifier_type == 'phone':
                send_result = self.send_sms_otp(identifier, otp_code, purpose)
            else:
                send_result = self.send_email_otp(identifier, otp_code, purpose)
            
            if send_result['success']:
                return {
                    'success': True,
                    'otp_id': otp_id,
                    'expires_in_minutes': self.OTP_EXPIRY_MINUTES,
                    'message': f'OTP sent to {identifier}'
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to send OTP: {send_result.get("error")}'
                }
                
        except Exception as e:
            connection.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            cursor.close()
            connection.close()
    
    def verify_otp(
        self,
        identifier: str,
        otp_code: str,
        purpose: str
    ) -> Dict:
        """Verify OTP code"""
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        try:
            # Fetch latest unverified OTP
            cursor.execute("""
                SELECT * FROM otp_verifications 
                WHERE (phone = %s OR email = %s)
                AND purpose = %s
                AND verified = FALSE
                AND expires_at > NOW()
                AND attempts < %s
                ORDER BY created_at DESC 
                LIMIT 1
            """, (identifier, identifier, purpose, self.MAX_ATTEMPTS))
            
            otp_record = cursor.fetchone()
            
            if not otp_record:
                return {
                    'success': False,
                    'error': 'Invalid or expired OTP'
                }
            
            # Verify OTP
            salt = settings.SECRET_KEY.encode()
            provided_hash = hmac.new(salt, otp_code.encode(), hashlib.sha256).hexdigest()
            
            # Increment attempts
            cursor.execute("""
                UPDATE otp_verifications 
                SET attempts = attempts + 1 
                WHERE otp_id = %s
            """, (otp_record['otp_id'],))
            
            if provided_hash == otp_record['otp_hash']:
                # Success - mark as verified
                cursor.execute("""
                    UPDATE otp_verifications 
                    SET verified = TRUE, verified_at = NOW()
                    WHERE otp_id = %s
                """, (otp_record['otp_id'],))
                
                # Update user verification status
                if otp_record['user_id']:
                    if otp_record['phone']:
                        cursor.execute(
                            "UPDATE users SET phone_verified = TRUE WHERE user_id = %s",
                            (otp_record['user_id'],)
                        )
                    if otp_record['email']:
                        cursor.execute(
                            "UPDATE users SET email_verified = TRUE WHERE user_id = %s",
                            (otp_record['user_id'],)
                        )
                
                connection.commit()
                
                return {
                    'success': True,
                    'message': 'OTP verified successfully',
                    'user_id': otp_record['user_id']
                }
            else:
                # Failed attempt
                remaining_attempts = self.MAX_ATTEMPTS - (otp_record['attempts'] + 1)
                
                if remaining_attempts <= 0:
                    # Blacklist this identifier
                    identifier_val = otp_record['phone'] or otp_record['email']
                    identifier_type = 'phone' if otp_record['phone'] else 'email'
                    blocked_until = datetime.now() + timedelta(hours=self.BLACKLIST_DURATION_HOURS)
                    
                    cursor.execute("""
                        INSERT INTO otp_blacklist (identifier, identifier_type, reason, blocked_until)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE blocked_until = %s
                    """, (
                        identifier_val,
                        identifier_type,
                        'Too many failed OTP attempts',
                        blocked_until,
                        blocked_until
                    ))
                    
                    connection.commit()
                    
                    return {
                        'success': False,
                        'error': f'Too many failed attempts. Account locked for {self.BLACKLIST_DURATION_HOURS} hours.'
                    }
                
                connection.commit()
                
                return {
                    'success': False,
                    'error': f'Invalid OTP. {remaining_attempts} attempts remaining.'
                }
                
        except Exception as e:
            connection.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            cursor.close()
            connection.close()


# Initialize service
otp_service = OTPService()