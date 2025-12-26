import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL')

print("=" * 50)
print("TESTING EMAIL CONFIGURATION")
print("=" * 50)
print(f"Host: {SMTP_HOST}")
print(f"Port: {SMTP_PORT}")
print(f"Username: {SMTP_USERNAME}")
print(f"Password: {'*' * len(SMTP_PASSWORD) if SMTP_PASSWORD else 'NOT SET'}")
print(f"From: {SMTP_FROM_EMAIL}")
print("=" * 50)

try:
    msg = MIMEMultipart()
    msg['Subject'] = 'Test Email from PanvelIQ'
    msg['From'] = SMTP_FROM_EMAIL
    msg['To'] = "karumpulihero@gmail.com"  # Send to yourself
    
    html = """
    <html>
    <body>
        <h1>Test Email</h1>
        <p>If you received this, your SMTP configuration is working!</p>
        <p>Your OTP code: <strong>123456</strong></p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html, 'html'))
    
    print("\n📧 Connecting to SMTP server...")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.set_debuglevel(1)  # Show detailed output
        print("📧 Starting TLS...")
        server.starttls()
        print("📧 Logging in...")
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        print("📧 Sending email...")
        server.send_message(msg)
    
    print("\n✅ EMAIL SENT SUCCESSFULLY!")
    print(f"✅ Check your inbox: {SMTP_USERNAME}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()