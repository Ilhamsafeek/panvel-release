import requests
import base64

# Your credentials
MOZ_ACCESS_ID = "mozscape-h4VjYyvy9k"
MOZ_SECRET_KEY = "iFOG6Vfavzi8ejNwG3vm5pIpnc8g5hQZ"

# Create Basic Auth header
credentials = f"{MOZ_ACCESS_ID}:{MOZ_SECRET_KEY}"
encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
auth_header = f"Basic {encoded}"

print(f"Auth Header: {auth_header}")

# Test Moz API
url = "https://lsapi.seomoz.com/v2/url_metrics"
headers = {
    "Authorization": auth_header,
    "Content-Type": "application/json"
}
payload = {
    "targets": ["moz.com"]
}

print(f"\nCalling Moz API...")
response = requests.post(url, json=payload, headers=headers, timeout=30)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")