#!/usr/bin/env python3
"""
Test Google Search Console Credentials
This will tell us exactly what's wrong
"""

import json
import base64
import os
import sys

print("="*70)
print("Google Search Console Credentials Diagnostic Test")
print("="*70)

# Step 1: Load environment variables
print("\n[1] Loading environment variables...")
from dotenv import load_dotenv
load_dotenv()

GA4_CREDENTIALS_BASE64 = os.getenv('GA4_CREDENTIALS_BASE64')

if not GA4_CREDENTIALS_BASE64:
    print("❌ ERROR: GA4_CREDENTIALS_BASE64 not found in environment")
    print("   Check your .env file")
    sys.exit(1)

print(f"✅ Found GA4_CREDENTIALS_BASE64 (length: {len(GA4_CREDENTIALS_BASE64)} chars)")

# Step 2: Decode base64
print("\n[2] Decoding base64...")
try:
    decoded = base64.b64decode(GA4_CREDENTIALS_BASE64)
    print(f"✅ Base64 decoded successfully ({len(decoded)} bytes)")
except Exception as e:
    print(f"❌ Base64 decode failed: {e}")
    sys.exit(1)

# Step 3: Parse JSON
print("\n[3] Parsing JSON...")
try:
    credentials_json = json.loads(decoded)
    print("✅ JSON parsed successfully")
    print(f"   Project ID: {credentials_json.get('project_id')}")
    print(f"   Client Email: {credentials_json.get('client_email')}")
except Exception as e:
    print(f"❌ JSON parse failed: {e}")
    sys.exit(1)

# Step 4: Check private key
print("\n[4] Checking private key...")
private_key = credentials_json.get('private_key', '')

print(f"   Private key length: {len(private_key)} chars")
print(f"   First 50 chars: {private_key[:50]}")
print(f"   Last 50 chars: {private_key[-50:]}")

# Check for escaped newlines
if '\\n' in private_key:
    print("   ⚠️  WARNING: Found escaped newlines (\\n)")
    print("   Converting to actual newlines...")
    private_key = private_key.replace('\\n', '\n')
    credentials_json['private_key'] = private_key
    print("   ✅ Converted escaped newlines")
else:
    print("   ✅ No escaped newlines found")

# Validate format
if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
    print(f"   ❌ ERROR: Invalid header. Starts with: {private_key[:30]}")
    sys.exit(1)

if not private_key.strip().endswith('-----END PRIVATE KEY-----'):
    print(f"   ❌ ERROR: Invalid footer. Ends with: {private_key[-30:]}")
    sys.exit(1)

print("   ✅ Private key format looks valid")

# Step 5: Test credential creation
print("\n[5] Testing credential creation...")
try:
    from google.oauth2 import service_account
    
    credentials = service_account.Credentials.from_service_account_info(
        credentials_json,
        scopes=['https://www.googleapis.com/auth/webmasters.readonly']
    )
    
    print("   ✅ SUCCESS! Credentials created successfully")
    print(f"   Service Account: {credentials.service_account_email}")
    print(f"   Project ID: {credentials.project_id}")
    
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    print("\n" + "="*70)
    print("ERROR DETAILS:")
    print("="*70)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 6: Test API service creation
print("\n[6] Testing Search Console API service...")
try:
    from googleapiclient.discovery import build
    
    service = build('searchconsole', 'v1', credentials=credentials)
    print("   ✅ SUCCESS! Search Console service created")
    
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Success!
print("\n" + "="*70)
print("✅ ALL TESTS PASSED!")
print("="*70)
print("\nYour Google Search Console credentials are working correctly.")
print("The issue must be in how the application is loading them.\n")