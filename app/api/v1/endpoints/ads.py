"""
Ad Strategy & Suggestion Engine API - Module 9 (COMPLETE VERSION)
File: app/api/v1/endpoints/ad_strategy.py

COMPLETE implementation with ALL requirements from scope document:
1. Audience Intelligence & Segmentation (ENHANCED with lookalike, device, time-based)
2. Platform & Channel Selector (ENHANCED with format selection, TikTok, YouTube)
3. Ad Copy & Creative Generator (ENHANCED with image prompts, video scripts)
4. Placement & Bidding Optimizer (NEW - with historical data, auto/manual recommendations)
5. Performance Forecasting Model (ENHANCED with break-even calculator, simulations)
6. Execution & Publishing Engine (ENHANCED with A/B testing, pause/resume)
7. Live Dashboard & Report (COMPLETE)
"""

from fastapi import APIRouter, HTTPException, status, Depends, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import pymysql
import json
from openai import OpenAI

# ADD THESE IMPORTS AT THE TOP OF THE FILE (if not already present)
import re
import traceback


from app.core.config import settings
from app.core.security import require_admin_or_employee, get_current_user, get_db_connection
from app.services.ads_service import AdService

router = APIRouter()

# Initialize services
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
ad_service = AdService()


# ========== PYDANTIC MODELS ==========

class AudienceSegmentCreate(BaseModel):
    """Create audience segment with enhanced options"""
    client_id: int
    platform: str = Field(..., description="meta, google, linkedin, tiktok")
    segment_name: str
    demographics: Dict[str, Any] = Field(default_factory=dict)
    interests: List[str] = Field(default_factory=list)
    behaviors: List[str] = Field(default_factory=list)
    device_targeting: Optional[Dict[str, Any]] = None  # NEW: mobile, desktop, tablet
    time_based_targeting: Optional[Dict[str, Any]] = None  # NEW: time of day, day of week
    lookalike_source: Optional[str] = None  # NEW: lookalike audience
    custom_criteria: Optional[Dict[str, Any]] = None


class PlatformRecommendationRequest(BaseModel):
    """Get AI platform recommendations with format selection"""
    client_id: int
    campaign_objective: str
    budget: float
    target_audience: Dict[str, Any]
    industry: Optional[str] = None
    include_formats: bool = True  # NEW: Include format recommendations


class AdCopyGenerateRequest(BaseModel):
    """Generate ad copy with creative suggestions"""
    campaign_objective: str
    product_service: str
    target_audience: str
    platform: str
    tone: str = "professional"
    key_benefits: List[str] = Field(default_factory=list)
    cta_type: str = "Learn More"
    include_image_prompts: bool = True  # NEW
    include_video_scripts: bool = False  # NEW
    ad_format: Optional[str] = None  # NEW: stories, feed, reels, shorts, youtube


class PlacementOptimizationRequest(BaseModel):
    """Get placement and bidding recommendations"""
    campaign_id: int
    platform: str
    historical_data_days: int = 30  # NEW: Use historical data
    optimization_goal: str = "conversions"  # NEW: conversions, clicks, impressions


class CampaignCreate(BaseModel):
    """Create ad campaign with enhanced options"""
    client_id: int
    campaign_name: str
    platform: str
    objective: str
    budget: float
    start_date: date
    end_date: Optional[date] = None
    target_audience: Dict[str, Any]
    placement_settings: Optional[Dict[str, Any]] = None
    bidding_strategy: Optional[str] = None
    schedule_settings: Optional[Dict[str, Any]] = None  # NEW: scheduling
    ab_test_config: Optional[Dict[str, Any]] = None  # NEW: A/B testing


class AdCreate(BaseModel):
    """Create ad within campaign"""
    campaign_id: int
    ad_name: str
    ad_format: str
    primary_text: str
    headline: str
    description: Optional[str] = None
    media_urls: List[str] = Field(default_factory=list)
    is_ab_test_variant: bool = False  # NEW
    ab_test_group: Optional[str] = None  # NEW: A or B


class ForecastRequest(BaseModel):
    """Forecast campaign performance with simulations"""
    platform: str
    objective: str
    budget: float
    duration_days: int
    target_audience_size: int
    include_breakeven: bool = True  # NEW
    average_order_value: Optional[float] = None  # NEW: for break-even calc
    run_simulations: bool = False  # NEW: budget scenarios


class CampaignControlRequest(BaseModel):
    """Control campaign status"""
    action: str = Field(..., description="pause, resume, schedule")
    scheduled_at: Optional[datetime] = None  # NEW


# ========== 1. ENHANCED AUDIENCE INTELLIGENCE ==========

@router.post("/audience/create", summary="Create enhanced audience segment")
async def create_audience_segment(
    segment: AudienceSegmentCreate,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Create custom audience segment with ALL targeting options:
    - Custom & lookalike audiences
    - Interest & behavior targeting
    - Device profiling
    - Time-based targeting
    - In-market & affinity audiences (Google)
    """
    connection = None
    cursor = None
    
    try:
        # Get ENHANCED AI suggestions
        ai_suggestions = await ad_service.get_enhanced_audience_suggestions(
            platform=segment.platform,
            demographics=segment.demographics,
            interests=segment.interests,
            behaviors=segment.behaviors,
            device_targeting=segment.device_targeting,
            time_targeting=segment.time_based_targeting,
            lookalike_source=segment.lookalike_source
        )
        
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Build ENHANCED segment criteria
        segment_criteria = {
            "demographics": segment.demographics,
            "interests": segment.interests,
            "behaviors": segment.behaviors,
            "device_targeting": segment.device_targeting or {},
            "time_based_targeting": segment.time_based_targeting or {},
            "lookalike": segment.lookalike_source,
            "custom": segment.custom_criteria or {},
            "ai_suggestions": ai_suggestions,
            # NEW: Platform-specific audiences
            "in_market_audiences": ai_suggestions.get('in_market_audiences', []),
            "affinity_audiences": ai_suggestions.get('affinity_audiences', [])
        }
        
        cursor.execute("""
            INSERT INTO audience_segments (
                client_id, segment_name, platform, segment_criteria,
                estimated_size, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            segment.client_id,
            segment.segment_name,
            segment.platform,
            json.dumps(segment_criteria),
            ai_suggestions.get('estimated_reach', 0),
            current_user['user_id']
        ))
        
        connection.commit()
        segment_id = cursor.lastrowid
        
        return {
            "success": True,
            "segment_id": segment_id,
            "segment_criteria": segment_criteria,
            "ai_suggestions": ai_suggestions,
            "lookalike_audiences": ai_suggestions.get('lookalike_suggestions', []),
            "device_breakdown": ai_suggestions.get('device_breakdown', {}),
            "best_times": ai_suggestions.get('best_times', [])
        }
        
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create segment: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/audience/list/{client_id}", summary="List audience segments")
async def list_audience_segments(
    client_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get all audience segments for a client"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT s.*, u.full_name as creator_name
            FROM audience_segments s
            JOIN users u ON s.created_by = u.user_id
            WHERE s.client_id = %s
            ORDER BY s.created_at DESC
        """, (client_id,))
        
        segments = cursor.fetchall()
        
        for seg in segments:
            if seg['segment_criteria']:
                seg['segment_criteria'] = json.loads(seg['segment_criteria'])
        
        return {"success": True, "segments": segments}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch segments: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== 2. ENHANCED PLATFORM SELECTOR ==========

@router.post("/platform/recommend", summary="Get enhanced platform recommendations")
async def get_platform_recommendations(
    request: PlatformRecommendationRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    AI-powered platform selection with:
    - Meta, Google, YouTube, Display, TikTok, LinkedIn
    - Budget split suggestions
    - Format selection (Stories vs Feed, Search vs Display, Reels vs Shorts)
    """
    try:
        recommendations = await ad_service.recommend_platforms_enhanced(
            objective=request.campaign_objective,
            budget=request.budget,
            target_audience=request.target_audience,
            industry=request.industry,
            include_formats=request.include_formats
        )
        
        return {
            "success": True,
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


# ========== 3. ENHANCED AD COPY & CREATIVE GENERATOR ==========

@router.post("/adcopy/generate", summary="Generate enhanced ad copy with creatives")
async def generate_ad_copy(
    request: AdCopyGenerateRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Generate platform-optimized ad copy with:
    - Primary text, headlines, descriptions
    - Image prompts for Canva/DALL-E integration
    - Video script templates for Reels/Shorts/YouTube
    """
    try:
        ad_copy = await ad_service.generate_ad_copy_enhanced(
            objective=request.campaign_objective,
            product=request.product_service,
            audience=request.target_audience,
            platform=request.platform,
            tone=request.tone,
            benefits=request.key_benefits,
            cta=request.cta_type,
            include_image_prompts=request.include_image_prompts,
            include_video_scripts=request.include_video_scripts,
            ad_format=request.ad_format
        )
        
        return {
            "success": True,
            "ad_copy": ad_copy
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate ad copy: {str(e)}"
        )


# ========== 4. NEW: PLACEMENT & BIDDING OPTIMIZER ==========

@router.post("/placement/optimize", summary="Get placement and bidding recommendations")
async def optimize_placement(
    request: PlacementOptimizationRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Placement & bidding optimization using:
    - Historical performance data
    - Platform-specific insights
    - Auto vs manual placement recommendations
    - Smart bidding strategies (Maximize Conversions, Target ROAS, etc.)
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get historical performance data
        end_date = date.today()
        start_date = end_date - timedelta(days=request.historical_data_days)
        
        cursor.execute("""
            SELECT 
                ap.*, a.ad_format, a.placement_settings
            FROM ad_performance ap
            JOIN ads a ON ap.ad_id = a.ad_id
            JOIN ad_campaigns c ON a.campaign_id = c.campaign_id
            WHERE c.campaign_id = %s 
            AND c.platform = %s
            AND ap.metric_date BETWEEN %s AND %s
        """, (request.campaign_id, request.platform, start_date, end_date))
        
        historical_data = cursor.fetchall()
        
        # Get AI-powered optimization recommendations
        optimization = await ad_service.optimize_placement_and_bidding(
            platform=request.platform,
            historical_data=historical_data,
            optimization_goal=request.optimization_goal
        )
        
        return {
            "success": True,
            "optimization": optimization
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize placement: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== 5. ENHANCED PERFORMANCE FORECASTING ==========

@router.post("/forecast", summary="Enhanced performance forecast with simulations")
async def forecast_performance(
    request: ForecastRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Generate AI-powered performance forecast with:
    - CTR, CPC, CPM, ROAS, Impressions predictions
    - Budget vs result simulation
    - Break-even ad spend calculator
    - Multiple budget scenarios
    """
    try:
        forecast = await ad_service.forecast_campaign_performance_enhanced(
            platform=request.platform,
            objective=request.objective,
            budget=request.budget,
            duration_days=request.duration_days,
            audience_size=request.target_audience_size,
            include_breakeven=request.include_breakeven,
            aov=request.average_order_value,
            run_simulations=request.run_simulations
        )
        
        return {
            "success": True,
            "forecast": forecast
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate forecast: {str(e)}"
        )


# ========== 6. CAMPAIGNS WITH A/B TESTING ==========

@router.post("/campaigns/create", summary="Create campaign with A/B testing")
async def create_campaign(
    campaign: CampaignCreate,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Create new ad campaign with A/B testing and scheduling options"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            INSERT INTO ad_campaigns (
                client_id, created_by, campaign_name, platform, objective,
                budget, start_date, end_date, target_audience,
                placement_settings, bidding_strategy, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            campaign.client_id,
            current_user['user_id'],
            campaign.campaign_name,
            campaign.platform,
            campaign.objective,
            campaign.budget,
            campaign.start_date,
            campaign.end_date,
            json.dumps(campaign.target_audience),
            json.dumps(campaign.placement_settings or {}),
            campaign.bidding_strategy,
            'draft'
        ))
        
        connection.commit()
        campaign_id = cursor.lastrowid
        
        # If A/B testing configured, create suggestion record
        if campaign.ab_test_config:
            cursor.execute("""
                INSERT INTO ai_ad_suggestions (
                    client_id, campaign_id, audience_segments,
                    platform_recommendations, ad_copy_suggestions,
                    budget_recommendations, forecasted_metrics, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                campaign.client_id,
                campaign_id,
                json.dumps({}),
                json.dumps({}),
                json.dumps({"ab_test": campaign.ab_test_config}),
                json.dumps({}),
                json.dumps({}),
                'pending'
            ))
            connection.commit()
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "message": "Campaign created successfully",
            "ab_testing_enabled": bool(campaign.ab_test_config)
        }
        
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/campaigns/list/{client_id}", summary="List campaigns")
async def list_campaigns(
    client_id: int,
    platform: Optional[str] = None,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get all campaigns for a client"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT c.*, u.full_name as creator_name,
                   COUNT(DISTINCT a.ad_id) as total_ads
            FROM ad_campaigns c
            JOIN users u ON c.created_by = u.user_id
            LEFT JOIN ads a ON c.campaign_id = a.campaign_id
            WHERE c.client_id = %s
        """
        params = [client_id]
        
        if platform:
            query += " AND c.platform = %s"
            params.append(platform)
        
        query += " GROUP BY c.campaign_id ORDER BY c.created_at DESC"
        
        cursor.execute(query, params)
        campaigns = cursor.fetchall()
        
        for camp in campaigns:
            if camp['target_audience']:
                camp['target_audience'] = json.loads(camp['target_audience'])
            if camp['placement_settings']:
                camp['placement_settings'] = json.loads(camp['placement_settings'])
        
        return {"success": True, "campaigns": campaigns}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch campaigns: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== 7. ENHANCED CAMPAIGN PUBLISHING & CONTROL ==========

@router.post("/campaigns/{campaign_id}/publish", summary="Publish campaign with A/B testing")
async def publish_campaign(
    campaign_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Publish campaign to ad platform with:
    - Draft to live pushing
    - A/B split test creation
    - Automatic scheduling
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM ad_campaigns WHERE campaign_id = %s", (campaign_id,))
        campaign = cursor.fetchone()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Check for A/B test configuration
        cursor.execute("""
            SELECT ad_copy_suggestions FROM ai_ad_suggestions 
            WHERE campaign_id = %s ORDER BY created_at DESC LIMIT 1
        """, (campaign_id,))
        
        ab_config = None
        ab_result = cursor.fetchone()
        if ab_result and ab_result['ad_copy_suggestions']:
            suggestions = json.loads(ab_result['ad_copy_suggestions'])
            ab_config = suggestions.get('ab_test')
        
        # Publish campaign
        result = await ad_service.publish_campaign_enhanced(
            campaign=campaign,
            ab_test_config=ab_config
        )
        
        # Update campaign status
        cursor.execute("""
            UPDATE ad_campaigns
            SET status = 'active', external_campaign_id = %s
            WHERE campaign_id = %s
        """, (result.get('external_id'), campaign_id))
        
        connection.commit()
        
        return {
            "success": True,
            "external_campaign_id": result.get('external_id'),
            "ab_test_created": result.get('ab_test_created', False),
            "message": "Campaign published successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish campaign: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.post("/campaigns/{campaign_id}/control", summary="Control campaign (pause/resume/schedule)")
async def control_campaign(
    campaign_id: int,
    control: CampaignControlRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Campaign control actions:
    - Pause campaign
    - Resume campaign
    - Schedule campaign for future date
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM ad_campaigns WHERE campaign_id = %s", (campaign_id,))
        campaign = cursor.fetchone()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Execute control action
        result = await ad_service.control_campaign(
            campaign=campaign,
            action=control.action,
            scheduled_at=control.scheduled_at
        )
        
        # Update campaign status
        new_status = {
            'pause': 'paused',
            'resume': 'active',
            'schedule': 'draft'
        }.get(control.action, campaign['status'])
        
        cursor.execute("""
            UPDATE ad_campaigns SET status = %s WHERE campaign_id = %s
        """, (new_status, campaign_id))
        
        connection.commit()
        
        return {
            "success": True,
            "action": control.action,
            "new_status": new_status,
            "message": f"Campaign {control.action}d successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to control campaign: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== ADS MANAGEMENT ==========

@router.post("/ads/create", summary="Create ad with A/B test support")
async def create_ad(
    ad: AdCreate,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Create ad within a campaign (supports A/B testing)"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            INSERT INTO ads (
                campaign_id, ad_name, ad_format, primary_text,
                headline, description, media_urls, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ad.campaign_id,
            ad.ad_name,
            ad.ad_format,
            ad.primary_text,
            ad.headline,
            ad.description,
            json.dumps(ad.media_urls),
            'active'
        ))
        
        connection.commit()
        ad_id = cursor.lastrowid
        
        return {
            "success": True,
            "ad_id": ad_id,
            "message": "Ad created successfully",
            "ab_test_group": ad.ab_test_group if ad.is_ab_test_variant else None
        }
        
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ad: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/campaigns/{campaign_id}/ads", summary="List campaign ads")
async def list_campaign_ads(
    campaign_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get all ads for a campaign"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT a.*,
                   COALESCE(SUM(ap.impressions), 0) as total_impressions,
                   COALESCE(SUM(ap.clicks), 0) as total_clicks,
                   COALESCE(AVG(ap.ctr), 0) as avg_ctr,
                   COALESCE(AVG(ap.cpc), 0) as avg_cpc
            FROM ads a
            LEFT JOIN ad_performance ap ON a.ad_id = ap.ad_id
            WHERE a.campaign_id = %s
            GROUP BY a.ad_id
            ORDER BY a.created_at DESC
        """, (campaign_id,))
        
        ads = cursor.fetchall()
        
        for ad in ads:
            if ad['media_urls']:
                ad['media_urls'] = json.loads(ad['media_urls'])
        
        return {"success": True, "ads": ads}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch ads: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ========== PERFORMANCE TRACKING ==========

@router.get("/performance/{campaign_id}", summary="Get campaign performance")
async def get_campaign_performance(
    campaign_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get campaign performance metrics"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                ap.metric_date,
                SUM(ap.impressions) as impressions,
                SUM(ap.clicks) as clicks,
                AVG(ap.ctr) as ctr,
                AVG(ap.cpc) as cpc,
                SUM(ap.spend) as spend,
                SUM(ap.conversions) as conversions,
                AVG(ap.roas) as roas
            FROM ads a
            JOIN ad_performance ap ON a.ad_id = ap.ad_id
            WHERE a.campaign_id = %s
        """
        params = [campaign_id]
        
        if start_date:
            query += " AND ap.metric_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND ap.metric_date <= %s"
            params.append(end_date)
        
        query += " GROUP BY ap.metric_date ORDER BY ap.metric_date DESC"
        
        cursor.execute(query, params)
        metrics = cursor.fetchall()
        
        # Calculate totals
        cursor.execute("""
            SELECT 
                SUM(ap.impressions) as total_impressions,
                SUM(ap.clicks) as total_clicks,
                AVG(ap.ctr) as avg_ctr,
                AVG(ap.cpc) as avg_cpc,
                SUM(ap.spend) as total_spend,
                SUM(ap.conversions) as total_conversions,
                AVG(ap.roas) as avg_roas
            FROM ads a
            JOIN ad_performance ap ON a.ad_id = ap.ad_id
            WHERE a.campaign_id = %s
        """ + (" AND ap.metric_date >= %s" if start_date else "") + 
              (" AND ap.metric_date <= %s" if end_date else ""),
        params)
        
        totals = cursor.fetchone()
        
        return {
            "success": True,
            "daily_metrics": metrics,
            "totals": totals
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch performance: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/dashboard/{client_id}", summary="Get ads dashboard data")
async def get_ads_dashboard(
    client_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get comprehensive dashboard data"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Campaign stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_campaigns,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_campaigns,
                COUNT(CASE WHEN status = 'paused' THEN 1 END) as paused_campaigns,
                SUM(budget) as total_budget
            FROM ad_campaigns
            WHERE client_id = %s
        """, (client_id,))
        campaign_stats = cursor.fetchone()
        
        # Performance by platform
        cursor.execute("""
            SELECT 
                c.platform,
                COUNT(DISTINCT c.campaign_id) as campaigns,
                COUNT(DISTINCT a.ad_id) as ads,
                COALESCE(SUM(ap.impressions), 0) as impressions,
                COALESCE(SUM(ap.clicks), 0) as clicks,
                COALESCE(SUM(ap.spend), 0) as spend,
                COALESCE(SUM(ap.conversions), 0) as conversions
            FROM ad_campaigns c
            LEFT JOIN ads a ON c.campaign_id = a.campaign_id
            LEFT JOIN ad_performance ap ON a.ad_id = ap.ad_id
            WHERE c.client_id = %s
            GROUP BY c.platform
        """, (client_id,))
        platform_performance = cursor.fetchall()
        
        # Recent campaigns
        cursor.execute("""
            SELECT c.*, u.full_name as creator_name
            FROM ad_campaigns c
            JOIN users u ON c.created_by = u.user_id
            WHERE c.client_id = %s
            ORDER BY c.created_at DESC
            LIMIT 5
        """, (client_id,))
        recent_campaigns = cursor.fetchall()
        
        return {
            "success": True,
            "campaign_stats": campaign_stats,
            "platform_performance": platform_performance,
            "recent_campaigns": recent_campaigns
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard data: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@router.get("/campaigns/list-all", summary="List all campaigns across all clients")
async def list_all_campaigns(
    platform: Optional[str] = None,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get all campaigns across all clients (for admin/employee view)"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT c.*, 
                   u.full_name as creator_name,
                   client.full_name as client_name,
                   COUNT(DISTINCT a.ad_id) as total_ads
            FROM ad_campaigns c
            JOIN users u ON c.created_by = u.user_id
            JOIN users client ON c.client_id = client.user_id
            LEFT JOIN ads a ON c.campaign_id = a.campaign_id
            WHERE 1=1
        """
        params = []
        
        if platform:
            query += " AND c.platform = %s"
            params.append(platform)
        
        query += " GROUP BY c.campaign_id ORDER BY c.created_at DESC"
        
        cursor.execute(query, params)
        campaigns = cursor.fetchall()
        
        for camp in campaigns:
            if camp['target_audience']:
                camp['target_audience'] = json.loads(camp['target_audience'])
            if camp['placement_settings']:
                camp['placement_settings'] = json.loads(camp['placement_settings'])
        
        return {"success": True, "campaigns": campaigns}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch campaigns: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/audience/list-all", summary="List all audience segments across all clients")
async def list_all_audience_segments(
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get all audience segments across all clients (for admin/employee view)"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT s.*, 
                   u.full_name as creator_name,
                   client.full_name as client_name
            FROM audience_segments s
            JOIN users u ON s.created_by = u.user_id
            JOIN users client ON s.client_id = client.user_id
            ORDER BY s.created_at DESC
        """)
        
        segments = cursor.fetchall()
        
        for seg in segments:
            if seg['segment_criteria']:
                seg['segment_criteria'] = json.loads(seg['segment_criteria'])
        
        return {"success": True, "segments": segments}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch segments: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/campaigns/details/{campaign_id}", summary="Get single campaign details")
async def get_campaign_details(
    campaign_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get detailed information about a specific campaign"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT c.*, 
                   u.full_name as creator_name,
                   client.full_name as client_name,
                   COUNT(DISTINCT a.ad_id) as total_ads
            FROM ad_campaigns c
            JOIN users u ON c.created_by = u.user_id
            JOIN users client ON c.client_id = client.user_id
            LEFT JOIN ads a ON c.campaign_id = a.campaign_id
            WHERE c.campaign_id = %s
            GROUP BY c.campaign_id
        """, (campaign_id,))
        
        campaign = cursor.fetchone()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        if campaign['target_audience']:
            campaign['target_audience'] = json.loads(campaign['target_audience'])
        if campaign['placement_settings']:
            campaign['placement_settings'] = json.loads(campaign['placement_settings'])
        
        return {"success": True, "campaign": campaign}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch campaign details: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# =================================================================
# COMPLETE FIX - Generate Audience Insights
# This version removes ALL references to non-existent columns
# Replace ENTIRE function in app/api/v1/endpoints/ads.py
# =================================================================

@router.post("/audience/generate-insights", summary="Generate AI insights for client")
async def generate_audience_insights(
    client_id: int = Body(...),
    business_description: str = Body(None),
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Generate AI-powered audience insights based on client profile
    FIXED: Uses correct table names and columns only
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # STEP 1: Get basic user info
        cursor.execute("""
            SELECT 
                user_id,
                full_name, 
                email,
                role
            FROM users
            WHERE user_id = %s
        """, (client_id,))
        
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # STEP 2: Get client profile data (business info)
        cursor.execute("""
            SELECT 
                business_name,
                business_type,
                website_url,
                current_budget
            FROM client_profiles
            WHERE client_id = %s
        """, (client_id,))
        
        profile = cursor.fetchone()
        
        # STEP 3: Get latest project proposal data (if exists)
        cursor.execute("""
            SELECT 
                target_audience,
                business_type as proposal_business_type
            FROM project_proposals
            WHERE client_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (client_id,))
        
        proposal = cursor.fetchone()
        
        # Build business context from available data
        business_name = (profile.get('business_name') if profile else None) or user.get('full_name') or 'Unknown Business'
        business_type = (profile.get('business_type') if profile else None) or (proposal.get('proposal_business_type') if proposal else None) or 'General Business'
        website = (profile.get('website_url') if profile else None) or 'Not provided'
        existing_audience = (proposal.get('target_audience') if proposal else None) or 'Not specified'
        
        print(f"[GENERATE_INSIGHTS] Client: {business_name}, Type: {business_type}")
        
        # Generate AI insights using OpenAI
        prompt = f"""You are an expert digital marketing strategist. Analyze this business and generate COMPREHENSIVE audience insights and segmentation recommendations.

Business Information:
- Company: {business_name}
- Business Type: {business_type}
- Website: {website}
- Existing Target Audience: {existing_audience}
- Additional Notes: {business_description or 'Not provided'}

Provide a detailed JSON response with these EXACT keys (respond with ONLY JSON, no markdown):
{{
    "audience_segments": [
        {{
            "segment_name": "Tech-Savvy Professionals",
            "demographics": {{
                "age_range": "25-45",
                "gender": "All",
                "income_level": "Middle to upper income",
                "education": "College educated",
                "location": "Urban areas"
            }},
            "interests": ["technology", "business", "innovation", "productivity", "professional development"],
            "behaviors": ["online shoppers", "early adopters", "social media active", "content consumers"],
            "pain_points": ["time management", "efficiency", "cost optimization"],
            "platform_recommendations": ["meta", "google", "linkedin"],
            "estimated_size": 250000,
            "priority": "High"
        }},
        {{
            "segment_name": "Decision Makers",
            "demographics": {{
                "age_range": "35-55",
                "gender": "All",
                "income_level": "Upper income",
                "education": "Advanced degree",
                "location": "Urban and suburban"
            }},
            "interests": ["business strategy", "leadership", "management", "ROI"],
            "behaviors": ["B2B buyers", "conference attendees", "LinkedIn active"],
            "pain_points": ["team efficiency", "budget constraints", "competitive pressure"],
            "platform_recommendations": ["linkedin", "google"],
            "estimated_size": 150000,
            "priority": "Medium"
        }}
    ],
    "platform_specific_targeting": {{
        "meta": {{
            "interests": ["Business Tools", "Technology", "Entrepreneurship"],
            "behaviors": ["Small Business Owners", "Engaged Shoppers"],
            "lookalike_potential": "High"
        }},
        "google": {{
            "in_market": ["Business Software", "Professional Services"],
            "affinity": ["Business Professionals", "Tech Enthusiasts"],
            "custom_intent": ["business solutions", "productivity tools"]
        }},
        "linkedin": {{
            "job_titles": ["Manager", "Director", "CEO", "Founder"],
            "industries": ["Technology", "Business Services"],
            "company_sizes": ["50-200", "200-1000"],
            "seniority": ["Manager", "Director", "VP"]
        }}
    }},
    "recommended_budget_allocation": {{
        "meta": 40,
        "google": 35,
        "linkedin": 25
    }},
    "key_messaging_themes": [
        "Increase efficiency and productivity",
        "Reduce costs while improving quality",
        "Stay ahead of competition"
    ],
    "content_recommendations": [
        "Case studies showing ROI",
        "How-to guides and tutorials",
        "Industry trend reports"
    ]
}}

Generate 2-3 relevant audience segments for {business_type} business.
Respond ONLY with valid JSON."""
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3000
        )
        
        # Parse JSON response with multiple fallback strategies
        response_text = response.choices[0].message.content.strip()
        print(f"[GENERATE_INSIGHTS] AI Response length: {len(response_text)} chars")
        
        try:
            # Try direct JSON parse
            insights = json.loads(response_text)
            print(f"[GENERATE_INSIGHTS] Successfully parsed JSON directly")
        except json.JSONDecodeError as e:
            print(f"[GENERATE_INSIGHTS] Direct parse failed: {str(e)}")
            # Try to find JSON in markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    insights = json.loads(json_match.group(1))
                    print(f"[GENERATE_INSIGHTS] Parsed JSON from markdown block")
                except Exception as e2:
                    print(f"[GENERATE_INSIGHTS] Markdown parse failed: {str(e2)}")
                    # Try to find raw JSON
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        insights = json.loads(json_match.group(0))
                        print(f"[GENERATE_INSIGHTS] Parsed raw JSON")
                    else:
                        raise HTTPException(
                            status_code=500,
                            detail="AI response did not contain valid JSON. Please try again."
                        )
            else:
                # Try to find raw JSON
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    insights = json.loads(json_match.group(0))
                    print(f"[GENERATE_INSIGHTS] Parsed raw JSON (no markdown)")
                else:
                    print(f"[GENERATE_INSIGHTS] Response text: {response_text[:500]}...")
                    raise HTTPException(
                        status_code=500,
                        detail="AI response did not contain valid JSON. Please try again."
                    )
        
        return {
            "success": True,
            "insights": insights,
            "client_name": user.get('full_name'),
            "business_name": business_name,
            "business_type": business_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[GENERATE_INSIGHTS] Fatal error: {str(e)}")
        import traceback
        print(f"[GENERATE_INSIGHTS] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

            
# =================================================================
# FIXED MONITORING ENDPOINT - Add to app/api/v1/endpoints/ads.py
# =================================================================

# ========== FEATURE 3: REAL-TIME CAMPAIGN MONITORING (FIXED) ==========

@router.get("/campaigns/monitor/active", summary="Monitor active campaigns with AI recommendations")
async def monitor_active_campaigns(
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get all active campaigns with real-time AI recommendations
    Analyzes performance and provides actionable insights
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Get active campaigns with performance data
        cursor.execute("""
            SELECT c.*, 
                   u.full_name as creator_name,
                   client.full_name as client_name,
                   COUNT(DISTINCT a.ad_id) as total_ads,
                   COALESCE(SUM(ap.impressions), 0) as total_impressions,
                   COALESCE(SUM(ap.clicks), 0) as total_clicks,
                   COALESCE(AVG(ap.ctr), 0) as avg_ctr,
                   COALESCE(AVG(ap.cpc), 0) as avg_cpc,
                   COALESCE(SUM(ap.spend), 0) as total_spend,
                   COALESCE(SUM(ap.conversions), 0) as total_conversions
            FROM ad_campaigns c
            JOIN users u ON c.created_by = u.user_id
            JOIN users client ON c.client_id = client.user_id
            LEFT JOIN ads a ON c.campaign_id = a.campaign_id
            LEFT JOIN ad_performance ap ON a.ad_id = ap.ad_id 
                AND ap.metric_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            WHERE c.status = 'active'
            GROUP BY c.campaign_id
            ORDER BY c.created_at DESC
        """)
        
        campaigns = cursor.fetchall()
        
        if not campaigns:
            return {
                "success": True,
                "active_campaigns": [],
                "total_active": 0
            }
        
        # Generate AI recommendations for each campaign
        monitored_campaigns = []
        
        for campaign in campaigns:
            try:
                # Parse JSON fields
                if campaign.get('target_audience') and isinstance(campaign['target_audience'], str):
                    campaign['target_audience'] = json.loads(campaign['target_audience'])
                if campaign.get('placement_settings') and isinstance(campaign['placement_settings'], str):
                    campaign['placement_settings'] = json.loads(campaign['placement_settings'])
                
                # Generate AI-powered recommendations
                recommendations = await generate_campaign_recommendations(
                    campaign_id=campaign['campaign_id'],
                    performance_metrics={
                        'impressions': int(campaign.get('total_impressions', 0)),
                        'clicks': int(campaign.get('total_clicks', 0)),
                        'ctr': float(campaign.get('avg_ctr', 0)),
                        'cpc': float(campaign.get('avg_cpc', 0)),
                        'spend': float(campaign.get('total_spend', 0)),
                        'conversions': int(campaign.get('total_conversions', 0)),
                        'budget': float(campaign.get('budget', 0))
                    },
                    platform=campaign.get('platform', 'unknown'),
                    objective=campaign.get('objective', 'unknown')
                )
                
                monitored_campaigns.append({
                    **campaign,
                    'ai_recommendations': recommendations
                })
            except Exception as e:
                print(f"[MONITORING] Error processing campaign {campaign.get('campaign_id')}: {str(e)}")
                # Add campaign without recommendations if AI fails
                monitored_campaigns.append({
                    **campaign,
                    'ai_recommendations': {
                        'status': 'Unknown',
                        'status_color': 'gray',
                        'priority_actions': [],
                        'performance_analysis': {},
                        'quick_wins': [],
                        'budget_recommendation': 'Unable to analyze',
                        'error': 'AI analysis failed'
                    }
                })
        
        return {
            "success": True,
            "active_campaigns": monitored_campaigns,
            "total_active": len(monitored_campaigns)
        }
        
    except Exception as e:
        print(f"[MONITORING] Fatal error: {str(e)}")
        print(f"[MONITORING] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to monitor campaigns: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


async def generate_campaign_recommendations(
    campaign_id: int,
    performance_metrics: Dict[str, Any],
    platform: str,
    objective: str
) -> Dict[str, Any]:
    """Generate AI recommendations for campaign optimization"""
    
    try:
        # Calculate some basic metrics
        ctr = performance_metrics.get('ctr', 0)
        cpc = performance_metrics.get('cpc', 0)
        conversions = performance_metrics.get('conversions', 0)
        spend = performance_metrics.get('spend', 0)
        budget = performance_metrics.get('budget', 0)
        
        # Build prompt
        prompt = f"""You are an expert digital advertising analyst. Analyze this campaign performance and provide ACTIONABLE recommendations.

Campaign Details:
- Platform: {platform}
- Objective: {objective}
- Budget: ${budget:.2f}

Performance Metrics (Last 7 Days):
- Impressions: {performance_metrics.get('impressions', 0):,}
- Clicks: {performance_metrics.get('clicks', 0):,}
- CTR: {ctr:.2f}%
- CPC: ${cpc:.2f}
- Total Spend: ${spend:.2f}
- Conversions: {conversions}

Provide a JSON response with these exact keys (respond ONLY with valid JSON, no markdown):
{{
    "status": "Excellent/Good/Needs Attention/Critical",
    "status_color": "green/yellow/orange/red",
    "priority_actions": [
        {{
            "action": "Specific action to take",
            "reason": "Why this action is needed",
            "impact": "Expected impact",
            "priority": "High/Medium/Low"
        }}
    ],
    "performance_analysis": {{
        "ctr_assessment": "Analysis of CTR",
        "cpc_assessment": "Analysis of CPC",
        "spend_efficiency": "Budget utilization analysis",
        "conversion_rate": "Conversion performance"
    }},
    "quick_wins": ["Quick improvement 1", "Quick improvement 2", "Quick improvement 3"],
    "budget_recommendation": "Increase by X%/Decrease by X%/Maintain current",
    "audience_refinement": ["Audience suggestion 1", "Audience suggestion 2"],
    "creative_suggestions": ["Creative idea 1", "Creative idea 2"],
    "estimated_improvement": "X% expected lift"
}}"""
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON with multiple fallback strategies
        try:
            # Try direct JSON parse
            recommendations = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON in markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    recommendations = json.loads(json_match.group(1))
                except:
                    # Try to find raw JSON object
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        recommendations = json.loads(json_match.group(0))
                    else:
                        raise ValueError("No valid JSON found")
            else:
                # Try to find raw JSON object
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    recommendations = json.loads(json_match.group(0))
                else:
                    raise ValueError("No valid JSON found")
        
        # Validate required fields
        required_fields = ['status', 'status_color', 'priority_actions', 'performance_analysis']
        for field in required_fields:
            if field not in recommendations:
                recommendations[field] = get_default_field(field)
        
        return recommendations
        
    except Exception as e:
        print(f"[CAMPAIGN_MONITOR] Error generating recommendations for campaign {campaign_id}: {str(e)}")
        print(f"[CAMPAIGN_MONITOR] Response text: {response_text if 'response_text' in locals() else 'N/A'}")
        
        # Return basic recommendations based on metrics
        return generate_basic_recommendations(performance_metrics, platform, objective)


def get_default_field(field_name: str) -> Any:
    """Get default value for missing field"""
    defaults = {
        'status': 'Unknown',
        'status_color': 'gray',
        'priority_actions': [],
        'performance_analysis': {
            'ctr_assessment': 'Unable to analyze',
            'cpc_assessment': 'Unable to analyze',
            'spend_efficiency': 'Unable to analyze',
            'conversion_rate': 'Unable to analyze'
        },
        'quick_wins': [],
        'budget_recommendation': 'Maintain current',
        'audience_refinement': [],
        'creative_suggestions': [],
        'estimated_improvement': '0%'
    }
    return defaults.get(field_name, None)


def generate_basic_recommendations(
    metrics: Dict[str, Any],
    platform: str,
    objective: str
) -> Dict[str, Any]:
    """Generate basic recommendations without AI when API fails"""
    
    ctr = metrics.get('ctr', 0)
    cpc = metrics.get('cpc', 0)
    conversions = metrics.get('conversions', 0)
    spend = metrics.get('spend', 0)
    budget = metrics.get('budget', 0)
    
    priority_actions = []
    quick_wins = []
    status = 'Good'
    status_color = 'green'
    
    # CTR Analysis
    if ctr < 1.0:
        status = 'Needs Attention'
        status_color = 'orange'
        priority_actions.append({
            'action': 'Improve ad creative and copy',
            'reason': f'CTR is {ctr:.2f}%, below industry benchmark of 1-2%',
            'impact': 'Could increase CTR by 50-100%',
            'priority': 'High'
        })
        quick_wins.append('Test new headline variations')
    
    # CPC Analysis
    if cpc > 5.0:
        priority_actions.append({
            'action': 'Optimize bidding strategy',
            'reason': f'CPC of ${cpc:.2f} is high for {platform}',
            'impact': 'Could reduce CPC by 20-30%',
            'priority': 'Medium'
        })
        quick_wins.append('Refine audience targeting to reduce costs')
    
    # Conversion Analysis
    if conversions == 0 and spend > 0:
        status = 'Critical'
        status_color = 'red'
        priority_actions.append({
            'action': 'Review conversion tracking and landing page',
            'reason': 'No conversions recorded despite active spend',
            'impact': 'Essential for campaign success',
            'priority': 'High'
        })
    
    # Budget Analysis
    budget_utilization = (spend / budget * 100) if budget > 0 else 0
    if budget_utilization < 50:
        quick_wins.append('Increase daily budget to accelerate learning phase')
    elif budget_utilization > 90:
        priority_actions.append({
            'action': 'Monitor budget pacing',
            'reason': f'{budget_utilization:.0f}% of budget spent',
            'impact': 'Avoid budget exhaustion before campaign end',
            'priority': 'Medium'
        })
    
    return {
        'status': status,
        'status_color': status_color,
        'priority_actions': priority_actions[:3],  # Max 3
        'performance_analysis': {
            'ctr_assessment': f'CTR is {ctr:.2f}%' + (' - below benchmark' if ctr < 1.0 else ' - performing well'),
            'cpc_assessment': f'CPC is ${cpc:.2f}' + (' - optimize to reduce costs' if cpc > 5.0 else ' - within acceptable range'),
            'spend_efficiency': f'{budget_utilization:.0f}% of budget utilized',
            'conversion_rate': 'Tracking conversions' if conversions > 0 else 'No conversions yet - review tracking'
        },
        'quick_wins': quick_wins[:3] if quick_wins else ['Continue monitoring performance', 'Test new ad variations', 'Analyze audience insights'],
        'budget_recommendation': 'Increase by 20%' if budget_utilization > 80 and status == 'Good' else 'Maintain current',
        'audience_refinement': ['Add lookalike audiences', 'Exclude non-converting segments'],
        'creative_suggestions': ['Test video ads', 'Add carousel format'],
        'estimated_improvement': '15-25%' if priority_actions else '5-10%'
    }

