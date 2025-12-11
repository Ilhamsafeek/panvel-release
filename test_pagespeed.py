"""
Test Google PageSpeed Insights API
"""
import requests

# Your API key
API_KEY = "AIzaSyDw5QK2VfyUBV8SKCwkBfxaXYPg4GrbKCw"

# Test URL
test_url = "https://panvel-iq.calim.ai"

# API endpoint
api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

params = {
    'url': test_url,
    'key': API_KEY,
    'category': 'performance',
    'strategy': 'mobile'
}

print(f"Testing PageSpeed API with URL: {test_url}")
print("Making API request...")

try:
    response = requests.get(api_url, params=params, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        
        # Extract performance score
        lighthouse_result = data.get('lighthouseResult', {})
        categories = lighthouse_result.get('categories', {})
        performance = categories.get('performance', {})
        score = performance.get('score', 0)
        
        # Convert to 0-100 scale
        pagespeed_score = round(score * 100, 1)
        
        print(f"\n SUCCESS!")
        print(f"PageSpeed Score: {pagespeed_score}/100")
        print(f"API is working correctly!")
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\n❌ EXCEPTION: {str(e)}")