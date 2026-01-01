"""
AI Service for Strategy Generation
FIXED for OpenAI v1.0.0+

COPY THIS ENTIRE FILE to: app/services/ai_service.py
"""

from openai import OpenAI
import json
from typing import Dict, Any
from app.core.config import settings


class AIService:
    """AI Service for generating marketing strategies and proposals"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        # New OpenAI v1.0+ client
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4"
    
    async def generate_strategy(self, prompt: str) -> Dict[str, Any]:
        """
        Generate comprehensive marketing strategy using AI
        
        Args:
            prompt: Detailed prompt with client information
            
        Returns:
            Dictionary containing strategy recommendations
        """
        try:
            print("   → Calling OpenAI API for strategy...")
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert digital marketing strategist. 
                        Generate comprehensive, actionable marketing strategies in JSON format.
                        Be specific, data-driven, and focus on ROI."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            print("   → OpenAI response received")
            
            # Try to parse as JSON
            try:
                strategy = json.loads(content)
            except json.JSONDecodeError:
                print("   → JSON parse failed, using fallback")
                strategy = self._get_fallback_strategy()
            
            return strategy
        
        except Exception as e:
            print(f"   ⚠️  AI Strategy Generation Error: {e}")
            return self._get_fallback_strategy()
    
    async def generate_differentiators(self, prompt: str) -> Dict[str, Any]:
        """
        Generate competitive differentiators
        
        Args:
            prompt: Prompt with business context
            
        Returns:
            Dictionary of differentiators
        """
        try:
            print("   → Calling OpenAI API for differentiators...")
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a marketing consultant highlighting unique value propositions.
                        Generate compelling competitive differentiators in JSON format."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.6,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            print("   → OpenAI response received")
            
            try:
                differentiators = json.loads(content)
            except json.JSONDecodeError:
                print("   → JSON parse failed, using fallback")
                differentiators = self._get_fallback_differentiators()
            
            return differentiators
        
        except Exception as e:
            print(f"   ⚠️  AI Differentiators Generation Error: {e}")
            return self._get_fallback_differentiators()
    
    async def generate_timeline(self, prompt: str) -> Dict[str, Any]:
        """
        Generate project timeline
        
        Args:
            prompt: Prompt with strategy and budget info
            
        Returns:
            Dictionary containing timeline phases
        """
        try:
            print("   → Calling OpenAI API for timeline...")
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a project manager creating realistic marketing timelines.
                        Generate detailed phase-wise timelines in JSON format with milestones and deliverables."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            print("   → OpenAI response received")
            
            try:
                timeline = json.loads(content)
            except json.JSONDecodeError:
                print("   → JSON parse failed, using fallback")
                timeline = self._get_fallback_timeline()
            
            return timeline
        
        except Exception as e:
            print(f"   ⚠️  AI Timeline Generation Error: {e}")
            return self._get_fallback_timeline()
    
    def _get_fallback_strategy(self) -> Dict[str, Any]:
        """Fallback strategy if AI fails"""
        return {
            "campaigns": {
                "paid_advertising": {
                    "platforms": ["Meta (Facebook & Instagram)", "Google Ads"],
                    "formats": ["Search Ads", "Display Ads", "Video Ads", "Carousel Ads"],
                    "budget_allocation": "60% of total budget",
                    "expected_roi": "300-400%"
                },
                "email_marketing": {
                    "strategy": "Segmented campaigns with automation",
                    "frequency": "2-3 emails per week",
                    "tools": ["Mailchimp", "SendGrid"],
                    "expected_open_rate": "25-35%"
                },
                "seo": {
                    "focus": "On-page optimization and content strategy",
                    "keyword_targets": "50-100 keywords",
                    "content_plan": "Weekly blog posts + technical SEO",
                    "timeline": "3-6 months for results"
                },
                "social_media": {
                    "platforms": ["Instagram", "Facebook", "LinkedIn"],
                    "posting_frequency": "Daily",
                    "content_types": ["Stories", "Reels", "Posts", "Live"],
                    "engagement_strategy": "Community management + influencer partnerships"
                }
            },
            "automation_tools": [
                "HubSpot for CRM and email automation",
                "Hootsuite for social media scheduling",
                "Google Analytics 4 for tracking",
                "Meta Business Suite for ad management",
                "Zapier for workflow automation"
            ],
            "kpis": {
                "month_1": {
                    "website_traffic": "500-1000 visitors",
                    "leads": "50-100",
                    "conversions": "10-20"
                },
                "month_3": {
                    "website_traffic": "2000-3000 visitors",
                    "leads": "200-300",
                    "conversions": "50-75"
                },
                "month_6": {
                    "website_traffic": "5000+ visitors",
                    "leads": "500+",
                    "conversions": "150+"
                }
            }
        }
    
    def _get_fallback_differentiators(self) -> Dict[str, Any]:
        """Fallback differentiators if AI fails"""
        return {
            "differentiators": [
                {
                    "title": "AI-Powered Automation",
                    "description": "Deploy campaigns 70% faster using our proprietary AI automation tools, reducing manual work and accelerating time-to-market.",
                    "impact": "Faster deployment, reduced costs"
                },
                {
                    "title": "Hyper-Personalized Targeting",
                    "description": "Our AI analyzes thousands of data points to create highly targeted audience segments, improving ad relevance and conversion rates by 2-3x.",
                    "impact": "Higher conversion rates, better ROAS"
                },
                {
                    "title": "Integrated Online-Offline Strategy",
                    "description": "We bridge digital and physical touchpoints, creating seamless customer journeys that drive both online conversions and foot traffic.",
                    "impact": "Omnichannel presence, increased revenue"
                },
                {
                    "title": "Cost-Efficient Media Optimization",
                    "description": "Our AI continuously optimizes ad spend across platforms, ensuring you get maximum results for minimum investment.",
                    "impact": "20-30% cost reduction, improved ROI"
                },
                {
                    "title": "Predictive Performance Analytics",
                    "description": "Advanced machine learning models forecast campaign performance, allowing proactive adjustments before budget is wasted.",
                    "impact": "Data-driven decisions, reduced risk"
                }
            ]
        }
    
    def _get_fallback_timeline(self) -> Dict[str, Any]:
        """Fallback timeline if AI fails"""
        return {
            "phases": [
                {
                    "phase": "Discovery & Setup",
                    "duration": "Week 1-2",
                    "milestones": [
                        "Complete brand audit",
                        "Finalize target audience personas",
                        "Set up tracking and analytics",
                        "Establish KPI baselines"
                    ],
                    "deliverables": [
                        "Marketing strategy document",
                        "Audience personas",
                        "Analytics dashboard setup"
                    ]
                },
                {
                    "phase": "Campaign Development",
                    "duration": "Week 3-4",
                    "milestones": [
                        "Create ad campaigns",
                        "Develop content calendar",
                        "Design creative assets",
                        "Set up automation workflows"
                    ],
                    "deliverables": [
                        "Ad creatives (20-30 variations)",
                        "Content calendar (3 months)",
                        "Email templates",
                        "Landing pages"
                    ]
                },
                {
                    "phase": "Launch & Optimization",
                    "duration": "Week 5-8",
                    "milestones": [
                        "Launch paid campaigns",
                        "Begin organic content posting",
                        "Start email sequences",
                        "A/B test key elements"
                    ],
                    "deliverables": [
                        "Live campaigns across all platforms",
                        "Weekly performance reports",
                        "Optimization recommendations"
                    ]
                },
                {
                    "phase": "Scale & Growth",
                    "duration": "Month 3-6",
                    "milestones": [
                        "Scale winning campaigns",
                        "Expand to new platforms",
                        "Implement advanced automation",
                        "Launch retargeting campaigns"
                    ],
                    "deliverables": [
                        "Monthly strategy reviews",
                        "ROI reports",
                        "Growth projections",
                        "Quarterly business reviews"
                    ]
                }
            ],
            "expected_results": {
                "month_1": "Foundation established, initial traction",
                "month_3": "Consistent lead flow, positive ROI",
                "month_6": "Scalable growth, 3-4x ROI achieved"
            }
        }


    async def generate_content(self, prompt: str, content_type: str = "general") -> Any:
        """Generate AI content - handles value_props, competitive, roi, and general content"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert digital marketing strategist. Always respond with valid JSON when requested."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean JSON markers
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            content = content.strip()
            
            # Parse JSON for structured types
            if content_type in ["value_props", "competitive", "roi"]:
                try:
                    parsed = json.loads(content)
                    return parsed
                except json.JSONDecodeError as e:
                    print(f"JSON parse error for {content_type}: {e}")
                    # Return default structures
                    if content_type == "value_props":
                        return []
                    elif content_type == "competitive":
                        return {
                            "opportunities": ["Market analysis in progress"],
                            "threats": ["Competitive analysis in progress"],
                            "key_insights": ["Analysis pending"],
                            "opportunity_score": 50
                        }
                    elif content_type == "roi":
                        return {
                            "expected_leads": {"month_1": 0, "month_3": 0, "month_6": 0, "month_12": 0},
                            "cost_per_lead": {"average": 0, "best_case": 0, "worst_case": 0},
                            "conversion_rate": 0,
                            "estimated_customers": 0,
                            "estimated_revenue": 0,
                            "roi_percentage": 0,
                            "timeframe_to_roi": 0
                        }
            
            return content
        
        except Exception as e:
            print(f"Content generation error ({content_type}): {e}")
            # Return safe defaults
            if content_type == "value_props":
                return [
                    {
                        "title": "🚀 AI-Powered Marketing Automation",
                        "description": "Leverage cutting-edge AI to automate campaigns and optimize performance in real-time.",
                        "competitive_advantage": "Traditional agencies use manual processes. We deploy AI for 3x faster results.",
                        "impact": "Reduce costs by 40% while improving campaign performance."
                    }
                ]
            elif content_type == "competitive":
                return {
                    "opportunities": [
                        "Competitors focus on large enterprises - opportunity in SMB market",
                        "Limited AI adoption - we can differentiate with automation",
                        "Underserved niche markets in specific industries"
                    ],
                    "threats": [
                        "Established competitors have larger budgets",
                        "Brand recognition advantages",
                        "Long-term client relationships create switching costs"
                    ],
                    "key_insights": [
                        "Market is shifting towards AI-driven solutions",
                        "Customer expectations for real-time results increasing",
                        "Integration across channels is becoming critical"
                    ],
                    "opportunity_score": 65
                }
            elif content_type == "roi":
                budget = 10000  # default
                return {
                    "expected_leads": {
                        "month_1": int(budget * 0.05),
                        "month_3": int(budget * 0.15),
                        "month_6": int(budget * 0.30),
                        "month_12": int(budget * 0.60)
                    },
                    "cost_per_lead": {
                        "average": 75,
                        "best_case": 50,
                        "worst_case": 120
                    },
                    "conversion_rate": 5,
                    "estimated_customers": int(budget * 0.60 * 0.05),
                    "estimated_revenue": int(budget * 2),
                    "roi_percentage": 200,
                    "timeframe_to_roi": 6
                }

            elif content_type == "achievability":
                return {
                        "achievability_score": 75,
                        "status": "Realistic",
                        "assessment": "The budget and goals align well with industry standards. Timeline expectations are achievable with proper resource allocation.",
                        "recommendations": [
                            "Focus on high-impact channels first",
                            "Set incremental milestones to track progress",
                            "Allocate 10-15% buffer for optimization"
                        ],
                        "risk_factors": [
                            "Market competition may require higher ad spend",
                            "Content production timelines might need adjustment"
                        ]
                }                   
            
            return "Content generation unavailable"