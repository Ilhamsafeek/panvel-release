"""
AI Project Planner - Complete API Implementation (No Migration Required)
File: app/api/v1/endpoints/project_planner.py
"""

from fastapi import APIRouter, HTTPException, status, Depends, Response, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pymysql
import json
import secrets
from io import BytesIO
import requests

from app.core.config import settings
from app.services.ai_service import AIService
from app.core.security import require_admin_or_employee
from app.core.security import get_db_connection

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


router = APIRouter()



# ========== PYDANTIC MODELS ==========

class ProjectInput(BaseModel):
    """Lead/Prospect project discovery input"""
    lead_name: str
    lead_email: str
    company_name: str
    business_type: str
    website_url: Optional[str] = None
    budget: float
    challenges: str
    target_audience: str
    existing_presence: Optional[Dict[str, Any]] = {}


class ProposalEdit(BaseModel):
    """Model for editing proposals - accepts HTML content"""
    strategy: Optional[str] = None
    differentiators: Optional[str] = None
    timeline: Optional[str] = None
    custom_notes: Optional[str] = None
    tone: Optional[str] = None


class SendProposalRequest(BaseModel):
    """Model for sending proposals"""
    lead_email: str
    lead_name: str
    send_immediately: bool = True
    scheduled_time: Optional[datetime] = None
    include_sections: Optional[List[str]] = None
    custom_message: Optional[str] = None



# Email Request Model
class EmailRequest(BaseModel):
    recipient_email: EmailStr
    recipient_name: Optional[str] = "Valued Client"
    subject: Optional[str] = None
    message: Optional[str] = None
    include_pdf: bool = True



# ========== DATABASE CONNECTION ==========

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    try:
        cursor.execute(f"""
            SELECT COUNT(*) as count
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = %s 
            AND COLUMN_NAME = %s
        """, (table_name, column_name))
        result = cursor.fetchone()
        return result['count'] > 0
    except:
        return False


# ========== API ENDPOINTS ==========
@router.post("/generate-proposal")
async def generate_proposal(
    project_input: ProjectInput,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Generate AI-powered project proposal"""
    connection = None
    cursor = None
    
    try:
        print(f"\n{'='*60}")
        print(f"[PROPOSAL] Generating for {project_input.company_name}")
        print(f"{'='*60}")
        
        # Initialize AI Service
        ai_service = AIService()
        
        # Generate Strategy
        print("[1/6] Generating Strategy...")
        strategy_prompt = f"""
        Create a comprehensive digital marketing strategy for:
        Company: {project_input.company_name}
        Website: {project_input.website_url or 'Not provided'}
        Business Type: {project_input.business_type}
        Budget: ${project_input.budget}
        Challenges: {project_input.challenges}
        Target Audience: {project_input.target_audience}
        Existing Presence: {json.dumps(project_input.existing_presence)}
        
        Include:
        - Recommended campaigns (ad, email, SEO, social media)
        - Platform recommendations
        - Creative formats
        - Content topics
        - Automation tools
        
        Format as JSON with campaigns and automation_tools arrays.
        """
        
        ai_strategy = await ai_service.generate_strategy(strategy_prompt)
        print("   ✓ Strategy generated")
        
        # Generate Differentiators
        print("[2/6] Generating Differentiators...")
        differentiator_prompt = f"""
        Create competitive differentiators for a digital marketing agency proposal.
        Budget: ${project_input.budget}
        Business Type: {project_input.business_type}
        
        Highlight:
        - Faster deployment with automation
        - AI-personalized targeting
        - Cost-efficiency
        - Advanced performance tracking
        
        Format as JSON with differentiators array containing title, description, and impact.
        """
        
        differentiators = await ai_service.generate_differentiators(differentiator_prompt)
        print("   ✓ Differentiators generated")
        
        # Generate Value Propositions (NEW)
        print("[3/6] Generating Value Propositions...")
        vp_prompt = f"""
        Create 4-5 unique value propositions for {project_input.company_name} ({project_input.business_type}).
        Budget: ${project_input.budget}
        
        For each value proposition provide:
        - title: Catchy, benefit-focused (with emoji)
        - description: Clear 2-3 sentence explanation
        - competitive_advantage: Why this beats competitors
        - impact: Expected business impact
        
        Format as JSON array with objects containing: title, description, competitive_advantage, impact
        """
        value_propositions = await ai_service.generate_content(vp_prompt, "value_props")
        print("   ✓ Value Propositions generated")
        
        # Generate Competitive Analysis (NEW)
        print("[4/6] Performing Competitive Analysis...")
        comp_prompt = f"""
        Analyze competitive landscape for {project_input.business_type} business: {project_input.company_name}
        Budget: ${project_input.budget}
        Target Audience: {project_input.target_audience}
        
        Provide competitive intelligence with:
        - opportunities: Array of 4-5 specific opportunities where competitors are weak
        - threats: Array of 3-4 competitive threats/challenges
        - key_insights: Array of 3 critical insights about the market
        - opportunity_score: Score 0-100 indicating market opportunity
        
        Format as JSON with keys: opportunities, threats, key_insights, opportunity_score
        """
        competitive_analysis = await ai_service.generate_content(comp_prompt, "competitive")
        print("   ✓ Competitive Analysis complete")
        
        # Generate ROI Simulation (NEW)
        print("[5/6] Generating ROI Simulation...")
        roi_prompt = f"""
        Create realistic ROI simulation for:
        Budget: ${project_input.budget}
        Business Type: {project_input.business_type}
        Target Audience: {project_input.target_audience}
        
        Provide "If you spend $X, expect Y leads" projections:
        - expected_leads: Object with month_1, month_3, month_6, month_12 (number of leads)
        - cost_per_lead: Object with average, best_case, worst_case (dollar amounts)
        - conversion_rate: Percentage (e.g., 5 for 5%)
        - estimated_customers: Number of customers from leads
        - estimated_revenue: Total revenue expected (dollar amount)
        - roi_percentage: Overall ROI percentage
        - timeframe_to_roi: Months to break even
        
        Format as JSON with above keys. Be realistic based on industry benchmarks.
        """
        roi_simulation = await ai_service.generate_content(roi_prompt, "roi")
        print("   ✓ ROI Simulation complete")

        # Generate Achievability Assessment (NEW - Client Request)
        print("[6/7] Evaluating Achievability...")
        achievability_prompt = f"""
        Evaluate if client expectations are achievable:

        Client Details:
        - Company: {project_input.company_name}
        - Budget: ${project_input.budget}
        - Challenges: {project_input.challenges}
        - Target Audience: {project_input.target_audience}
        - Business Type: {project_input.business_type}

        Provide realistic assessment:
        - achievability_score: 0-100 (100 = highly achievable)
        - status: "Realistic" / "Optimistic" / "Needs Adjustment"
        - assessment: 2-3 sentence explanation
        - recommendations: Array of 2-3 suggestions to improve achievability
        - risk_factors: Array of 2-3 potential risks

        Format as JSON with above keys.
        """
        achievability = await ai_service.generate_content(achievability_prompt, "achievability")
        print("   ✓ Achievability Assessment complete")

        
        # Generate Timeline
        print("[6/6] Generating Timeline...")
        # Generate Timeline
        timeline_prompt = f"""
        You are a digital marketing project manager creating a detailed implementation timeline.

        Client Information:
        - Company: {project_input.company_name}
        - Business Type: {project_input.business_type}
        - Budget: ${project_input.budget}
        - Challenges: {project_input.challenges}
        - Target Audience: {project_input.target_audience}

        Create a comprehensive 4-6 phase project timeline for implementing their digital marketing strategy.

        Each phase MUST include:
        1. phase: Phase name (e.g., "Discovery & Strategy", "Campaign Development")
        2. duration: Duration in weeks or specific timeframe (e.g., "4 weeks", "Week 1-4")
        3. milestones: Array of 3-5 specific milestones for each phase
        4. deliverables: Array of 3-4 key deliverables for each phase

        Phases should cover the complete marketing implementation lifecycle:
        - Phase 1: Discovery, audit, strategy planning
        - Phase 2: Campaign setup, content creation, creative development
        - Phase 3: Launch preparation, testing, optimization setup
        - Phase 4: Campaign launch, monitoring, initial optimization
        - Phase 5: Performance analysis, scaling successful campaigns
        - Phase 6 (optional): Ongoing optimization, reporting, continuous improvement

        CRITICAL: Return ONLY valid JSON with NO markdown, NO code blocks, NO explanations.

        Required JSON structure (exactly like this):
        {{
        "phases": [
            {{
            "phase": "Discovery & Strategy",
            "duration": "3-4 weeks",
            "milestones": [
                "Complete brand and competitor audit",
                "Finalize target audience personas",
                "Set up tracking and analytics infrastructure",
                "Establish KPI baselines and success metrics"
            ],
            "deliverables": [
                "Comprehensive marketing strategy document",
                "Detailed audience personas",
                "Analytics dashboard setup",
                "KPI tracking system"
            ]
            }},
            {{
            "phase": "Campaign Development",
            "duration": "4-5 weeks",
            "milestones": [
                "Create campaign concepts and messaging",
                "Develop content calendar",
                "Design creative assets",
                "Set up campaign infrastructure"
            ],
            "deliverables": [
                "Campaign creative assets",
                "Content calendar for 90 days",
                "Ad campaign structure",
                "Landing pages and conversion funnels"
            ]
            }}
        ]
        }}

        Make it specific to {project_input.business_type} industry with a ${project_input.budget} budget.
        Use realistic timelines based on industry standards.
        Total timeline should be 12-24 weeks for complete implementation.
        Include both milestones AND deliverables for each phase.
        """

        timeline = await ai_service.generate_timeline(timeline_prompt)
        print("   ✓ Timeline generated")
        
        # Save to Database
        print("[SAVE] Saving to database...")
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check if lead exists
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (project_input.lead_email.lower(),))
        lead_user = cursor.fetchone()
        
        if not lead_user:
            cursor.execute("""
                INSERT INTO users (email, password_hash, full_name, role, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (project_input.lead_email.lower(), '', project_input.lead_name, 'client', 'pending'))
            connection.commit()
            lead_user_id = cursor.lastrowid
        else:
            lead_user_id = lead_user['user_id']
        
        # Insert proposal with NEW fields
        cursor.execute("""
            INSERT INTO project_proposals 
            (client_id, created_by, lead_name, lead_email, company_name, website_url, 
            business_type, budget, challenges, target_audience, existing_presence, 
            ai_generated_strategy, competitive_differentiators, value_propositions,
            competitive_analysis, roi_simulation, achievability_assessment, suggested_timeline, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            lead_user_id,
            current_user['user_id'],
            project_input.lead_name,
            project_input.lead_email,
            project_input.company_name,
            project_input.website_url,
            project_input.business_type,
            project_input.budget,
            project_input.challenges,
            project_input.target_audience,
            json.dumps(project_input.existing_presence or {}),
            json.dumps(ai_strategy),
            json.dumps(differentiators),
            json.dumps(value_propositions) if value_propositions else '[]',      # NEW
            json.dumps(competitive_analysis) if competitive_analysis else '{}',  # NEW
            json.dumps(roi_simulation) if roi_simulation else '{}',              # NEW
            json.dumps(achievability) if achievability else '{}',  # NEW
            json.dumps(timeline),
            'draft'
        ))
        
        connection.commit()
        proposal_id = cursor.lastrowid
        
        print(f"\n✅ SUCCESS! Proposal ID: {proposal_id}")
        print(f"{'='*60}\n")
        
        # Fetch the complete proposal record
        cursor.execute("""
            SELECT pp.*, u.full_name as client_full_name, u.email as client_email
            FROM project_proposals pp
            LEFT JOIN users u ON pp.client_id = u.user_id
            WHERE pp.proposal_id = %s
        """, (proposal_id,))
        
        complete_proposal = cursor.fetchone()
        
        # Parse JSON fields for frontend
        json_fields = ['existing_presence', 'ai_generated_strategy', 
                      'competitive_differentiators', 'value_propositions',
                      'competitive_analysis', 'roi_simulation', 'suggested_timeline']
        
        for field in json_fields:
            if complete_proposal.get(field):
                if isinstance(complete_proposal[field], str):
                    try:
                        complete_proposal[field] = json.loads(complete_proposal[field])
                    except:
                        complete_proposal[field] = {} if field != 'value_propositions' else []
        
        return {
            "success": True,
            "message": "Proposal generated successfully with competitive analysis and ROI simulation",
            "proposal_id": proposal_id,
            "proposal": complete_proposal
        }
    
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"\n❌ ERROR: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            
                      

@router.put("/proposals/{proposal_id}/edit")
async def edit_proposal(
    proposal_id: int,
    edits: ProposalEdit,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Edit proposal - stores edited HTML in custom_notes field"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get existing proposal
        cursor.execute("SELECT * FROM project_proposals WHERE proposal_id = %s", (proposal_id,))
        proposal = cursor.fetchone()
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Check which columns exist
        has_custom_html_columns = column_exists(cursor, 'project_proposals', 'custom_strategy_html')
        
        # Build update based on available columns
        if has_custom_html_columns:
            # New schema - use custom HTML columns
            update_fields = []
            update_values = []
            
            if edits.strategy is not None:
                update_fields.append("custom_strategy_html = %s")
                update_values.append(edits.strategy)
            
            if edits.differentiators is not None:
                update_fields.append("custom_differentiators_html = %s")
                update_values.append(edits.differentiators)
            
            if edits.timeline is not None:
                update_fields.append("custom_timeline_html = %s")
                update_values.append(edits.timeline)
            
            if edits.custom_notes is not None:
                update_fields.append("custom_notes = %s")
                update_values.append(edits.custom_notes)
            
            if edits.tone is not None and column_exists(cursor, 'project_proposals', 'tone'):
                update_fields.append("tone = %s")
                update_values.append(edits.tone)
        else:
            # Old schema - store everything in custom_notes as JSON
            edited_content = {
                "strategy_html": edits.strategy,
                "differentiators_html": edits.differentiators,
                "timeline_html": edits.timeline,
                "tone": edits.tone,
                "edited_at": datetime.now().isoformat()
            }
            
            update_fields = ["custom_notes = %s"]
            update_values = [json.dumps(edited_content)]
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_fields.append("updated_at = NOW()")
        update_values.append(proposal_id)
        
        update_query = f"""
            UPDATE project_proposals 
            SET {', '.join(update_fields)}
            WHERE proposal_id = %s
        """
        
        cursor.execute(update_query, tuple(update_values))
        connection.commit()
        
        print(f"[EDIT] Proposal {proposal_id} updated (schema: {'new' if has_custom_html_columns else 'old'})")
        
        return {
            "success": True,
            "message": "Proposal updated successfully",
            "proposal_id": proposal_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"[EDIT] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/proposals/list")
async def list_proposals(current_user: dict = Depends(require_admin_or_employee)):
    """Get all proposals"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT p.proposal_id, p.business_type, p.budget, p.status, p.created_at,
                   u.full_name as client_name, u.email as client_email,u.email as client_email, p.company_name
            FROM project_proposals p
            JOIN users u ON p.client_id = u.user_id
            ORDER BY p.created_at DESC
        """
        cursor.execute(query)
        proposals = cursor.fetchall()
        
        for proposal in proposals:
            if proposal.get('created_at'):
                proposal['created_at'] = proposal['created_at'].isoformat()
        
        return {
            "success": True,
            "proposals": proposals,
            "total": len(proposals)
        }
    
    except Exception as e:
        print(f"Error listing proposals: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/proposals/{proposal_id}/debug")
async def debug_proposal(
    proposal_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Debug endpoint to see raw database data"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = "SELECT * FROM project_proposals WHERE proposal_id = %s"
        cursor.execute(query, (proposal_id,))
        proposal = cursor.fetchone()
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Get raw data
        debug_info = {
            "proposal_id": proposal['proposal_id'],
            "strategy_raw_type": str(type(proposal.get('ai_generated_strategy'))),
            "strategy_raw_value": str(proposal.get('ai_generated_strategy'))[:500],
            "timeline_raw_type": str(type(proposal.get('suggested_timeline'))),
            "timeline_raw_value": str(proposal.get('suggested_timeline'))[:500],
            "diff_raw_type": str(type(proposal.get('competitive_differentiators'))),
            "diff_raw_value": str(proposal.get('competitive_differentiators'))[:500],
        }
        
        # Try to parse
        for field in ['ai_generated_strategy', 'suggested_timeline', 'competitive_differentiators']:
            if proposal.get(field):
                try:
                    if isinstance(proposal[field], str):
                        parsed = json.loads(proposal[field])
                        debug_info[f"{field}_parsed_keys"] = list(parsed.keys()) if isinstance(parsed, dict) else "NOT_A_DICT"
                    elif isinstance(proposal[field], dict):
                        debug_info[f"{field}_parsed_keys"] = list(proposal[field].keys())
                    else:
                        debug_info[f"{field}_parsed_keys"] = "UNKNOWN_TYPE"
                except Exception as e:
                    debug_info[f"{field}_error"] = str(e)
        
        return {
            "success": True,
            "debug": debug_info
        }
    
    except Exception as e:
        print(f"Debug error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@router.get("/proposals/{proposal_id}")
async def get_proposal(
    proposal_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get a single proposal with all details"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT 
                pp.*,
                creator.full_name as created_by_name
            FROM project_proposals pp
            LEFT JOIN users creator ON pp.created_by = creator.user_id
            WHERE pp.proposal_id = %s
        """, (proposal_id,))
        
        proposal = cursor.fetchone()
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Parse JSON fields
        json_fields = ['existing_presence', 'ai_generated_strategy', 
                      'competitive_differentiators', 'suggested_timeline']
        
        for field in json_fields:
            if proposal.get(field):
                if isinstance(proposal[field], str):
                    try:
                        proposal[field] = json.loads(proposal[field])
                    except:
                        proposal[field] = {}
        
        return {
            "success": True,
            "proposal": proposal
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/proposals")
async def get_proposals(
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get all proposals for current user"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Query based on role
        if current_user['role'] == 'client':
            cursor.execute("""
                SELECT 
                    pp.*,
                    creator.full_name as created_by_name
                FROM project_proposals pp
                LEFT JOIN users creator ON pp.created_by = creator.user_id
                WHERE pp.client_id = %s
                ORDER BY pp.created_at DESC
            """, (current_user['user_id'],))
        else:  # admin or employee
            cursor.execute("""
                SELECT 
                    pp.*,
                    creator.full_name as created_by_name
                FROM project_proposals pp
                LEFT JOIN users creator ON pp.created_by = creator.user_id
                ORDER BY pp.created_at DESC
            """)
        
        proposals = cursor.fetchall()
        
        # Parse JSON fields for each proposal
        for proposal in proposals:
            json_fields = ['existing_presence', 'ai_generated_strategy', 
                          'competitive_differentiators', 'suggested_timeline']
            
            for field in json_fields:
                if proposal.get(field):
                    if isinstance(proposal[field], str):
                        try:
                            proposal[field] = json.loads(proposal[field])
                        except:
                            proposal[field] = {}
        
        return {
            "success": True,
            "proposals": proposals
        }
        
    except Exception as e:
        print(f"Error fetching proposals: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.post("/proposals/{proposal_id}/send")
async def send_proposal(
    proposal_id: int,
    send_data: SendProposalRequest,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Send proposal to client"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get proposal
        cursor.execute("SELECT * FROM project_proposals WHERE proposal_id = %s", (proposal_id,))
        proposal = cursor.fetchone()
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Check if scheduled_send_time column exists
        has_scheduled_column = column_exists(cursor, 'project_proposals', 'scheduled_send_time')
        
        # Update status
        if send_data.send_immediately:
            cursor.execute("""
                UPDATE project_proposals 
                SET status = %s, sent_at = NOW()
                WHERE proposal_id = %s
            """, ('sent', proposal_id))
            
            print(f"[SEND] Proposal sent to {send_data.lead_email}")
            message = "Proposal sent successfully"
        else:
            if has_scheduled_column:
                cursor.execute("""
                    UPDATE project_proposals 
                    SET status = %s, scheduled_send_time = %s
                    WHERE proposal_id = %s
                """, ('scheduled', send_data.scheduled_time, proposal_id))
            else:
                # Store in custom_notes if column doesn't exist
                cursor.execute("""
                    UPDATE project_proposals 
                    SET status = %s, custom_notes = %s
                    WHERE proposal_id = %s
                """, ('scheduled', json.dumps({"scheduled_time": send_data.scheduled_time.isoformat()}), proposal_id))
            
            message = f"Proposal scheduled for {send_data.scheduled_time}"
        
        connection.commit()
        
        return {
            "success": True,
            "message": message
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error sending proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.post("/proposals/{proposal_id}/generate-link")
async def generate_shareable_link(
    proposal_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Generate shareable link for proposal with 30-day expiry"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check if proposal exists
        cursor.execute("""
            SELECT proposal_id, client_id 
            FROM project_proposals 
            WHERE proposal_id = %s
        """, (proposal_id,))
        proposal = cursor.fetchone()
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Generate unique token
        share_token = secrets.token_urlsafe(32)
        
        # Calculate expiry date (30 days from now)
        expires_at = datetime.now() + timedelta(days=30)
        
        # Check table structure to determine which columns exist
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'proposal_share_links'
        """)
        columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
        
        has_is_active = 'is_active' in columns
        has_view_count = 'view_count' in columns
        
        # Delete existing links for this proposal (simpler approach)
        cursor.execute("""
            DELETE FROM proposal_share_links 
            WHERE proposal_id = %s
        """, (proposal_id,))
        
        # Insert new share link based on available columns
        if has_is_active and has_view_count:
            cursor.execute("""
                INSERT INTO proposal_share_links 
                (proposal_id, share_token, created_by, expires_at, is_active, view_count)
                VALUES (%s, %s, %s, %s, TRUE, 0)
            """, (proposal_id, share_token, current_user['user_id'], expires_at))
        elif has_is_active:
            cursor.execute("""
                INSERT INTO proposal_share_links 
                (proposal_id, share_token, created_by, expires_at, is_active)
                VALUES (%s, %s, %s, %s, TRUE)
            """, (proposal_id, share_token, current_user['user_id'], expires_at))
        else:
            # Basic insert without optional columns
            cursor.execute("""
                INSERT INTO proposal_share_links 
                (proposal_id, share_token, created_by, expires_at)
                VALUES (%s, %s, %s, %s)
            """, (proposal_id, share_token, current_user['user_id'], expires_at))
        
        connection.commit()
        
        # Generate the share URL
        base_url = getattr(settings, 'FRONTEND_URL', 'https://panvel-iq.calim.ai')
        share_link = f"{base_url}/proposals/view/{share_token}"
        
        print(f"[LINK] Generated share link for proposal {proposal_id}, expires: {expires_at}")
        
        return {
            "success": True,
            "share_link": share_link,
            "expires_at": expires_at.isoformat(),
            "expires_in": "30 days"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error generating share link: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@router.get("/proposals/shared/{share_token}")
async def get_shared_proposal(share_token: str):
    """
    Public endpoint to view a shared proposal via token
    No authentication required - validates token and expiry
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # First, get the columns that exist in the table
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'proposal_share_links'
        """)
        columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
        
        # Determine primary key column name
        pk_column = 'id' if 'id' in columns else 'link_id' if 'link_id' in columns else columns[0]
        has_is_active = 'is_active' in columns
        has_view_count = 'view_count' in columns
        has_last_viewed = 'last_viewed_at' in columns
        
        # Find the share link and validate
        cursor.execute(f"""
            SELECT * FROM proposal_share_links
            WHERE share_token = %s
        """, (share_token,))
        
        share_link = cursor.fetchone()
        
        if not share_link:
            raise HTTPException(
                status_code=404, 
                detail="Invalid or expired share link"
            )
        
        # Check if link is active (if column exists)
        if has_is_active and not share_link.get('is_active', True):
            raise HTTPException(
                status_code=410, 
                detail="This share link has been deactivated"
            )
        
        # Check if link has expired
        expires_at = share_link.get('expires_at')
        if expires_at and datetime.now() > expires_at:
            # Mark as inactive if column exists
            if has_is_active:
                cursor.execute(f"""
                    UPDATE proposal_share_links 
                    SET is_active = FALSE 
                    WHERE {pk_column} = %s
                """, (share_link[pk_column],))
                connection.commit()
            
            raise HTTPException(
                status_code=410, 
                detail="This share link has expired"
            )
        
        # Fetch the proposal data
        proposal_id = share_link['proposal_id']
        cursor.execute("""
            SELECT 
                pp.*,
                u.full_name as client_name,
                u.email as client_email,
                creator.full_name as created_by_name
            FROM project_proposals pp
            LEFT JOIN users u ON pp.client_id = u.user_id
            LEFT JOIN users creator ON pp.created_by = creator.user_id
            WHERE pp.proposal_id = %s
        """, (proposal_id,))
        
        proposal = cursor.fetchone()
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Update view count if column exists
        if has_view_count:
            update_parts = ["view_count = COALESCE(view_count, 0) + 1"]
            if has_last_viewed:
                update_parts.append("last_viewed_at = NOW()")
            
            cursor.execute(f"""
                UPDATE proposal_share_links 
                SET {', '.join(update_parts)}
                WHERE {pk_column} = %s
            """, (share_link[pk_column],))
            connection.commit()
        
        # Parse JSON fields
        def safe_json_parse(data, default=None):
            if data is None:
                return default
            if isinstance(data, (dict, list)):
                return data
            try:
                return json.loads(data) if data else default
            except:
                return default
        
        # Format proposal for public view
        proposal_data = {
            "proposal_id": proposal['proposal_id'],
            "client_name": proposal.get('client_name', 'Client'),
            "company_name": proposal.get('company_name', ''),
            "business_type": proposal.get('business_type', ''),
            "budget": float(proposal['budget']) if proposal.get('budget') else 0,
            "challenges": proposal.get('challenges', ''),
            "target_audience": proposal.get('target_audience', ''),
            "ai_generated_strategy": safe_json_parse(proposal.get('ai_generated_strategy'), {}),
            "competitive_differentiators": safe_json_parse(proposal.get('competitive_differentiators'), {}),
            "suggested_timeline": safe_json_parse(proposal.get('suggested_timeline'), {}),
            "status": proposal.get('status', 'draft'),
            "created_at": proposal['created_at'].isoformat() if proposal.get('created_at') else None,
            "created_by_name": proposal.get('created_by_name', 'PanvelIQ Team')
        }
        
        # Calculate days remaining
        days_remaining = 30  # Default
        if expires_at:
            days_remaining = (expires_at - datetime.now()).days
        
        view_count = share_link.get('view_count', 0) or 0
        
        return {
            "success": True,
            "proposal": proposal_data,
            "link_info": {
                "expires_at": expires_at.isoformat() if expires_at else None,
                "days_remaining": max(0, days_remaining),
                "view_count": view_count + 1
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching shared proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/proposals/{proposal_id}/export/pdf")
async def export_proposal_pdf(
    proposal_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Export proposal as PDF with DRAFT watermark if not approved"""
    connection = None
    cursor = None
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
        from PyPDF2 import PdfReader, PdfWriter
        from html import unescape
        import re
        from io import BytesIO
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get proposal with status
        cursor.execute("""
            SELECT p.*, u.full_name as client_name, u.email as client_email
            FROM project_proposals p
            LEFT JOIN users u ON p.client_id = u.user_id
            WHERE p.proposal_id = %s
        """, (proposal_id,))
        
        proposal = cursor.fetchone()
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Check if approved
        is_approved = proposal.get('status') == 'accepted'
        print(f"📋 Proposal Status: {proposal.get('status')} | Approved: {is_approved}")
        
        # Parse JSON fields
        def safe_json_parse(data, default=None):
            if data is None:
                return default
            if isinstance(data, (dict, list)):
                return data
            try:
                return json.loads(data) if data else default
            except:
                return default
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75*inch, bottomMargin=0.75*inch)
        
        # Setup styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#9926F3'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1DD8FC'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY
        )
        
        # Build PDF content
        story = []
        
        # Cover Page
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph("DIGITAL MARKETING PROPOSAL", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        company_name = proposal.get('company_name') or proposal.get('client_name') or 'Valued Client'
        story.append(Paragraph(f"Prepared for {company_name}", body_style))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", body_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Business Overview
        story.append(Paragraph("Business Overview", heading_style))
        if proposal.get('business_type'):
            story.append(Paragraph(f"<b>Business Type:</b> {proposal['business_type']}", body_style))
            story.append(Spacer(1, 0.1*inch))
        if proposal.get('budget'):
            story.append(Paragraph(f"<b>Budget:</b> ${float(proposal['budget']):,.2f}", body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Challenges
        if proposal.get('challenges'):
            story.append(Paragraph("Challenges & Objectives", heading_style))
            story.append(Paragraph(proposal['challenges'], body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Target Audience
        if proposal.get('target_audience'):
            story.append(Paragraph("Target Audience", heading_style))
            story.append(Paragraph(proposal['target_audience'], body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # AI Strategy
        ai_strategy = safe_json_parse(proposal.get('ai_generated_strategy'), {})
        if ai_strategy:
            story.append(Paragraph("Recommended Strategy", heading_style))
            for key, value in ai_strategy.items():
                if value:
                    clean_key = key.replace('_', ' ').title()
                    story.append(Paragraph(f"<b>{clean_key}:</b> {value}", body_style))
                    story.append(Spacer(1, 0.1*inch))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_text = f"""
        <b>PanvelIQ - AI-Powered Digital Marketing</b><br/>
        Email: info@panveliq.com | Website: www.panveliq.com<br/>
        <i>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>
        """
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER
        )
        story.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # =====================================================
        # ADD DRAFT WATERMARK IF NOT APPROVED
        # =====================================================
        if not is_approved:
            print("⚠️ Adding DRAFT watermark...")
            
            # Read the generated PDF
            pdf_reader = PdfReader(buffer)
            pdf_writer = PdfWriter()
            
            # Add watermark to each page
            for page in pdf_reader.pages:
                # Get page dimensions
                page_box = page.mediabox
                page_width = float(page_box.width)
                page_height = float(page_box.height)
                
                # Create watermark
                watermark_buffer = BytesIO()
                watermark_canvas = canvas.Canvas(watermark_buffer, pagesize=(page_width, page_height))
                
                # Draw diagonal DRAFT watermark
                watermark_canvas.saveState()
                watermark_canvas.translate(page_width / 2, page_height / 2)
                watermark_canvas.rotate(45)
                watermark_canvas.setFillColor(colors.Color(0.8, 0.1, 0.1, alpha=0.2))
                watermark_canvas.setFont("Helvetica-Bold", 80)
                
                text = "DRAFT"
                text_width = watermark_canvas.stringWidth(text, "Helvetica-Bold", 80)
                watermark_canvas.drawString(-text_width / 2, 0, text)
                watermark_canvas.restoreState()
                watermark_canvas.save()
                
                # Merge watermark with page
                watermark_buffer.seek(0)
                watermark_page = PdfReader(watermark_buffer).pages[0]
                page.merge_page(watermark_page)
                pdf_writer.add_page(page)
            
            # Write watermarked PDF
            final_buffer = BytesIO()
            pdf_writer.write(final_buffer)
            final_buffer.seek(0)
            buffer = final_buffer
            print(" DRAFT watermark applied")
        else:
            print(" No watermark needed (approved)")
        
        # Generate filename
        safe_company_name = str(company_name).replace(' ', '_').replace('/', '_')
        filename = f"Proposal_{safe_company_name}_{proposal_id}.pdf"
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    
    except ImportError as ie:
        raise HTTPException(
            status_code=501,
            detail="PDF export requires reportlab and PyPDF2. Install: pip install reportlab PyPDF2"
        )
    except Exception as e:
        print(f"PDF Export Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

            
def generate_proposal_html_for_pdf(proposal, strategy, differentiators, timeline):
    """Generate HTML from AI data if no edited content exists"""
    
    # Extract data with proper key checking
    campaigns = strategy.get('Recommended_Campaigns', strategy.get('campaigns', []))
    tools = strategy.get('Automation_Tools', strategy.get('automation_tools', []))
    diff_items = differentiators.get('differentiators', [])
    phases = timeline.get('phases', [])
    
    company_name = proposal.get('company_name') or strategy.get('Company') or 'Your Company'
    budget = proposal.get('budget') or strategy.get('Budget') or 0
    business_type = proposal.get('business_type') or strategy.get('Business_Type') or 'business'
    challenges = proposal.get('challenges') or (', '.join(strategy.get('Challenges', [])) if strategy.get('Challenges') else 'Business challenges')
    target_audience = proposal.get('target_audience') or strategy.get('Target_Audience') or 'Target audience'
    
    # Build campaigns HTML
    campaigns_html = ""
    if campaigns:
        for camp in campaigns:
            campaign_type = camp.get('Type') or camp.get('type') or 'Campaign'
            platform = camp.get('Platform') or camp.get('platform') or ''
            platform_text = ', '.join(platform) if isinstance(platform, list) else platform
            topics = camp.get('Content_Topics') or camp.get('content_topics') or []
            topics_text = ', '.join(topics) if isinstance(topics, list) else ''
            budget_pct = camp.get('Budget_Allocation_Percentage') or ''
            
            campaigns_html += f"<li><strong>{campaign_type}</strong>"
            if platform_text:
                campaigns_html += f" ({platform_text})"
            campaigns_html += f": {topics_text}"
            if budget_pct:
                campaigns_html += f" <em>({budget_pct}% of budget)</em>"
            campaigns_html += "</li>"
    else:
        campaigns_html = "<li>Customized marketing campaigns based on your business needs</li>"
    
    # Build tools HTML
    tools_html = ""
    if tools:
        for tool in tools:
            tool_name = tool.get('Tool') or tool.get('tool') or tool.get('name') or 'Marketing Tool'
            purpose = tool.get('Purpose') or tool.get('purpose') or 'Campaign enhancement'
            budget_pct = tool.get('Budget_Allocation_Percentage') or ''
            
            tools_html += f"<li><strong>{tool_name}:</strong> {purpose}"
            if budget_pct:
                tools_html += f" <em>({budget_pct}% of budget)</em>"
            tools_html += "</li>"
    else:
        tools_html = "<li>Marketing automation and analytics tools</li>"
    
    # Build differentiators HTML
    diff_html = ""
    if diff_items:
        for diff in diff_items:
            title = diff.get('title', 'Competitive Advantage')
            description = diff.get('description', '')
            impact = diff.get('impact', 'Positive impact on results')
            diff_html += f"""
            <li>
                <strong>{title}:</strong> {description}<br>
                <em>Impact: {impact}</em>
            </li>
            """
    else:
        diff_html = "<li><strong>AI-Powered Approach:</strong> Leveraging technology for optimal results<br><em>Impact: Increased efficiency and ROI</em></li>"
    
    # Build timeline HTML
    timeline_html = ""
    if phases:
        for idx, phase in enumerate(phases, 1):
            phase_name = phase.get('phase') or phase.get('name') or f"Phase {idx}"
            duration = phase.get('duration', 'TBD')
            deliverables = phase.get('deliverables', [])
            
            timeline_html += f"""
            <h3><strong>Phase {idx}: {phase_name}</strong></h3>
            <p><strong>Duration:</strong> {duration}</p>
            <p><strong>Key Deliverables:</strong></p>
            <ul>
            """
            for deliverable in deliverables:
                timeline_html += f"<li>{deliverable}</li>"
            timeline_html += "</ul>"
    else:
        timeline_html = """
        <h3><strong>Phase 1: Planning & Setup</strong></h3>
        <p><strong>Duration:</strong> 2-4 weeks</p>
        <ul><li>Initial strategy development and campaign setup</li></ul>
        """
    
    return f"""
    <h1>Digital Marketing Proposal</h1>
    <h2>for {company_name}</h2>
    <p style="text-align: center;"><em>Prepared by PanvelIQ</em></p>
    
    <hr>
    
    <h2><strong>Executive Summary</strong></h2>
    <p>This comprehensive digital marketing proposal has been specifically designed for <strong>{company_name}</strong>, a {business_type} looking to enhance their digital presence and drive measurable growth.</p>
    <p>Our AI-powered approach combines cutting-edge marketing technology with proven strategies to deliver exceptional results within your investment budget of <strong>${budget:,.2f}</strong>.</p>
    
    <h2><strong>Current Challenges</strong></h2>
    <p>{challenges}</p>
    
    <h2><strong>Target Audience Analysis</strong></h2>
    <p>{target_audience}</p>
    
    <h2><strong>Recommended Marketing Strategy</strong></h2>
    <p>Based on our AI analysis, we recommend a comprehensive marketing approach across multiple channels.</p>
    
    <h3><strong>Recommended Campaigns</strong></h3>
    <ul>
        {campaigns_html}
    </ul>
    
    <h3><strong>Automation Tools & Technologies</strong></h3>
    <ul>
        {tools_html}
    </ul>
    
    <h2><strong>Competitive Differentiators</strong></h2>
    <p>What sets our approach apart:</p>
    <ul>
        {diff_html}
    </ul>
    
    <h2><strong>Project Timeline</strong></h2>
    {timeline_html}
    
    <hr>
    
    <h2><strong>Investment & ROI</strong></h2>
    <p><strong>Total Investment:</strong> ${budget:,.2f}</p>
    <p>Our data-driven approach ensures maximum return on investment through:</p>
    <ul>
        <li>Continuous performance optimization</li>
        <li>AI-powered audience targeting</li>
        <li>Real-time analytics and reporting</li>
        <li>Agile campaign management</li>
    </ul>
    
    <h2><strong>Next Steps</strong></h2>
    <ol>
        <li>Review this proposal and provide feedback</li>
        <li>Schedule a strategy session to discuss implementation</li>
        <li>Finalize project scope and timeline</li>
        <li>Begin Phase 1 execution</li>
    </ol>
    """


@router.put("/proposals/{proposal_id}/update-content")
async def update_proposal_content(
    proposal_id: int,
    content: dict,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Update proposal content from editor"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check if proposal exists
        cursor.execute("SELECT proposal_id FROM project_proposals WHERE proposal_id = %s", (proposal_id,))
        proposal = cursor.fetchone()
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Check if custom_strategy_html column exists
        has_custom_html = column_exists(cursor, 'project_proposals', 'custom_strategy_html')
        
        if has_custom_html:
            # Store in dedicated column
            cursor.execute("""
                UPDATE project_proposals 
                SET custom_strategy_html = %s, updated_at = NOW()
                WHERE proposal_id = %s
            """, (content.get('content'), proposal_id))
        else:
            # Store in custom_notes
            cursor.execute("""
                UPDATE project_proposals 
                SET custom_notes = %s, updated_at = NOW()
                WHERE proposal_id = %s
            """, (json.dumps({"edited_content": content.get('content')}), proposal_id))
        
        connection.commit()
        
        print(f"[UPDATE] Proposal {proposal_id} content saved")
        
        return {
            "success": True,
            "message": "Content saved successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error updating content: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.delete("/proposals/{proposal_id}")
async def delete_proposal(
    proposal_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Delete a proposal"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("DELETE FROM project_proposals WHERE proposal_id = %s", (proposal_id,))
        connection.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        return {
            "success": True,
            "message": "Proposal deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.post("/proposals/{proposal_id}/send-to-dashboard")
async def send_to_dashboard(
    proposal_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """Send proposal to client dashboard"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check if proposal exists
        cursor.execute("""
            SELECT p.*, u.full_name, u.email 
            FROM project_proposals p
            JOIN users u ON p.client_id = u.user_id
            WHERE p.proposal_id = %s
        """, (proposal_id,))
        proposal = cursor.fetchone()
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Update status to sent
        cursor.execute("""
            UPDATE project_proposals 
            SET status = %s, sent_at = NOW(), updated_at = NOW()
            WHERE proposal_id = %s
        """, ('sent', proposal_id))
        
        # Create notification for the client
        cursor.execute("""
            INSERT INTO notifications 
            (user_id, notification_type, title, message, is_read, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (
            proposal['client_id'],
            'proposal_received',
            'New Marketing Proposal',
            f'A new marketing proposal has been added to your dashboard. Please review and provide your feedback.',
            False
        ))
        
        connection.commit()
        
        print(f"[DASHBOARD] Proposal {proposal_id} sent to client {proposal['full_name']} (ID: {proposal['client_id']})")
        print(f"[NOTIFICATION] Created notification for client")
        
        return {
            "success": True,
            "message": "Proposal added to client dashboard!",
            "notification_created": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error sending to dashboard: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

            


@router.post("/proposals/{proposal_id}/send-email")
async def send_proposal_email(
    proposal_id: int,
    email_request: EmailRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Send proposal via email - non-blocking
    Uses background task to prevent timeout
    """
    connection = None
    cursor = None
    
    try:
        # Quick validation only
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Verify proposal exists and belongs to user
        cursor.execute("""
            SELECT pp.*, u.full_name as client_name, u.email as client_email
            FROM project_proposals pp
            LEFT JOIN users u ON pp.client_id = u.user_id
            WHERE pp.proposal_id = %s
        """, (proposal_id,))
        
        proposal = cursor.fetchone()
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Schedule email sending in background
        background_tasks.add_task(
            send_proposal_email_task,
            proposal_id,
            email_request.recipient_email,
            email_request.recipient_name,
            email_request.subject,
            email_request.message,
            email_request.include_pdf,
            current_user['user_id'],
            proposal
        )
        
        # Log email activity immediately
        cursor.execute("""
            INSERT INTO email_logs 
            (proposal_id, recipient_email, status, sent_by, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (proposal_id, email_request.recipient_email, 'queued', current_user['user_id']))
        
        connection.commit()
        email_log_id = cursor.lastrowid
        
        return {
            "success": True,
            "message": "Proposal email is being sent in the background",
            "email_log_id": email_log_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error queuing email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue email: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



async def send_proposal_email_task(
    proposal_id: int,
    recipient_email: str,
    recipient_name: str,
    subject: Optional[str],
    custom_message: Optional[str],
    include_pdf: bool,
    sender_id: int,
    proposal: dict
):
    """
    Background task for sending proposal email with SMTP
    Automatically generates share link if needed
    """
    connection = None
    cursor = None
    
    try:
        print(f"\n{'='*60}")
        print(f"📧 SENDING PROPOSAL EMAIL")
        print(f"{'='*60}")
        print(f"Proposal ID: {proposal_id}")
        print(f"To: {recipient_email}")
        print(f"Include PDF: {include_pdf}")
        
        # First, generate or get existing share link
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check for existing valid share link
        cursor.execute("""
            SELECT share_token, expires_at 
            FROM proposal_share_links 
            WHERE proposal_id = %s 
            AND expires_at > NOW()
            ORDER BY created_at DESC 
            LIMIT 1
        """, (proposal_id,))
        
        share_link_data = cursor.fetchone()
        
        if share_link_data:
            share_token = share_link_data['share_token']
            print(f"✓ Using existing share token")
        else:
            # Generate new share token
            share_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=30)
            
            # Check table structure
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'proposal_share_links'
            """)
            columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
            
            has_is_active = 'is_active' in columns
            has_view_count = 'view_count' in columns
            
            # Insert new share link
            if has_is_active and has_view_count:
                cursor.execute("""
                    INSERT INTO proposal_share_links 
                    (proposal_id, share_token, created_by, expires_at, is_active, view_count)
                    VALUES (%s, %s, %s, %s, TRUE, 0)
                """, (proposal_id, share_token, sender_id, expires_at))
            elif has_is_active:
                cursor.execute("""
                    INSERT INTO proposal_share_links 
                    (proposal_id, share_token, created_by, expires_at, is_active)
                    VALUES (%s, %s, %s, %s, TRUE)
                """, (proposal_id, share_token, sender_id, expires_at))
            else:
                cursor.execute("""
                    INSERT INTO proposal_share_links 
                    (proposal_id, share_token, created_by, expires_at)
                    VALUES (%s, %s, %s, %s)
                """, (proposal_id, share_token, sender_id, expires_at))
            
            connection.commit()
            print(f"✓ Generated new share token")
        
        # Get SMTP configuration
        smtp_host = settings.SMTP_HOST
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USERNAME
        smtp_password = settings.SMTP_PASSWORD
        from_email = settings.SMTP_FROM_EMAIL
        from_name = settings.FROM_NAME
        
        # Validate SMTP configuration
        if not all([smtp_host, smtp_user, smtp_password]):
            raise Exception("SMTP configuration incomplete. Please configure email settings.")
        
        print(f"✓ SMTP Server: {smtp_host}:{smtp_port}")
        
        # Generate email subject
        if not subject:
            company_name = proposal.get('company_name', 'Your Company')
            subject = f"Marketing Proposal for {company_name} - PanvelIQ"
        
        # Generate HTML email content with share token
        html_content = generate_proposal_email_html(
            recipient_name=recipient_name,
            company_name=proposal.get('company_name', 'Your Company'),
            proposal_id=proposal_id,
            share_token=share_token,
            custom_message=custom_message,
            budget=proposal.get('budget', 0)
        )
        
        # Generate plain text version with share token
        text_content = generate_proposal_email_text(
            recipient_name=recipient_name,
            company_name=proposal.get('company_name', 'Your Company'),
            proposal_id=proposal_id,
            share_token=share_token
        )
        
        print(f"✓ Email content generated with share link")
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = recipient_email
        msg['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        # Attach text and HTML versions
        part_text = MIMEText(text_content, 'plain', 'utf-8')
        part_html = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part_text)
        msg.attach(part_html)
        
        # Attach PDF if requested
        if include_pdf:
            try:
                print(f"📄 Generating PDF...")
                
                # Generate PDF (with timeout)
                pdf_data = generate_proposal_pdf_bytes(proposal_id)
                
                if pdf_data:
                    part_pdf = MIMEBase('application', 'pdf')
                    part_pdf.set_payload(pdf_data)
                    encoders.encode_base64(part_pdf)
                    part_pdf.add_header(
                        'Content-Disposition',
                        f'attachment; filename="proposal_{proposal_id}.pdf"'
                    )
                    msg.attach(part_pdf)
                    print(f"✓ PDF attached ({len(pdf_data)} bytes)")
                else:
                    print(f"⚠ PDF generation failed - sending email without PDF")
                    
            except Exception as pdf_error:
                print(f"⚠ PDF attachment error: {str(pdf_error)}")
                # Continue sending email without PDF
        
        # Send email via SMTP
        print(f" Connecting to SMTP server...")
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to {recipient_email}")
        print(f"{'='*60}\n")
        
        # Update status to 'sent'
        cursor.execute("""
            UPDATE email_logs 
            SET status = 'sent', sent_at = NOW()
            WHERE proposal_id = %s 
            AND recipient_email = %s 
            AND status = 'queued'
            ORDER BY created_at DESC 
            LIMIT 1
        """, (proposal_id, recipient_email))
        
        connection.commit()
        
    except smtplib.SMTPAuthenticationError as auth_error:
        error_msg = f"SMTP Authentication Failed: {str(auth_error)}"
        print(f"❌ {error_msg}")
        log_email_failure(proposal_id, recipient_email, error_msg)
        
    except smtplib.SMTPException as smtp_error:
        error_msg = f"SMTP Error: {str(smtp_error)}"
        print(f"❌ {error_msg}")
        log_email_failure(proposal_id, recipient_email, error_msg)
        
    except Exception as e:
        error_msg = f"Email sending failed: {str(e)}"
        print(f"❌ {error_msg}")
        log_email_failure(proposal_id, recipient_email, error_msg)
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def generate_proposal_email_html(
    recipient_name: str,
    company_name: str,
    proposal_id: int,
    share_token: str,
    custom_message: Optional[str],
    budget: float
) -> str:
    """
    Generate professional HTML email template for proposal
    Uses share token for secure access
    """
    
    # Custom message or default
    message_html = f"<p>{custom_message}</p>" if custom_message else f"""
    <p>We've prepared a comprehensive digital marketing proposal tailored specifically for {company_name}.</p>
    <p>Our AI-powered platform has analyzed your business needs and created a customized strategy to help you achieve your marketing goals.</p>
    """
    
    # Build the proposal URL with share token
    proposal_url = f"{settings.FRONTEND_URL}/proposals/view/{share_token}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PanvelIQ - Marketing Proposal</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #f5f5f5; padding: 40px 0;">
            <tr>
                <td align="center">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" style="background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        
                        <!-- Header with Gradient -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #9926F3 0%, #1DD8FC 100%); padding: 40px 30px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">PanvelIQ</h1>
                                <p style="margin: 10px 0 0 0; color: #ffffff; font-size: 14px; opacity: 0.9;">AI-Powered Digital Marketing Intelligence</p>
                            </td>
                        </tr>
                        
                        <!-- Main Content -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <h2 style="margin: 0 0 20px 0; color: #1a1a1a; font-size: 24px; font-weight: 600;">
                                    Dear {recipient_name},
                                </h2>
                                
                                {message_html}
                                
                                <!-- Proposal Highlights Box -->
                                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 30px 0; background: linear-gradient(135deg, rgba(153,38,243,0.05) 0%, rgba(29,216,252,0.05) 100%); border-radius: 8px; border-left: 4px solid #9926F3;">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <h3 style="margin: 0 0 15px 0; color: #9926F3; font-size: 16px; font-weight: 600;">Proposal Highlights</h3>
                                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                                <tr>
                                                    <td style="padding: 8px 0; color: #555; font-size: 14px;">
                                                        <strong>Company:</strong> {company_name}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 8px 0; color: #555; font-size: 14px;">
                                                        <strong>Estimated Budget:</strong> ₹{budget:,.0f}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 8px 0; color: #555; font-size: 14px;">
                                                        <strong>Proposal ID:</strong> #{proposal_id}
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- CTA Button -->
                                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 30px 0;">
                                    <tr>
                                        <td align="center">
                                            <a href="{proposal_url}" style="display: inline-block; background: linear-gradient(135deg, #9926F3 0%, #1DD8FC 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 15px rgba(153,38,243,0.3);">
                                                View Full Proposal
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 30px 0 0 0; color: #666; font-size: 14px; line-height: 1.6;">
                                    This proposal includes AI-generated strategies, competitive analysis, and detailed campaign recommendations tailored to your specific business needs.
                                </p>
                                
                                <p style="margin: 20px 0 0 0; color: #666; font-size: 14px;">
                                    Best regards,<br>
                                    <strong>The PanvelIQ Team</strong>
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e0e0e0;">
                                <p style="margin: 0 0 10px 0; color: #999; font-size: 12px;">
                                    This email was sent by PanvelIQ
                                </p>
                                <p style="margin: 0; color: #999; font-size: 12px;">
                                    If you have any questions, please contact us at 
                                    <a href="mailto:hello@panvel-iq.calim.ai" style="color: #9926F3; text-decoration: none;">hello@panvel-iq.calim.ai</a>
                                </p>
                            </td>
                        </tr>
                        
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    return html


def generate_proposal_email_text(
    recipient_name: str,
    company_name: str,
    proposal_id: int,
    share_token: str
) -> str:
    """
    Generate plain text version of email
    Uses share token for secure access
    """
    
    proposal_url = f"{settings.FRONTEND_URL}/proposals/view/{share_token}"
    
    text = f"""
PanvelIQ - Marketing Proposal

Dear {recipient_name},

We've prepared a comprehensive digital marketing proposal tailored specifically for {company_name}.

Proposal ID: #{proposal_id}
Company: {company_name}

View your full proposal at: {proposal_url}

This proposal includes AI-generated strategies, competitive analysis, and detailed campaign recommendations.

Best regards,
The PanvelIQ Team

---
If you have any questions, contact us at hello@panvel-iq.calim.ai
    """
    
    return text.strip()

    


def generate_proposal_pdf_bytes(proposal_id: int) -> Optional[bytes]:
    """
    Generate PDF and return as bytes
    
    Returns:
        bytes: PDF data or None if generation fails
    """
    try:
        # Call the PDF generation endpoint internally
        token = create_internal_access_token()  # Create internal token
        
        response = requests.get(
            f"{settings.BASE_URL}/api/v1/project-planner/proposals/{proposal_id}/export/pdf",
            headers={'Authorization': f'Bearer {token}'},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.content
        else:
            print(f"⚠ PDF generation returned status {response.status_code}")
            return None
            
    except requests.Timeout:
        print(f"⚠ PDF generation timed out")
        return None
    except Exception as e:
        print(f"⚠ PDF generation error: {str(e)}")
        return None


def log_email_failure(proposal_id: int, recipient_email: str, error_message: str):
    """Log failed email attempt to database"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE email_logs 
            SET status = 'failed', 
                error_message = %s,
                updated_at = NOW()
            WHERE proposal_id = %s 
            AND recipient_email = %s 
            AND status = 'queued'
            ORDER BY created_at DESC 
            LIMIT 1
        """, (error_message, proposal_id, recipient_email))
        
        connection.commit()
        cursor.close()
        connection.close()
        
    except Exception as log_error:
        print(f"Failed to log email error: {str(log_error)}")

