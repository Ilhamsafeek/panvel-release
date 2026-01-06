"""
Smart SEO Toolkit API Router - COMPLETE FIX
File: app/api/v1/endpoints/seo.py

Fixes:
1. Domain Authority Audit - Real Moz API integration
2. Backlinks Audit - Real Moz API integration
3. Overall SEO Score Audit - Combined technical audit
4. Site Performance Audit - PageSpeed Insights integration
5. Usability Record Counts - Part of SEO audit
6. Keyword Tracking with position changes, volume, difficulty
7. Backlink Strategist - Suggest outreach targets with DA scoring
8. SERP Tracker Bug - Fixed unique positions per keyword
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import json
import pymysql
import requests
import hashlib
import hmac
import base64
import time
import random

from app.core.config import settings
from app.core.security import get_current_user, get_db_connection

from google.oauth2 import service_account
from googleapiclient.discovery import build

# OpenAI client
try:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
except:
    client = None

router = APIRouter()


# ========== PYDANTIC MODELS ==========

class SEOProjectCreate(BaseModel):
    website_url: str
    target_keywords: List[str] = []
    
    @validator('website_url')
    def validate_url(cls, v):
        # Clean and validate URL
        v = v.strip()
        if not v.startswith(('http://', 'https://')):
            v = f"https://{v}"
        return v

class ContentOptimizationRequest(BaseModel):
    content: str
    target_keyword: str
    content_type: str = "blog"

class TechnicalAuditRequest(BaseModel):
    seo_project_id: int

class BacklinkOutreachRequest(BaseModel):
    seo_project_id: int
    target_url: str
    anchor_text: str
    
    @validator('target_url')
    def validate_target_url(cls, v):
        v = v.strip()
        if not v.startswith(('http://', 'https://')):
            v = f"https://{v}"
        return v

class KeywordTrackingRequest(BaseModel):
    seo_project_id: int
    keyword: str

class VoiceSearchRequest(BaseModel):
    content: str

class BacklinkTargetRequest(BaseModel):
    seo_project_id: int
    niche: str
    min_da: int = 30


# ========== MOZ API HELPER FUNCTIONS ==========

def get_moz_auth_header() -> str:
    """Generate Moz API v2 authentication header - Simple Basic Auth"""
    access_id = settings.MOZ_ACCESS_ID
    secret_key = settings.MOZ_SECRET_KEY
    # Moz API v2 uses simple Basic Auth: base64(access_id:secret_key)
    credentials = f"{access_id}:{secret_key}"
    encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    return f"Basic {encoded}"


def get_moz_url_metrics(url: str) -> Dict[str, Any]:
    """
    Get domain authority and metrics from Moz API
    Returns error state if API fails - no fake data
    """
    try:
        if not settings.MOZ_ACCESS_ID or not settings.MOZ_SECRET_KEY:
            return {
                'success': False, 
                'error': 'Moz API credentials not configured',
                'domain_authority': 0,
                'page_authority': 0,
                'spam_score': 0
            }
        
        endpoint = "https://lsapi.seomoz.com/v2/url_metrics"
        headers = {
            "Authorization": get_moz_auth_header(),
            "Content-Type": "application/json"
        }
        
        # Ensure URL has protocol
        if not url.startswith('http'):
            url = f"https://{url}"
        
        payload = {"targets": [url]}
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f'Moz API Error: {response.status_code} - {response.text[:200]}',
                'domain_authority': 0,
                'page_authority': 0,
                'spam_score': 0
            }
        
        data = response.json()
        
        if data.get('results') and len(data['results']) > 0:
            result = data['results'][0]
            return {
                'success': True,
                'url': url,
                'domain_authority': result.get('domain_authority', 0),
                'page_authority': result.get('page_authority', 0),
                'spam_score': result.get('spam_score', 0),
                'root_domains_to_page': result.get('root_domains_to_page', 0),
                'external_pages_to_page': result.get('external_pages_to_page', 0),
                'linking_domains': result.get('root_domains_to_root_domain', 0),
                'total_backlinks': result.get('external_pages_to_root_domain', 0),
                'last_crawled': result.get('last_crawled', None),
                'source': 'moz_api'
            }
        
        return {
            'success': False, 
            'error': 'No data returned from Moz',
            'domain_authority': 0,
            'page_authority': 0,
            'spam_score': 0
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False, 
            'error': f'Moz API Error: {str(e)}',
            'domain_authority': 0,
            'page_authority': 0,
            'spam_score': 0
        }
    except Exception as e:
        return {
            'success': False, 
            'error': str(e),
            'domain_authority': 0,
            'page_authority': 0,
            'spam_score': 0
        }


def get_moz_backlinks(url: str, limit: int = 50) -> Dict[str, Any]:
    """
    Get backlink data from Moz API
    Returns error state if API fails - no fake data
    """
    try:
        if not settings.MOZ_ACCESS_ID or not settings.MOZ_SECRET_KEY:
            return {
                'success': False, 
                'error': 'Moz API credentials not configured',
                'backlinks': [],
                'total_backlinks': 0,
                'unique_domains': 0
            }
        
        endpoint = "https://lsapi.seomoz.com/v2/anchor_text"
        headers = {
            "Authorization": get_moz_auth_header(),
            "Content-Type": "application/json"
        }
        
        if not url.startswith('http'):
            url = f"https://{url}"
        
        payload = {
            "target": url,
            "scope": "root_domain",
            "limit": limit
        }
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f'Moz API Error: {response.status_code}',
                'backlinks': [],
                'total_backlinks': 0,
                'unique_domains': 0
            }
        
        data = response.json()
        
        backlinks = []
        total_backlinks = 0
        
        if data.get('results'):
            for result in data['results']:
                backlinks.append({
                    'anchor_text': result.get('anchor_text', ''),
                    'external_pages': result.get('external_pages', 0),
                    'external_root_domains': result.get('external_root_domains', 0),
                    'deleted_pages': result.get('deleted_pages', 0)
                })
                total_backlinks += result.get('external_pages', 0)
        
        return {
            'success': True,
            'url': url,
            'total_backlinks': total_backlinks,
            'unique_domains': len(backlinks),
            'backlinks': backlinks,
            'source': 'moz_api'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'backlinks': [],
            'total_backlinks': 0,
            'unique_domains': 0
        }


def get_moz_top_pages(domain: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get top pages from Moz API"""
    try:
        if not settings.MOZ_ACCESS_ID or not settings.MOZ_SECRET_KEY:
            return []
        
        endpoint = "https://lsapi.seomoz.com/v2/top_pages"
        headers = {
            "Authorization": get_moz_auth_header(),
            "Content-Type": "application/json"
        }
        
        if not domain.startswith('http'):
            domain = f"https://{domain}"
        
        payload = {"target": domain, "limit": limit}
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        top_pages = []
        if data.get('results'):
            for page in data['results']:
                top_pages.append({
                    'url': page.get('page', ''),
                    'page_authority': page.get('page_authority', 0),
                    'external_links': page.get('external_pages_to_page', 0),
                    'root_domains_linking': page.get('root_domains_to_page', 0)
                })
        
        return top_pages
        
    except Exception as e:
        return []


# ========== PAGESPEED INSIGHTS ==========

def get_pagespeed_insights(url: str, strategy: str = "mobile") -> Dict[str, Any]:
    """
    Get REAL PageSpeed Insights data from Google API
    """
    try:
        api_key = getattr(settings, 'PAGESPEED_API_KEY', None) or getattr(settings, 'GOOGLE_API_KEY', None)
        if not api_key:
            return {'success': False, 'error': 'PageSpeed API key not configured'}
        
        if not url.startswith('http'):
            url = f"https://{url}"
        
        endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        
        # Build URL manually to handle multiple category params correctly
        categories = ['performance', 'accessibility', 'best-practices', 'seo']
        category_params = '&'.join([f'category={cat}' for cat in categories])
        
        full_url = f"{endpoint}?url={requests.utils.quote(url, safe='')}&key={api_key}&strategy={strategy}&{category_params}"
        
        response = requests.get(full_url, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        lighthouse = data.get('lighthouseResult', {})
        categories_data = lighthouse.get('categories', {})
        audits = lighthouse.get('audits', {})
        
        # Extract Core Web Vitals
        fcp = audits.get('first-contentful-paint', {}).get('numericValue', 0)
        lcp = audits.get('largest-contentful-paint', {}).get('numericValue', 0)
        cls = audits.get('cumulative-layout-shift', {}).get('numericValue', 0)
        tbt = audits.get('total-blocking-time', {}).get('numericValue', 0)
        si = audits.get('speed-index', {}).get('numericValue', 0)
        
        return {
            'success': True,
            'url': url,
            'strategy': strategy,
            'performance_score': int(categories_data.get('performance', {}).get('score', 0) * 100),
            'accessibility_score': int(categories_data.get('accessibility', {}).get('score', 0) * 100),
            'best_practices_score': int(categories_data.get('best-practices', {}).get('score', 0) * 100),
            'seo_score': int(categories_data.get('seo', {}).get('score', 0) * 100),
            'core_web_vitals': {
                'first_contentful_paint': round(fcp / 1000, 2) if fcp else 0,
                'largest_contentful_paint': round(lcp / 1000, 2) if lcp else 0,
                'cumulative_layout_shift': round(cls, 3) if cls else 0,
                'total_blocking_time': round(tbt, 0) if tbt else 0,
                'speed_index': round(si / 1000, 2) if si else 0
            },
            'diagnostics': {
                'render_blocking_resources': len(audits.get('render-blocking-resources', {}).get('details', {}).get('items', [])),
                'unused_css': audits.get('unused-css-rules', {}).get('details', {}).get('overallSavingsBytes', 0),
                'unused_javascript': audits.get('unused-javascript', {}).get('details', {}).get('overallSavingsBytes', 0),
                'image_optimization': audits.get('uses-optimized-images', {}).get('details', {}).get('overallSavingsBytes', 0)
            }
        }
        
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'PageSpeed API Error: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}



def get_search_console_service():
    """Initialize Google Search Console API service - REAL IMPLEMENTATION"""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        import base64
        import tempfile
        import os
        
        # Try base64 first, then fall back to JSON
        credentials_json = None
        
        # Option 1: Base64 encoded (RECOMMENDED)
        if hasattr(settings, 'GA4_CREDENTIALS_BASE64') and settings.GA4_CREDENTIALS_BASE64:
            try:
                decoded = base64.b64decode(settings.GA4_CREDENTIALS_BASE64)
                credentials_json = json.loads(decoded)
                print("✅ Credentials loaded from base64")
            except Exception as e:
                print(f"❌ Failed to decode base64 credentials: {str(e)}")
        
        # Option 2: Direct JSON (fallback)
        if not credentials_json and hasattr(settings, 'GA4_CREDENTIALS_JSON') and settings.GA4_CREDENTIALS_JSON:
            try:
                credentials_json = json.loads(settings.GA4_CREDENTIALS_JSON)
                print("✅ Credentials loaded from JSON")
            except Exception as e:
                print(f"❌ Failed to parse JSON credentials: {str(e)}")
        
        if not credentials_json:
            print("❌ No valid credentials found")
            return None
        
        # ========== CRITICAL FIX: Handle private key newlines ==========
        if 'private_key' in credentials_json:
            private_key = credentials_json['private_key']
            
            # Debug: Show first 100 chars of key BEFORE fix
            print(f"🔍 Private key BEFORE fix (first 100 chars): {private_key[:100]}")
            
            # Check if key contains escaped newlines
            if '\\n' in private_key:
                print("⚠️  Found escaped newlines (\\n) - converting to actual newlines")
                private_key = private_key.replace('\\n', '\n')
                credentials_json['private_key'] = private_key
                print("✅ Converted escaped newlines to actual newlines")
            else:
                print("ℹ️  No escaped newlines found")
            
            # Debug: Show first 100 chars AFTER fix
            print(f"🔍 Private key AFTER fix (first 100 chars): {private_key[:100]}")
            
            # Validate key format
            if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                print(f"❌ Invalid private key format - missing header")
                print(f"   Key starts with: {private_key[:50]}")
                return None
            
            if not private_key.strip().endswith('-----END PRIVATE KEY-----'):
                print(f"❌ Invalid private key format - missing footer")
                print(f"   Key ends with: {private_key[-50:]}")
                return None
            
            print(f"✅ Private key format validated (total length: {len(private_key)} chars)")
        
        # Try creating credentials directly first
        try:
            print("🔄 Attempting direct credential creation...")
            credentials = service_account.Credentials.from_service_account_info(
                credentials_json,
                scopes=['https://www.googleapis.com/auth/webmasters.readonly']
            )
            print("✅ Service account credentials created successfully (direct method)")
        
        except Exception as direct_error:
            print(f"⚠️  Direct method failed: {str(direct_error)}")
            print("🔄 Trying temporary file workaround...")
            
            # Workaround: Use temporary file method
            temp_file = None
            try:
                # Create a temporary file with the credentials
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                    json.dump(credentials_json, tmp, indent=2)
                    temp_file = tmp.name
                    print(f"✅ Created temp credentials file: {temp_file}")
                
                # Load credentials from file
                credentials = service_account.Credentials.from_service_account_file(
                    temp_file,
                    scopes=['https://www.googleapis.com/auth/webmasters.readonly']
                )
                print("✅ Service account credentials created successfully (temp file method)")
                
            finally:
                # Clean up temp file
                if temp_file and os.path.exists(temp_file):
                    os.unlink(temp_file)
                    print(f"🗑️  Cleaned up temp file: {temp_file}")
        
        # Build and return the Search Console service
        service = build('searchconsole', 'v1', credentials=credentials)
        print("✅ Google Search Console service initialized successfully")
        return service
        
    except Exception as e:
        print(f"❌ Google Search Console service initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def get_keyword_position_from_gsc(site_url: str, keyword: str) -> Optional[float]:
    """Get actual keyword position from Google Search Console - REAL DATA ONLY"""
    try:
        service = get_search_console_service()
        if not service:
            return None  # GSC not configured
        
        if not site_url.startswith(('sc-domain:', 'http://', 'https://')):
            site_url = f"https://{site_url}"
        
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        request_body = {
            'startDate': start_date.isoformat(),
            'endDate': end_date.isoformat(),
            'dimensions': ['query'],
            'dimensionFilterGroups': [{
                'filters': [{
                    'dimension': 'query',
                    'operator': 'equals',
                    'expression': keyword.lower()
                }]
            }],
            'rowLimit': 1
        }
        
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body=request_body
        ).execute()
        
        if 'rows' in response and len(response['rows']) > 0:
            position = response['rows'][0].get('position', None)
            return round(position, 1) if position is not None else None
        
        return None
        
    except Exception:
        # Silent fail - any GSC error
        return None



async def get_keyword_position_serp(website_url: str, keyword: str) -> Dict[str, Any]:
    """
    Get REAL keyword position using Google Search Console + Moz APIs
    NO FAKE DATA - uses actual API integrations
    """
    try:
        clean_url = website_url.replace('http://', '').replace('https://', '').replace('www.', '')
        
        # 1. Get REAL position from Google Search Console
        gsc_position = get_keyword_position_from_gsc(website_url, keyword)
        
        # 2. Get domain authority from Moz
        moz_data = get_moz_url_metrics(clean_url)
        domain_authority = moz_data.get('domain_authority', 0) if moz_data.get('success') else 0
        
        # 3. Estimate search volume and difficulty using AI (estimation only, not position)
        search_volume = 0
        difficulty = 50
        cpc = 0.0
        
        if client:
            try:
                prompt = f"""Analyze the keyword "{keyword}" and provide realistic SEO metrics.
Return ONLY a JSON object with:
- search_volume: monthly search volume (integer)
- difficulty: 1-100 score
- cpc: estimated cost per click in USD

Return ONLY valid JSON, no markdown."""

                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an SEO expert. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                
                response_text = response.choices[0].message.content.strip()
                if response_text.startswith('```'):
                    response_text = response_text.split('```')[1]
                    if response_text.startswith('json'):
                        response_text = response_text[4:]
                    response_text = response_text.strip()
                
                metrics = json.loads(response_text)
                search_volume = metrics.get('search_volume', 0)
                difficulty = metrics.get('difficulty', 50)
                cpc = metrics.get('cpc', 0.0)
                
            except Exception as ai_error:
                print(f"AI estimation error: {ai_error}")
        
        # 4. Return with transparent data sources
        return {
            'position': gsc_position if gsc_position is not None else 0,
            'position_source': 'Google Search Console' if gsc_position is not None else 'Not Found',
            'search_volume': search_volume,
            'search_volume_source': 'AI Estimate' if search_volume > 0 else 'Unknown',
            'difficulty': difficulty,
            'difficulty_source': 'AI Estimate',
            'cpc': cpc,
            'cpc_source': 'AI Estimate' if cpc > 0 else 'Unknown',
            'domain_authority': domain_authority,
            'domain_authority_source': 'Moz API' if moz_data.get('success') else 'Not Available',
            'note': 'Position from Google Search Console (actual data)' if gsc_position else 'Keyword not currently ranking in Google Search Console'
        }
        
    except Exception as e:
        return {
            'position': 0,
            'position_source': 'Error',
            'search_volume': 0,
            'difficulty': 50,
            'cpc': 0.0,
            'domain_authority': 0,
            'error': str(e),
            'note': 'Failed to fetch keyword data from APIs'
        }


# ========== SEO PROJECTS ==========

@router.post("/projects/create")
async def create_seo_project(
    project: SEOProjectCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new SEO project with REAL domain authority from Moz"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get REAL domain authority from Moz API
        moz_data = get_moz_url_metrics(str(project.website_url))
        domain_authority = moz_data.get('domain_authority', 0) if moz_data.get('success') else 0
        
        client_id = current_user['user_id']
        
        query = """
            INSERT INTO seo_projects 
            (client_id, website_url, target_keywords, current_domain_authority, status)
            VALUES (%s, %s, %s, %s, 'active')
        """
        
        cursor.execute(query, (
            client_id,
            str(project.website_url),
            json.dumps(project.target_keywords),
            domain_authority
        ))
        connection.commit()
        
        project_id = cursor.lastrowid
        
        return {
            "success": True,
            "message": "SEO project created successfully",
            "seo_project_id": project_id,
            "domain_authority": domain_authority,
            "moz_data": moz_data if moz_data.get('success') else None
        }
    
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/projects/list")
async def list_seo_projects(current_user: dict = Depends(get_current_user)):
    """List all SEO projects for current user"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT seo_project_id, website_url, target_keywords, 
                   current_domain_authority, status, created_at
            FROM seo_projects 
            WHERE client_id = %s
            ORDER BY created_at DESC
        """
        
        cursor.execute(query, (current_user['user_id'],))
        projects = cursor.fetchall()
        
        for project in projects:
            if project['target_keywords']:
                project['target_keywords'] = json.loads(project['target_keywords'])
            if project['created_at']:
                project['created_at'] = project['created_at'].isoformat()
        
        return {"success": True, "projects": projects}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch projects: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@router.get("/debug/gsc-config")
async def debug_gsc_config(current_user: dict = Depends(get_current_user)):
    """Debug Google Search Console configuration"""
    return {
        "ga4_credentials_exists": bool(getattr(settings, 'GA4_CREDENTIALS_JSON', None)),
        "ga4_credentials_length": len(getattr(settings, 'GA4_CREDENTIALS_JSON', '')) if getattr(settings, 'GA4_CREDENTIALS_JSON', None) else 0,
        "search_console_creds_exists": bool(getattr(settings, 'SEARCH_CONSOLE_CREDENTIALS_JSON', None)),
        "google_api_key_exists": bool(settings.GOOGLE_API_KEY),
        "env_check": {
            "GA4_CREDENTIALS_JSON": "SET" if getattr(settings, 'GA4_CREDENTIALS_JSON', None) else "NOT SET"
        }
    }


# ========== COMPREHENSIVE SEO AUDIT ==========

@router.post("/audit/run")
async def run_comprehensive_audit(
    request: TechnicalAuditRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Run COMPREHENSIVE SEO audit including:
    - Domain Authority (Moz API)
    - Backlinks Analysis (Moz API)
    - Site Performance (PageSpeed Insights)
    - Overall SEO Score
    - Usability Metrics
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get project details
        cursor.execute(
            "SELECT website_url FROM seo_projects WHERE seo_project_id = %s AND client_id = %s",
            (request.seo_project_id, current_user['user_id'])
        )
        project = cursor.fetchone()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SEO project not found"
            )
        
        website_url = project['website_url']
        
        # 1. Get Moz Domain Authority & Backlinks
        moz_metrics = get_moz_url_metrics(website_url)
        backlink_data = get_moz_backlinks(website_url, limit=50)
        top_pages = get_moz_top_pages(website_url, limit=10)
        
        # 2. Get PageSpeed Insights (Mobile & Desktop)
        pagespeed_mobile = get_pagespeed_insights(website_url, 'mobile')
        pagespeed_desktop = get_pagespeed_insights(website_url, 'desktop')
        
        # 3. Calculate Overall SEO Score
        da_score = moz_metrics.get('domain_authority', 0) if moz_metrics.get('success') else 0
        performance_score = pagespeed_mobile.get('performance_score', 0) if pagespeed_mobile.get('success') else 0
        seo_lighthouse_score = pagespeed_mobile.get('seo_score', 0) if pagespeed_mobile.get('success') else 0
        
        # Weighted overall score
        overall_score = round(
            (da_score * 0.3) +  # Domain Authority: 30%
            (performance_score * 0.25) +  # Performance: 25%
            (seo_lighthouse_score * 0.25) +  # Lighthouse SEO: 25%
            (min(100, (backlink_data.get('unique_domains', 0) / 10) * 100) * 0.2)  # Backlinks: 20%
        )
        
        # 4. Build Technical Issues List
        technical_issues = []
        
        # Domain Authority Issues
        if da_score < 20:
            technical_issues.append({
                'category': 'Domain Authority',
                'severity': 'high',
                'issue': f'Low Domain Authority ({da_score}/100)',
                'recommendation': 'Build high-quality backlinks and improve content quality'
            })
        elif da_score < 40:
            technical_issues.append({
                'category': 'Domain Authority',
                'severity': 'medium',
                'issue': f'Moderate Domain Authority ({da_score}/100)',
                'recommendation': 'Focus on acquiring authoritative backlinks'
            })
        
        # Spam Score Issues
        spam_score = moz_metrics.get('spam_score', 0) if moz_metrics.get('success') else 0
        if spam_score > 30:
            technical_issues.append({
                'category': 'Spam Score',
                'severity': 'high',
                'issue': f'High Spam Score ({spam_score}%)',
                'recommendation': 'Audit and remove toxic backlinks'
            })
        
        # Performance Issues
        if pagespeed_mobile.get('success'):
            cwv = pagespeed_mobile.get('core_web_vitals', {})
            
            if cwv.get('largest_contentful_paint', 0) > 2.5:
                technical_issues.append({
                    'category': 'Core Web Vitals',
                    'severity': 'high',
                    'issue': f'Poor LCP ({cwv.get("largest_contentful_paint", 0)}s)',
                    'recommendation': 'Optimize images, preload critical resources'
                })
            
            if cwv.get('cumulative_layout_shift', 0) > 0.1:
                technical_issues.append({
                    'category': 'Core Web Vitals',
                    'severity': 'medium',
                    'issue': f'High CLS ({cwv.get("cumulative_layout_shift", 0)})',
                    'recommendation': 'Add size attributes to images and embeds'
                })
            
            if cwv.get('total_blocking_time', 0) > 200:
                technical_issues.append({
                    'category': 'Core Web Vitals',
                    'severity': 'medium',
                    'issue': f'High TBT ({cwv.get("total_blocking_time", 0)}ms)',
                    'recommendation': 'Reduce JavaScript execution time'
                })
            
            diag = pagespeed_mobile.get('diagnostics', {})
            if diag.get('render_blocking_resources', 0) > 3:
                technical_issues.append({
                    'category': 'Performance',
                    'severity': 'medium',
                    'issue': f'{diag.get("render_blocking_resources", 0)} render-blocking resources',
                    'recommendation': 'Defer non-critical CSS and JavaScript'
                })
        
        # Backlink Issues
        if backlink_data.get('unique_domains', 0) < 10:
            technical_issues.append({
                'category': 'Backlinks',
                'severity': 'medium',
                'issue': f'Low referring domains ({backlink_data.get("unique_domains", 0)})',
                'recommendation': 'Implement link building strategy'
            })
        
        # 5. Build Recommendations
        recommendations = []
        
        if da_score < 50:
            recommendations.append({
                'priority': 'high',
                'category': 'Off-Page SEO',
                'action': 'Build Quality Backlinks',
                'details': 'Focus on guest posting, broken link building, and creating linkable content'
            })
        
        if performance_score < 70:
            recommendations.append({
                'priority': 'high',
                'category': 'Performance',
                'action': 'Improve Page Speed',
                'details': 'Optimize images, enable compression, leverage browser caching'
            })
        
        if seo_lighthouse_score < 80:
            recommendations.append({
                'priority': 'medium',
                'category': 'Technical SEO',
                'action': 'Fix Technical Issues',
                'details': 'Ensure proper meta tags, structured data, and mobile-friendliness'
            })
        
        recommendations.append({
            'priority': 'medium',
            'category': 'Content',
            'action': 'Create High-Quality Content',
            'details': 'Publish comprehensive, well-researched content targeting long-tail keywords'
        })
        
        # 6. Save audit to database
        audit_data = {
            'overall_score': overall_score,
            'domain_authority': da_score,
            'page_authority': moz_metrics.get('page_authority', 0) if moz_metrics.get('success') else 0,
            'spam_score': spam_score,
            'total_backlinks': backlink_data.get('total_backlinks', 0),
            'referring_domains': backlink_data.get('unique_domains', 0),
            'performance_mobile': pagespeed_mobile.get('performance_score', 0) if pagespeed_mobile.get('success') else 0,
            'performance_desktop': pagespeed_desktop.get('performance_score', 0) if pagespeed_desktop.get('success') else 0,
            'seo_score': seo_lighthouse_score,
            'accessibility_score': pagespeed_mobile.get('accessibility_score', 0) if pagespeed_mobile.get('success') else 0
        }
        
        query = """
            INSERT INTO seo_audits 
            (seo_project_id, audit_date, overall_score, issues_found, recommendations, page_speed_score)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            request.seo_project_id,
            date.today(),
            overall_score,
            json.dumps(technical_issues),
            json.dumps(recommendations),
            performance_score
        ))
        
        # Update project domain authority
        cursor.execute(
            "UPDATE seo_projects SET current_domain_authority = %s WHERE seo_project_id = %s",
            (da_score, request.seo_project_id)
        )
        
        connection.commit()
        audit_id = cursor.lastrowid
        
        return {
            "success": True,
            "audit_id": audit_id,
            "website_url": website_url,
            "audit_date": date.today().isoformat(),
            "scores": {
                "overall_score": overall_score,
                "domain_authority": da_score,
                "page_authority": moz_metrics.get('page_authority', 0) if moz_metrics.get('success') else 0,
                "spam_score": spam_score,
                "performance_mobile": pagespeed_mobile.get('performance_score', 0) if pagespeed_mobile.get('success') else 0,
                "performance_desktop": pagespeed_desktop.get('performance_score', 0) if pagespeed_desktop.get('success') else 0,
                "seo_score": seo_lighthouse_score,
                "accessibility_score": pagespeed_mobile.get('accessibility_score', 0) if pagespeed_mobile.get('success') else 0,
                "best_practices_score": pagespeed_mobile.get('best_practices_score', 0) if pagespeed_mobile.get('success') else 0
            },
            "backlinks": {
                "total_backlinks": backlink_data.get('total_backlinks', 0),
                "referring_domains": backlink_data.get('unique_domains', 0),
                "top_anchor_texts": backlink_data.get('backlinks', [])[:10]
            },
            "core_web_vitals": pagespeed_mobile.get('core_web_vitals', {}) if pagespeed_mobile.get('success') else {},
            "top_pages": top_pages,
            "technical_issues": technical_issues,
            "recommendations": recommendations,
            "usability": {
                "mobile_friendly": pagespeed_mobile.get('performance_score', 0) >= 50 if pagespeed_mobile.get('success') else False,
                "accessibility_score": pagespeed_mobile.get('accessibility_score', 0) if pagespeed_mobile.get('success') else 0,
                "issues_count": len(technical_issues),
                "critical_issues": len([i for i in technical_issues if i['severity'] == 'high']),
                "warnings": len([i for i in technical_issues if i['severity'] == 'medium'])
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audit failed: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/audit/history/{project_id}")
async def get_audit_history(
    project_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get audit history for a project"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT audit_id, audit_date, overall_score, issues_found, 
                   recommendations, page_speed_score, created_at
            FROM seo_audits
            WHERE seo_project_id = %s
            ORDER BY audit_date DESC
            LIMIT 10
        """
        
        cursor.execute(query, (project_id,))
        audits = cursor.fetchall()
        
        for audit in audits:
            if audit['issues_found']:
                audit['issues_found'] = json.loads(audit['issues_found'])
            if audit['recommendations']:
                audit['recommendations'] = json.loads(audit['recommendations'])
            if audit['audit_date']:
                audit['audit_date'] = audit['audit_date'].isoformat()
            if audit['created_at']:
                audit['created_at'] = audit['created_at'].isoformat()
        
        return {"success": True, "audits": audits}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch audits: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== KEYWORD TRACKING - FIXED ==========

@router.post("/keywords/track")
async def track_keyword(
    request: KeywordTrackingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Track keyword with UNIQUE position per keyword (FIXED BUG)
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get project details
        cursor.execute(
            "SELECT website_url FROM seo_projects WHERE seo_project_id = %s AND client_id = %s",
            (request.seo_project_id, current_user['user_id'])
        )
        project = cursor.fetchone()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SEO project not found"
            )
        
        website_url = project['website_url']
        
        # Get UNIQUE keyword position and metrics
        keyword_data = await get_keyword_position_serp(website_url, request.keyword)
        
        current_position = keyword_data['position']
        search_volume = keyword_data['search_volume']
        difficulty = keyword_data.get('difficulty', 50)
        
        # Check for existing keyword to track position changes
        cursor.execute("""
            SELECT keyword_id, current_position 
            FROM keyword_tracking 
            WHERE seo_project_id = %s AND keyword = %s
            ORDER BY tracked_date DESC
            LIMIT 1
        """, (request.seo_project_id, request.keyword))
        
        existing = cursor.fetchone()
        previous_position = existing['current_position'] if existing else None
        position_change = (previous_position - current_position) if previous_position else 0
        
        # Save tracking data
        query = """
            INSERT INTO keyword_tracking 
            (seo_project_id, keyword, search_volume, current_position, tracked_date)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            request.seo_project_id,
            request.keyword,
            search_volume,
            current_position,
            date.today()
        ))
        connection.commit()
        
        return {
            "success": True,
            "keyword": request.keyword,
            "current_position": current_position,
            "previous_position": previous_position,
            "position_change": position_change,
            "search_volume": search_volume,
            "difficulty": difficulty,
            "cpc": keyword_data.get('cpc', 1.50),
            "domain_authority": keyword_data.get('domain_authority', 0),
            "tracked_date": date.today().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Keyword tracking failed: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/keywords/history/{project_id}")
async def get_keyword_history(
    project_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get keyword tracking history with position changes"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get latest position for each keyword
        query = """
            SELECT kt1.keyword_id, kt1.keyword, kt1.search_volume, 
                   kt1.current_position, kt1.tracked_date
            FROM keyword_tracking kt1
            INNER JOIN (
                SELECT keyword, MAX(tracked_date) as max_date
                FROM keyword_tracking
                WHERE seo_project_id = %s
                GROUP BY keyword
            ) kt2 ON kt1.keyword = kt2.keyword AND kt1.tracked_date = kt2.max_date
            WHERE kt1.seo_project_id = %s
            ORDER BY kt1.current_position ASC
        """
        
        cursor.execute(query, (project_id, project_id))
        keywords = cursor.fetchall()
        
        # Get position history for trends
        for kw in keywords:
            cursor.execute("""
                SELECT current_position, tracked_date
                FROM keyword_tracking
                WHERE seo_project_id = %s AND keyword = %s
                ORDER BY tracked_date DESC
                LIMIT 7
            """, (project_id, kw['keyword']))
            
            history = cursor.fetchall()
            kw['position_history'] = [
                {'position': h['current_position'], 'date': h['tracked_date'].isoformat()}
                for h in history
            ]
            
            # Calculate trend
            if len(history) >= 2:
                oldest_pos = history[-1]['current_position']
                newest_pos = history[0]['current_position']
                kw['trend'] = 'up' if newest_pos < oldest_pos else ('down' if newest_pos > oldest_pos else 'stable')
                kw['position_change'] = oldest_pos - newest_pos
            else:
                kw['trend'] = 'stable'
                kw['position_change'] = 0
            
            if kw['tracked_date']:
                kw['tracked_date'] = kw['tracked_date'].isoformat()
        
        return {"success": True, "keywords": keywords}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch keywords: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== BACKLINK STRATEGIST ==========

@router.post("/backlinks/suggest-targets")
async def suggest_backlink_targets(
    request: BacklinkTargetRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    AI-powered backlink target suggestions with DA scoring
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get project details
        cursor.execute(
            "SELECT website_url FROM seo_projects WHERE seo_project_id = %s AND client_id = %s",
            (request.seo_project_id, current_user['user_id'])
        )
        project = cursor.fetchone()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SEO project not found"
            )
        
        website_url = project['website_url']
        
        # Get current domain authority
        moz_data = get_moz_url_metrics(website_url)
        current_da = moz_data.get('domain_authority', 0) if moz_data.get('success') else 0
        
        # Use AI to suggest backlink targets
        if client:
            prompt = f"""As an SEO expert, suggest 10 high-quality backlink opportunities for a website in the "{request.niche}" niche.
            
Current website: {website_url}
Current Domain Authority: {current_da}
Minimum target DA: {request.min_da}

For each opportunity, provide:
1. target_type: Type of opportunity (guest post, resource page, broken link, directory, etc.)
2. description: Description of the opportunity
3. estimated_da: Estimated domain authority (must be >= {request.min_da})
4. outreach_strategy: Recommended outreach approach
5. difficulty: easy/medium/hard
6. relevance_score: 1-100 relevance to the niche

Return ONLY a JSON array of objects with these fields. No markdown."""

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert SEO link builder. Return only valid JSON array."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            targets = json.loads(response_text)
            
            # Enhance targets with scoring
            for i, target in enumerate(targets):
                target['id'] = i + 1
                target['priority'] = 'high' if target.get('estimated_da', 0) >= 50 else ('medium' if target.get('estimated_da', 0) >= 30 else 'low')
                target['da_badge_class'] = 'success' if target.get('estimated_da', 0) >= 70 else ('warning' if target.get('estimated_da', 0) >= 40 else 'danger')
        else:
            # Fallback targets
            targets = [
                {
                    'id': 1,
                    'target_type': 'Guest Post',
                    'description': f'Industry blog accepting guest contributions in {request.niche}',
                    'estimated_da': 45,
                    'outreach_strategy': 'Pitch unique article ideas with data',
                    'difficulty': 'medium',
                    'relevance_score': 85,
                    'priority': 'medium',
                    'da_badge_class': 'warning'
                },
                {
                    'id': 2,
                    'target_type': 'Resource Page',
                    'description': f'Curated resource list for {request.niche} professionals',
                    'estimated_da': 55,
                    'outreach_strategy': 'Suggest your resource as valuable addition',
                    'difficulty': 'easy',
                    'relevance_score': 90,
                    'priority': 'high',
                    'da_badge_class': 'warning'
                },
                {
                    'id': 3,
                    'target_type': 'Broken Link Building',
                    'description': f'Find broken links on {request.niche} authority sites',
                    'estimated_da': 60,
                    'outreach_strategy': 'Offer your content as replacement',
                    'difficulty': 'medium',
                    'relevance_score': 75,
                    'priority': 'high',
                    'da_badge_class': 'warning'
                }
            ]
        
        return {
            "success": True,
            "website_url": website_url,
            "current_da": current_da,
            "niche": request.niche,
            "min_da_filter": request.min_da,
            "targets": targets,
            "total_targets": len(targets)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate targets: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.post("/backlinks/outreach")
async def generate_backlink_outreach(
    request: BacklinkOutreachRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate AI-powered outreach email for backlink acquisition"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get project details
        cursor.execute(
            "SELECT website_url FROM seo_projects WHERE seo_project_id = %s AND client_id = %s",
            (request.seo_project_id, current_user['user_id'])
        )
        project = cursor.fetchone()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SEO project not found"
            )
        
        website_url = project['website_url']
        
        # Get target site DA
        target_moz = get_moz_url_metrics(request.target_url)
        target_da = target_moz.get('domain_authority', 0) if target_moz.get('success') else 0
        
        # Generate outreach email using AI
        if client:
            prompt = f"""Create a professional, personalized backlink outreach email.

My website: {website_url}
Target website: {request.target_url}
Target DA: {target_da}
Desired anchor text: {request.anchor_text}

Create a compelling outreach email that:
1. Has a catchy subject line
2. Is personalized and not spammy
3. Provides clear value proposition
4. Includes a specific request
5. Has a professional sign-off

Return ONLY a valid JSON object with these exact fields:
- subject: email subject line (plain text, no newlines)
- body: email body (use \\n for line breaks)
- follow_up: follow-up email text (use \\n for line breaks)

Ensure all text uses \\n for line breaks and has no unescaped control characters."""

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert outreach specialist. Return ONLY valid JSON with properly escaped strings. Use \\n for line breaks."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Remove any trailing code block markers
            if response_text.endswith('```'):
                response_text = response_text[:-3].strip()
            
            # Clean up any remaining control characters before parsing
            response_text = response_text.replace('\r\n', '\\n').replace('\r', '\\n').replace('\t', '    ')
            
            try:
                email_content = json.loads(response_text)
                
                # Ensure all required fields exist
                if not all(key in email_content for key in ['subject', 'body', 'follow_up']):
                    raise ValueError("Missing required fields in AI response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                # Fallback if AI response is malformed
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to parse AI response: {str(e)}"
                )
        else:
            email_content = {
                "subject": f"Collaboration Opportunity - {request.anchor_text}",
                "body": f"Hi,\n\nI came across your website ({request.target_url}) and was impressed by your content.\n\nI run {website_url} and believe our audiences would benefit from a collaboration.\n\nWould you be interested in linking to our resource about {request.anchor_text}?\n\nBest regards",
                "follow_up": "Hi,\n\nJust following up on my previous email about a potential collaboration.\n\nLet me know if you'd like to discuss further.\n\nBest"
            }
        
        # Save backlink to database with correct status value
        query = """
            INSERT INTO backlinks 
            (seo_project_id, source_url, target_url, anchor_text, status, outreach_email)
            VALUES (%s, %s, %s, %s, 'active', %s)
        """
        
        # Ensure JSON is properly serialized
        outreach_email_json = json.dumps(email_content, ensure_ascii=False)
        
        cursor.execute(query, (
            request.seo_project_id,
            request.target_url,
            website_url,
            request.anchor_text,
            outreach_email_json
        ))
        connection.commit()
        
        backlink_id = cursor.lastrowid
        
        return {
            "success": True,
            "backlink_id": backlink_id,
            "target_url": request.target_url,
            "target_da": target_da,
            "anchor_text": request.anchor_text,
            "outreach_email": email_content
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate outreach: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@router.get("/backlinks/list/{project_id}")
async def list_backlinks(
    project_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get all backlinks for a project"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT backlink_id, source_url, target_url, anchor_text, 
                   status, outreach_email, created_at
            FROM backlinks
            WHERE seo_project_id = %s
            ORDER BY created_at DESC
        """
        
        cursor.execute(query, (project_id,))
        backlinks = cursor.fetchall()
        
        for bl in backlinks:
            if bl['outreach_email']:
                bl['outreach_email'] = json.loads(bl['outreach_email'])
            if bl['created_at']:
                bl['created_at'] = bl['created_at'].isoformat()
        
        return {"success": True, "backlinks": backlinks}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch backlinks: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== CONTENT OPTIMIZATION ==========

@router.post("/optimize-content")
async def optimize_content(
    request: ContentOptimizationRequest,
    current_user: dict = Depends(get_current_user)
):
    """AI-powered content optimization scoring"""
    try:
        if not client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI service not available"
            )
        
        prompt = f"""Analyze this content for SEO optimization targeting the keyword "{request.target_keyword}".
Content type: {request.content_type}

Content:
{request.content[:3000]}

Provide a comprehensive SEO analysis with:
1. overall_score (0-100)
2. keyword_density (percentage)
3. word_count
4. readability_score (0-100)
5. title_optimization (0-100)
6. meta_description_suggestion
7. heading_structure (assessment)
8. internal_linking_suggestions (array)
9. keyword_variations (array of related keywords to include)
10. content_gaps (what's missing)
11. recommendations (array of actionable improvements)

Return ONLY valid JSON."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert SEO content analyst. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content.strip()
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        optimization = json.loads(response_text)
        
        return {
            "success": True,
            "target_keyword": request.target_keyword,
            "content_type": request.content_type,
            "optimization": optimization
        }
    
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse optimization results"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content optimization failed: {str(e)}"
        )


# ========== VOICE SEARCH OPTIMIZATION ==========

@router.post("/voice-search/optimize")
async def optimize_for_voice_search(
    request: VoiceSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Optimize content for voice search queries"""
    try:
        if not client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI service not available"
            )
        
        prompt = f"""Analyze this content for voice search optimization:

{request.content[:2000]}

Provide:
1. voice_search_score (0-100)
2. featured_snippet_potential (0-100)
3. question_keywords (array of question-based keywords to target)
4. conversational_phrases (array of natural language phrases)
5. local_seo_opportunities (if applicable)
6. schema_markup_suggestions (structured data recommendations)
7. optimization_tips (array of specific improvements)

Return ONLY valid JSON."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a voice search SEO expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        response_text = response.choices[0].message.content.strip()
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        optimization = json.loads(response_text)
        
        return {
            "success": True,
            "optimization": optimization
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice search optimization failed: {str(e)}"
        )


# ========== API TEST ENDPOINTS (PUBLIC - NO AUTH) ==========

@router.get("/test/moz")
async def test_moz_api():
    """Test Moz API connectivity - PUBLIC endpoint for testing"""
    try:
        # Check if credentials are configured
        if not settings.MOZ_ACCESS_ID or not settings.MOZ_SECRET_KEY:
            return {
                "success": False,
                "error": "Moz API credentials not configured",
                "config": {
                    "MOZ_ACCESS_ID": "Set" if settings.MOZ_ACCESS_ID else "Missing",
                    "MOZ_SECRET_KEY": "Set" if settings.MOZ_SECRET_KEY else "Missing"
                }
            }
        
        result = get_moz_url_metrics("moz.com")
        return {
            "success": result.get('success', False),
            "message": "Moz API working" if result.get('success') else result.get('error'),
            "data": result if result.get('success') else None,
            "debug": {
                "access_id_prefix": settings.MOZ_ACCESS_ID[:10] + "..." if settings.MOZ_ACCESS_ID else None,
                "secret_key_length": len(settings.MOZ_SECRET_KEY) if settings.MOZ_SECRET_KEY else 0
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/test/moz-debug")
async def test_moz_api_debug():
    """Debug Moz API - shows raw request/response"""
    try:
        access_id = settings.MOZ_ACCESS_ID
        secret_key = settings.MOZ_SECRET_KEY
        
        if not access_id or not secret_key:
            return {"success": False, "error": "Credentials missing"}
        
        # Build auth header
        credentials = f"{access_id}:{secret_key}"
        encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        auth_header = f"Basic {encoded}"
        
        endpoint = "https://lsapi.seomoz.com/v2/url_metrics"
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json"
        }
        payload = {"targets": ["moz.com"]}
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response_text": response.text[:1000] if response.text else None,
            "debug": {
                "access_id": access_id,
                "secret_key_first_5": secret_key[:5] + "..." if secret_key else None,
                "secret_key_length": len(secret_key) if secret_key else 0,
                "auth_header_preview": auth_header[:30] + "..."
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/test/pagespeed")
async def test_pagespeed_api():
    """Test PageSpeed Insights API connectivity - PUBLIC endpoint for testing"""
    try:
        # Check if API key is configured
        api_key = settings.PAGESPEED_API_KEY or getattr(settings, 'GOOGLE_API_KEY', None)
        if not api_key:
            return {
                "success": False,
                "error": "PageSpeed API key not configured",
                "config": {
                    "PAGESPEED_API_KEY": "Set" if getattr(settings, 'PAGESPEED_API_KEY', None) else "Missing",
                    "GOOGLE_API_KEY": "Set" if getattr(settings, 'GOOGLE_API_KEY', None) else "Missing"
                }
            }
        
        result = get_pagespeed_insights("google.com", "mobile")
        return {
            "success": result.get('success', False),
            "message": "PageSpeed API working" if result.get('success') else result.get('error'),
            "data": result if result.get('success') else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/test/openai")
async def test_openai_api():
    """Test OpenAI API connectivity - PUBLIC endpoint for testing"""
    try:
        if not client:
            return {
                "success": False,
                "error": "OpenAI client not initialized",
                "config": {
                    "OPENAI_API_KEY": "Set" if settings.OPENAI_API_KEY else "Missing"
                }
            }
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Say 'API working' in 2 words"}],
            max_tokens=10
        )
        
        return {
            "success": True,
            "message": "OpenAI API working",
            "response": response.choices[0].message.content
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/test/all")
async def test_all_apis():
    """Test all SEO-related APIs at once - PUBLIC endpoint"""
    results = {}
    
    # Test Moz (NO AI fallback - real data only)
    try:
        moz_result = get_moz_url_metrics("example.com")
        results["moz"] = {
            "success": moz_result.get('success', False),
            "domain_authority": moz_result.get('domain_authority') if moz_result.get('success') else None,
            "error": moz_result.get('error') if not moz_result.get('success') else None
        }
    except Exception as e:
        results["moz"] = {"success": False, "error": str(e)}
    
    # Test PageSpeed
    try:
        api_key = settings.PAGESPEED_API_KEY or getattr(settings, 'GOOGLE_API_KEY', None)
        if api_key:
            ps_result = get_pagespeed_insights("google.com", "mobile")
            results["pagespeed"] = {
                "success": ps_result.get('success', False),
                "performance_score": ps_result.get('performance_score') if ps_result.get('success') else None,
                "error": ps_result.get('error') if not ps_result.get('success') else None
            }
        else:
            results["pagespeed"] = {"success": False, "error": "API key not configured"}
    except Exception as e:
        results["pagespeed"] = {"success": False, "error": str(e)}
    
    # Test OpenAI
    try:
        if client:
            results["openai"] = {"success": True, "message": "Client initialized"}
        else:
            results["openai"] = {"success": False, "error": "Client not initialized"}
    except Exception as e:
        results["openai"] = {"success": False, "error": str(e)}
    
    # Overall status
    all_success = all(r.get('success', False) for r in results.values())
    
    return {
        "success": all_success,
        "message": "All APIs working" if all_success else "Some APIs have issues",
        "results": results
    }



# Add this endpoint to app/api/v1/endpoints/seo.py
# Insert after the existing endpoints

class CompetitorHeatmapRequest(BaseModel):
    seo_project_id: int
    competitor_urls: List[str]  # Max 5 competitors
    
    @validator('competitor_urls')
    def validate_competitors(cls, v):
        if len(v) > 5:
            raise ValueError("Maximum 5 competitors allowed")
        # Clean URLs
        cleaned = []
        for url in v:
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                url = f"https://{url}"
            cleaned.append(url)
        return cleaned


@router.post("/competitor-heatmap")
async def get_competitor_heatmap(
    request: CompetitorHeatmapRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate competitor comparison heatmap using real Moz API data
    
    Compares metrics across:
    - Domain Authority
    - Page Authority
    - Spam Score
    - Total Backlinks
    - Referring Domains
    - Top Pages
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get project details
        cursor.execute(
            "SELECT website_url FROM seo_projects WHERE seo_project_id = %s AND client_id = %s",
            (request.seo_project_id, current_user['user_id'])
        )
        project = cursor.fetchone()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SEO project not found"
            )
        
        client_url = project['website_url']
        
        # Array to store comparison data
        comparison_data = []
        
        # 1. Get client's metrics (YOUR SITE)
        client_moz = get_moz_url_metrics(client_url)
        client_backlinks = get_moz_backlinks(client_url, limit=10)
        
        if not client_moz.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch client metrics from Moz API"
            )
        
        client_data = {
            "name": "Your Site",
            "url": client_url,
            "domain_authority": client_moz.get('domain_authority', 0),
            "page_authority": client_moz.get('page_authority', 0),
            "spam_score": client_moz.get('spam_score', 0),
            "total_backlinks": client_backlinks.get('total_backlinks', 0),
            "referring_domains": client_backlinks.get('unique_domains', 0),
            "is_client": True
        }
        comparison_data.append(client_data)
        
        # 2. Get competitor metrics
        for idx, comp_url in enumerate(request.competitor_urls, 1):
            comp_moz = get_moz_url_metrics(comp_url)
            comp_backlinks = get_moz_backlinks(comp_url, limit=10)
            
            if comp_moz.get('success'):
                competitor_data = {
                    "name": f"Competitor {idx}",
                    "url": comp_url,
                    "domain_authority": comp_moz.get('domain_authority', 0),
                    "page_authority": comp_moz.get('page_authority', 0),
                    "spam_score": comp_moz.get('spam_score', 0),
                    "total_backlinks": comp_backlinks.get('total_backlinks', 0),
                    "referring_domains": comp_backlinks.get('unique_domains', 0),
                    "is_client": False
                }
                comparison_data.append(competitor_data)
            else:
                # If competitor fails, add placeholder with error
                comparison_data.append({
                    "name": f"Competitor {idx}",
                    "url": comp_url,
                    "error": "Failed to fetch data",
                    "is_client": False
                })
        
        # 3. Calculate gaps and opportunities
        metrics_to_compare = [
            "domain_authority",
            "page_authority", 
            "spam_score",
            "total_backlinks",
            "referring_domains"
        ]
        
        gaps = {}
        max_values = {}
        
        # Find max values for each metric
        for metric in metrics_to_compare:
            valid_values = [
                item.get(metric, 0) 
                for item in comparison_data 
                if metric in item and not item.get('error')
            ]
            max_values[metric] = max(valid_values) if valid_values else 0
        
        # Calculate gaps for client vs best competitor
        for metric in metrics_to_compare:
            client_value = client_data.get(metric, 0)
            max_value = max_values[metric]
            
            if metric == 'spam_score':
                # For spam score, lower is better
                gap = client_value - max_value if max_value > 0 else 0
                opportunity = "Lower spam score" if gap > 0 else "Maintain low spam"
            else:
                # For other metrics, higher is better
                gap = max_value - client_value
                opportunity = f"Increase by {gap}" if gap > 0 else "Leading"
            
            gaps[metric] = {
                "client_value": client_value,
                "max_competitor_value": max_value,
                "gap": gap,
                "opportunity": opportunity,
                "is_winning": (gap <= 0 and metric != 'spam_score') or (gap >= 0 and metric == 'spam_score')
            }
        
        return {
            "success": True,
            "client_url": client_url,
            "comparison_data": comparison_data,
            "gaps_analysis": gaps,
            "max_values": max_values,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate competitor heatmap: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



# Add these endpoints to app/api/v1/endpoints/seo.py

# ========== SEO MONTHLY REPORTS ==========

@router.post("/reports/sync/{project_id}")
async def sync_seo_performance_data(
    project_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Sync SEO performance data from Google Search Console
    Fetches last 30 days of data: Traffic, Clicks, Impressions
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get project details
        cursor.execute(
            "SELECT website_url FROM seo_projects WHERE seo_project_id = %s AND client_id = %s",
            (project_id, current_user['user_id'])
        )
        project = cursor.fetchone()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SEO project not found"
            )
        
        website_url = project['website_url']

        if not website_url.startswith(('sc-domain:', 'http://', 'https://')):
            website_url = f"https://{website_url}"


        
        # Get Google Search Console service
        search_console = get_search_console_service()
        
        if not search_console:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Search Console not configured. Please add credentials in settings."
            )
        
        # Fetch last 30 days of data
        from datetime import datetime, timedelta
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Build Search Console API request
        request_body = {
            'startDate': start_date.isoformat(),
            'endDate': end_date.isoformat(),
            'dimensions': ['date'],
            'rowLimit': 30
        }
        
        # Execute Search Console query
        response = search_console.searchanalytics().query(
            siteUrl=website_url,
            body=request_body
        ).execute()
        
        rows = response.get('rows', [])
        
        if not rows:
            return {
                "success": True,
                "message": "No data available from Google Search Console",
                "records_synced": 0
            }
        
        # Process and store data
        records_synced = 0
        for row in rows:
            metric_date = row['keys'][0]  # Date string YYYY-MM-DD
            impressions = int(row.get('impressions', 0))
            clicks = int(row.get('clicks', 0))
            ctr = float(row.get('ctr', 0)) * 100  # Convert to percentage
            position = float(row.get('position', 0))
            
            # Insert or update record
            cursor.execute("""
                INSERT INTO seo_performance_data 
                (seo_project_id, metric_date, impressions, clicks, ctr, average_position, traffic_source)
                VALUES (%s, %s, %s, %s, %s, %s, 'organic')
                ON DUPLICATE KEY UPDATE
                    impressions = VALUES(impressions),
                    clicks = VALUES(clicks),
                    ctr = VALUES(ctr),
                    average_position = VALUES(average_position),
                    updated_at = CURRENT_TIMESTAMP
            """, (project_id, metric_date, impressions, clicks, ctr, position))
            
            records_synced += 1
        
        connection.commit()
        
        return {
            "success": True,
            "message": f"Successfully synced {records_synced} days of performance data",
            "records_synced": records_synced,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        
        import traceback
        error_details = traceback.format_exc()
        print(f"Error syncing SEO performance data: {error_details}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync performance data: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/reports/monthly/{project_id}")
async def get_monthly_report(
    project_id: int,
    months: int = 3,
    current_user: dict = Depends(get_current_user)
):
    """
    Get monthly SEO performance report with graphs data
    Returns Traffic, Clicks, Impressions for specified number of months
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Verify project ownership
        cursor.execute(
            "SELECT website_url FROM seo_projects WHERE seo_project_id = %s AND client_id = %s",
            (project_id, current_user['user_id'])
        )
        project = cursor.fetchone()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SEO project not found"
            )
        
        # Calculate date range
        from datetime import datetime, timedelta
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=months * 30)
        
        # Fetch performance data
        cursor.execute("""
            SELECT 
                metric_date,
                impressions,
                clicks,
                ctr,
                average_position
            FROM seo_performance_data
            WHERE seo_project_id = %s
                AND metric_date BETWEEN %s AND %s
            ORDER BY metric_date ASC
        """, (project_id, start_date, end_date))
        
        daily_data = cursor.fetchall()
        
        # Calculate monthly aggregates
        monthly_summary = {}
        for row in daily_data:
            month_key = row['metric_date'].strftime('%Y-%m')
            
            if month_key not in monthly_summary:
                monthly_summary[month_key] = {
                    'total_impressions': 0,
                    'total_clicks': 0,
                    'avg_ctr': [],
                    'avg_position': [],
                    'days_count': 0
                }
            
            monthly_summary[month_key]['total_impressions'] += row['impressions']
            monthly_summary[month_key]['total_clicks'] += row['clicks']
            monthly_summary[month_key]['avg_ctr'].append(float(row['ctr']))
            monthly_summary[month_key]['avg_position'].append(float(row['average_position']))
            monthly_summary[month_key]['days_count'] += 1
        
        # Format monthly data for graphs
        monthly_labels = []
        monthly_impressions = []
        monthly_clicks = []
        monthly_ctr = []
        monthly_traffic = []  # Clicks = Traffic
        
        for month_key in sorted(monthly_summary.keys()):
            data = monthly_summary[month_key]
            month_name = datetime.strptime(month_key, '%Y-%m').strftime('%B %Y')
            
            monthly_labels.append(month_name)
            monthly_impressions.append(data['total_impressions'])
            monthly_clicks.append(data['total_clicks'])
            monthly_traffic.append(data['total_clicks'])  # Traffic = Clicks in SEO context
            
            # Calculate average CTR for the month
            avg_ctr = sum(data['avg_ctr']) / len(data['avg_ctr']) if data['avg_ctr'] else 0
            monthly_ctr.append(round(avg_ctr, 2))
        
        # Calculate overall summary
        total_impressions = sum([row['impressions'] for row in daily_data])
        total_clicks = sum([row['clicks'] for row in daily_data])
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        avg_position = sum([float(row['average_position']) for row in daily_data]) / len(daily_data) if daily_data else 0
        
        # Format daily data for detailed view
        daily_formatted = []
        for row in daily_data:
            daily_formatted.append({
                'date': row['metric_date'].isoformat(),
                'impressions': row['impressions'],
                'clicks': row['clicks'],
                'ctr': float(row['ctr']),
                'position': float(row['average_position'])
            })
        
        return {
            "success": True,
            "project_id": project_id,
            "website_url": project['website_url'],
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "months": months
            },
            "summary": {
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_traffic": total_clicks,
                "average_ctr": round(avg_ctr, 2),
                "average_position": round(avg_position, 2)
            },
            "monthly_data": {
                "labels": monthly_labels,
                "impressions": monthly_impressions,
                "clicks": monthly_clicks,
                "traffic": monthly_traffic,
                "ctr": monthly_ctr
            },
            "daily_data": daily_formatted
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error fetching monthly report: {error_details}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch monthly report: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/reports/export/{project_id}")
async def export_monthly_report(
    project_id: int,
    format: str = 'json',
    months: int = 3,
    current_user: dict = Depends(get_current_user)
):
    """
    Export monthly SEO report
    Formats: json, csv (future)
    """
    try:
        # Reuse the monthly report data
        report_data = await get_monthly_report(project_id, months, current_user)
        
        if format == 'json':
            return report_data
        elif format == 'csv':
            # Future: Convert to CSV format
            return {
                "success": True,
                "message": "CSV export coming soon",
                "data": report_data
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Supported: json, csv"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

        