from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

print("=" * 50)
print("TESTING TWILIO SMS CONFIGURATION")
print("=" * 50)
print(f"Account SID: {TWILIO_ACCOUNT_SID[:10]}..." if TWILIO_ACCOUNT_SID else "NOT SET")
print(f"Auth Token: {'SET' if TWILIO_AUTH_TOKEN else 'NOT SET'}")
print(f"From Number: {TWILIO_PHONE_NUMBER}")
print("=" * 50)

# ENTER YOUR PHONE NUMBER HERE
test_phone = input("\nEnter your phone number (with country code, e.g., +1234567890): ")

try:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    print(f"\n📱 Sending SMS to {test_phone}...")
    message = client.messages.create(
        body="Test SMS from PanvelIQ. Your OTP code: 123456",
        from_=TWILIO_PHONE_NUMBER,
        to=test_phone
    )
    
    print(f"\n✅ SMS SENT SUCCESSFULLY!")
    print(f"✅ Message SID: {message.sid}")
    print(f"✅ Status: {message.status}")
    print(f"✅ Check your phone: {test_phone}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()