"""
Onboarding API Endpoints - FIXED VERSION WITH ERROR HANDLING
Replace your current app/api/v1/endpoints/onboarding.py with this
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date, timedelta
import pymysql
from pymysql import Error
import json
import traceback

from app.core.config import settings
from app.core.security import get_current_user
from app.core.security import get_db_connection


router = APIRouter()


# ============================================
# PYDANTIC MODELS
# ============================================

class Package(BaseModel):
    package_id: Optional[int] = None
    package_name: str
    package_tier: str
    description: str
    price: float
    billing_cycle: str
    features: dict
    is_active: bool = True

class PackageSelect(BaseModel):
    package_id: int

class OnboardingSession(BaseModel):
    onboarding_id: Optional[int] = None
    user_id: int
    selected_package_id: Optional[int] = None
    verification_data: Optional[dict] = None
    verification_status: str = 'pending'
    discussion_notes: Optional[str] = None

class VerificationUpdate(BaseModel):
    verification_status: str
    discussion_notes: Optional[str] = None

class SubscriptionCreate(BaseModel):
    client_id: int
    package_id: int
    start_date: date
    end_date: date

# ============================================
# PACKAGE ENDPOINTS
# ============================================

@router.get("/packages", summary="Get all active packages")
async def get_packages():
    """
    Retrieve all active packages for selection
    """
    connection = None
    cursor = None
    
    try:
        print("🔍 Attempting to fetch packages...")
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # First check if table exists
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name = 'packages'
        """, (settings.DB_NAME,))
        
        table_check = cursor.fetchone()
        if table_check['count'] == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Packages table does not exist. Please run database migrations."
            )
        
        # Fetch packages
        query = """
            SELECT 
                package_id, 
                package_name, 
                package_tier, 
                description, 
                price, 
                billing_cycle, 
                features, 
                is_active
            FROM packages
            WHERE is_active = TRUE
            ORDER BY 
                CASE package_tier
                    WHEN 'basic' THEN 1
                    WHEN 'professional' THEN 2
                    WHEN 'enterprise' THEN 3
                END
        """
        
        cursor.execute(query)
        packages = cursor.fetchall()
        
        print(f" Found {len(packages)} packages")
        
        if len(packages) == 0:
            return {
                "status": "success",
                "packages": [],
                "message": "No packages found. Please run the seed data script."
            }
        
        # Parse JSON features field
        for package in packages:
            if package.get('features'):
                try:
                    if isinstance(package['features'], str):
                        package['features'] = json.loads(package['features'])
                except json.JSONDecodeError as e:
                    print(f"⚠️ Warning: Invalid JSON in features for package {package['package_id']}")
                    package['features'] = {}
        
        return {
            "status": "success",
            "packages": packages,
            "count": len(packages)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching packages: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve packages: {str(e)}"
        )
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@router.get("/packages/{package_id}", summary="Get specific package details")
async def get_package_by_id(package_id: int):
    """
    Retrieve specific package details
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT package_id, package_name, package_tier, description, 
                   price, billing_cycle, features, is_active
            FROM packages
            WHERE package_id = %s AND is_active = TRUE
        """
        
        cursor.execute(query, (package_id,))
        package = cursor.fetchone()
        
        if not package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        # Parse JSON features
        if package.get('features'):
            try:
                if isinstance(package['features'], str):
                    package['features'] = json.loads(package['features'])
            except json.JSONDecodeError:
                package['features'] = {}
        
        return {
            "status": "success",
            "package": package
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve package: {str(e)}"
        )
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# ============================================
# ONBOARDING SESSION ENDPOINTS
# ============================================

@router.post("/select-package", status_code=status.HTTP_201_CREATED, summary="Select package during onboarding")
async def select_package(
    package_select: PackageSelect,
    current_user: dict = Depends(get_current_user)
):
    """
    Client selects a package during onboarding
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Verify package exists
        cursor.execute(
            "SELECT package_id FROM packages WHERE package_id = %s AND is_active = TRUE", 
            (package_select.package_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        # Check if onboarding session exists
        cursor.execute(
            "SELECT onboarding_id FROM onboarding_sessions WHERE user_id = %s",
            (current_user['user_id'],)
        )
        existing_session = cursor.fetchone()
        
        if existing_session:
            # Update existing
            cursor.execute(
                "UPDATE onboarding_sessions SET selected_package_id = %s WHERE user_id = %s",
                (package_select.package_id, current_user['user_id'])
            )
            onboarding_id = existing_session['onboarding_id']
        else:
            # Create new
            cursor.execute(
                "INSERT INTO onboarding_sessions (user_id, selected_package_id, verification_status) VALUES (%s, %s, 'pending')",
                (current_user['user_id'], package_select.package_id)
            )
            onboarding_id = cursor.lastrowid
        
        connection.commit()
        
        return {
            "status": "success",
            "message": "Package selected successfully",
            "onboarding_id": onboarding_id,
            "package_id": package_select.package_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to select package: {str(e)}"
        )
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@router.get("/my-onboarding", summary="Get current user's onboarding status")
async def get_my_onboarding(current_user: dict = Depends(get_current_user)):
    """
    Retrieve current user's onboarding session details
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT 
                os.onboarding_id,
                os.user_id,
                os.selected_package_id,
                os.verification_data,
                os.verification_status,
                os.discussion_notes,
                os.verified_by,
                os.verified_at,
                os.created_at,
                p.package_name,
                p.package_tier,
                p.price,
                p.billing_cycle,
                u_verifier.full_name as verified_by_name
            FROM onboarding_sessions os
            LEFT JOIN packages p ON os.selected_package_id = p.package_id
            LEFT JOIN users u_verifier ON os.verified_by = u_verifier.user_id
            WHERE os.user_id = %s
        """
        
        cursor.execute(query, (current_user['user_id'],))
        session = cursor.fetchone()
        
        if not session:
            return {
                "status": "success",
                "onboarding_session": None,
                "message": "No onboarding session found"
            }
        
        # Parse JSON
        if session.get('verification_data'):
            try:
                if isinstance(session['verification_data'], str):
                    session['verification_data'] = json.loads(session['verification_data'])
            except:
                session['verification_data'] = {}
        
        return {
            "status": "success",
            "onboarding_session": session
        }
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve onboarding session: {str(e)}"
        )
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@router.post("/submit-verification", summary="Submit verification data")
async def submit_verification_data(
    verification_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Client submits business verification data - DIAGNOSTIC VERSION
    """
    connection = None
    cursor = None
    
    print("\n" + "="*80)
    print("🔍 VERIFICATION SUBMISSION STARTED")
    print("="*80)
    
    try:
        # Log incoming data
        print(f"📥 Current User: {current_user}")
        print(f"📥 Verification Data: {json.dumps(verification_data, indent=2)}")
        
        # Get database connection
        print("\n🔌 Connecting to database...")
        connection = get_db_connection()
        cursor = connection.cursor()
        print("✅ Database connected successfully")
        
        # Check if user exists
        print(f"\n👤 Checking if user {current_user['user_id']} exists...")
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (current_user['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ ERROR: User {current_user['user_id']} not found in database!")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in database"
            )
        
        print(f"✅ User found: {user['email']} (Role: {user['role']}, Status: {user['status']})")
        
        # Check if onboarding session exists
        print(f"\n📋 Checking onboarding session for user {current_user['user_id']}...")
        cursor.execute(
            "SELECT * FROM onboarding_sessions WHERE user_id = %s",
            (current_user['user_id'],)
        )
        onboarding = cursor.fetchone()
        
        if not onboarding:
            print("❌ ERROR: No onboarding session found!")
            print("💡 User must select a package first")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Onboarding session not found. Please select a package first."
            )
        
        print(f"✅ Onboarding session found (ID: {onboarding['onboarding_id']})")
        print(f"   Package ID: {onboarding['selected_package_id']}")
        print(f"   Status: {onboarding['verification_status']}")
        
        # Convert to JSON for onboarding_sessions
        verification_json = json.dumps(verification_data)
        print(f"\n📝 Verification JSON length: {len(verification_json)} characters")
        
        # STEP 1: Update onboarding_sessions
        print("\n🔄 STEP 1: Updating onboarding_sessions table...")
        cursor.execute(
            """UPDATE onboarding_sessions 
               SET verification_data = %s, 
                   verification_status = 'pending' 
               WHERE user_id = %s""",
            (verification_json, current_user['user_id'])
        )
        rows_updated = cursor.rowcount
        print(f"✅ Onboarding sessions updated: {rows_updated} row(s)")
        
        # STEP 2: Extract client profile data
        print("\n📊 STEP 2: Extracting client profile data...")
        business_name = verification_data.get('business_name')
        business_type = verification_data.get('business_type')
        website_url = verification_data.get('website_url')
        monthly_budget = verification_data.get('monthly_budget')
        
        print(f"   business_name: {business_name}")
        print(f"   business_type: {business_type}")
        print(f"   website_url: {website_url}")
        print(f"   monthly_budget: {monthly_budget}")
        
        # Convert budget
        current_budget = None
        if monthly_budget:
            try:
                current_budget = float(monthly_budget)
                print(f"   ✅ Budget converted: {current_budget}")
            except (ValueError, TypeError) as e:
                print(f"   ⚠️ Budget conversion failed: {e}")
                current_budget = None
        
        # STEP 3: Check if profile exists
        print("\n🔍 STEP 3: Checking if client_profiles entry exists...")
        cursor.execute(
            "SELECT * FROM client_profiles WHERE client_id = %s",
            (current_user['user_id'],)
        )
        existing_profile = cursor.fetchone()
        
        if existing_profile:
            print(f"✅ Profile found (ID: {existing_profile['profile_id']})")
            print("🔄 UPDATING existing profile...")
            
            cursor.execute("""
                UPDATE client_profiles 
                SET business_name = %s,
                    business_type = %s,
                    website_url = %s,
                    current_budget = %s,
                    updated_at = NOW()
                WHERE client_id = %s
            """, (
                business_name,
                business_type,
                website_url,
                current_budget,
                current_user['user_id']
            ))
            
            rows_updated = cursor.rowcount
            print(f"✅ Profile UPDATED: {rows_updated} row(s)")
            
        else:
            print("❌ No profile found")
            print("➕ CREATING new profile...")
            
            cursor.execute("""
                INSERT INTO client_profiles 
                (client_id, business_name, business_type, website_url, current_budget)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                current_user['user_id'],
                business_name,
                business_type,
                website_url,
                current_budget
            ))
            
            new_profile_id = cursor.lastrowid
            print(f"✅ Profile CREATED (ID: {new_profile_id})")
        
        # COMMIT TRANSACTION
        print("\n💾 COMMITTING transaction to database...")
        connection.commit()
        print("✅ TRANSACTION COMMITTED SUCCESSFULLY!")
        
        # Verify the data was saved
        print("\n🔍 VERIFICATION: Checking if data was actually saved...")
        
        cursor.execute(
            "SELECT verification_data, verification_status FROM onboarding_sessions WHERE user_id = %s",
            (current_user['user_id'],)
        )
        saved_onboarding = cursor.fetchone()
        print(f"   Onboarding status: {saved_onboarding['verification_status']}")
        print(f"   Verification data saved: {len(str(saved_onboarding['verification_data']))} chars")
        
        cursor.execute(
            "SELECT * FROM client_profiles WHERE client_id = %s",
            (current_user['user_id'],)
        )
        saved_profile = cursor.fetchone()
        if saved_profile:
            print(f"   ✅ Profile saved - Business: {saved_profile['business_name']}")
        else:
            print("   ❌ WARNING: Profile NOT found in database after commit!")
        
        print("\n" + "="*80)
        print("✅ VERIFICATION SUBMISSION COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
        return {
            "status": "success",
            "message": "Verification data submitted successfully. Awaiting admin review.",
            "debug": {
                "user_id": current_user['user_id'],
                "onboarding_updated": True,
                "profile_created_or_updated": True
            }
        }
    
    except HTTPException:
        print("\n❌ HTTP EXCEPTION RAISED")
        if connection:
            print("🔙 Rolling back transaction...")
            connection.rollback()
        raise
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        if connection:
            print("🔙 Rolling back transaction...")
            connection.rollback()
        
        import traceback
        print("\n📋 FULL TRACEBACK:")
        print(traceback.format_exc())
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit verification data: {str(e)}"
        )
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        print("🔌 Database connection closed\n")



@router.get("/debug/check-tables", summary="DEBUG: Check database tables")
async def debug_check_tables():
    """
    Diagnostic endpoint to verify tables exist
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        results = {}
        
        # Check onboarding_sessions
        cursor.execute("SELECT COUNT(*) as count FROM onboarding_sessions")
        results['onboarding_sessions_count'] = cursor.fetchone()['count']
        
        # Check client_profiles
        cursor.execute("SELECT COUNT(*) as count FROM client_profiles")
        results['client_profiles_count'] = cursor.fetchone()['count']
        
        # Check users
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'client'")
        results['client_users_count'] = cursor.fetchone()['count']
        
        # Check packages
        cursor.execute("SELECT * FROM packages")
        results['packages'] = cursor.fetchall()
        
        return {
            "status": "success",
            "results": results
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

            
# ============================================
# ADMIN ENDPOINTS
# ============================================

@router.get("/pending-verifications", summary="Get pending verifications (Admin)")
async def get_pending_verifications(current_user: dict = Depends(get_current_user)):
    """
    Admin retrieves pending onboarding sessions
    """
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access pending verifications"
        )
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT 
                os.onboarding_id,
                os.user_id,
                os.selected_package_id,
                os.verification_data,
                os.verification_status,
                os.discussion_notes,
                os.created_at,
                u.full_name,
                u.email,
                u.phone,
                p.package_name,
                p.package_tier,
                p.price,
                p.billing_cycle
            FROM onboarding_sessions os
            INNER JOIN users u ON os.user_id = u.user_id
            LEFT JOIN packages p ON os.selected_package_id = p.package_id
            WHERE os.verification_status = 'pending'
            ORDER BY os.created_at ASC
        """
        
        cursor.execute(query)
        sessions = cursor.fetchall()
        
        # Parse JSON
        for session in sessions:
            if session.get('verification_data'):
                try:
                    if isinstance(session['verification_data'], str):
                        session['verification_data'] = json.loads(session['verification_data'])
                except:
                    session['verification_data'] = {}
        
        return {
            "status": "success",
            "pending_verifications": sessions,
            "count": len(sessions)
        }
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pending verifications: {str(e)}"
        )
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.put("/verify/{onboarding_id}", summary="Verify onboarding (Admin)")
async def verify_onboarding(
    onboarding_id: int,
    verification: VerificationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Admin verifies or rejects onboarding
    - Verified: Creates subscription, activates user (status = 'active')
    - Rejected: Sets user status to 'inactive'
    """
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can verify onboarding"
        )
    
    if verification.verification_status not in ['verified', 'rejected']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'verified' or 'rejected'"
        )
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get onboarding session
        cursor.execute(
            "SELECT * FROM onboarding_sessions WHERE onboarding_id = %s",
            (onboarding_id,)
        )
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Onboarding session not found"
            )
        
        # Update onboarding session
        cursor.execute(
            """UPDATE onboarding_sessions 
               SET verification_status = %s, 
                   discussion_notes = %s, 
                   verified_by = %s, 
                   verified_at = NOW()
               WHERE onboarding_id = %s""",
            (verification.verification_status, verification.discussion_notes, 
             current_user['user_id'], onboarding_id)
        )
        
        # Handle approval vs rejection
        if verification.verification_status == 'verified':
            # APPROVAL: Create subscription and activate user
            print(f"\n✅ APPROVING onboarding for user {session['user_id']}")
            
            # Get package billing cycle
            cursor.execute(
                "SELECT billing_cycle FROM packages WHERE package_id = %s",
                (session['selected_package_id'],)
            )
            package = cursor.fetchone()
            
            if not package:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Package not found"
                )
            
            # Calculate subscription dates
            start_date = datetime.now().date()
            
            if package['billing_cycle'] == 'monthly':
                end_date = start_date + timedelta(days=30)
            elif package['billing_cycle'] == 'quarterly':
                end_date = start_date + timedelta(days=90)
            elif package['billing_cycle'] == 'yearly':
                end_date = start_date + timedelta(days=365)
            else:
                end_date = start_date + timedelta(days=30)
            
            print(f"📅 Subscription: {start_date} to {end_date} ({package['billing_cycle']})")
            
            # Create subscription
            print("➕ Creating subscription...")
            cursor.execute("""
                INSERT INTO client_subscriptions 
                (client_id, package_id, start_date, end_date, status)
                VALUES (%s, %s, %s, %s, 'active')
            """, (
                session['user_id'], 
                session['selected_package_id'], 
                start_date, 
                end_date
            ))
            
            subscription_id = cursor.lastrowid
            print(f"✅ Subscription created (ID: {subscription_id})")
            
            # Activate user
            print("🔓 Activating user account...")
            cursor.execute(
                "UPDATE users SET status = 'active' WHERE user_id = %s", 
                (session['user_id'],)
            )
            
            print(f"✅ User {session['user_id']} APPROVED - Status set to 'active'")
            
        else:
            # REJECTION: Set user status to 'inactive'
            cursor.execute(
                "UPDATE users SET status = 'inactive' WHERE user_id = %s", 
                (session['user_id'],)
            )
            
            print(f"❌ User {session['user_id']} REJECTED - Status set to 'inactive'")
        
        connection.commit()
        
        return {
            "success": True,
            "status": "success",
            "message": f"Onboarding {verification.verification_status} successfully",
            "onboarding_id": onboarding_id,
            "user_status": "active" if verification.verification_status == 'verified' else "inactive"
        }
        
    except HTTPException:
        if connection:
            connection.rollback()
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify onboarding: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/onboarding/{onboarding_id}", summary="Get onboarding details (Admin)")
async def get_onboarding_details(
    onboarding_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed onboarding information
    """
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view onboarding details"
        )
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT 
                os.*,
                u.full_name,
                u.email,
                u.phone,
                u.status as user_status,
                p.package_name,
                p.package_tier,
                p.description,
                p.price,
                p.billing_cycle,
                p.features,
                u_verifier.full_name as verified_by_name
            FROM onboarding_sessions os
            INNER JOIN users u ON os.user_id = u.user_id
            LEFT JOIN packages p ON os.selected_package_id = p.package_id
            LEFT JOIN users u_verifier ON os.verified_by = u_verifier.user_id
            WHERE os.onboarding_id = %s
        """
        
        cursor.execute(query, (onboarding_id,))
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Onboarding session not found"
            )
        
        # Parse JSON
        for field in ['verification_data', 'features']:
            if session.get(field):
                try:
                    if isinstance(session[field], str):
                        session[field] = json.loads(session[field])
                except:
                    session[field] = {}
        
        return {
            "status": "success",
            "onboarding_session": session
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve onboarding details: {str(e)}"
        )
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()