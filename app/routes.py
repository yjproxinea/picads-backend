import uuid
from typing import Any, Dict, List, Optional

import stripe
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import User, get_current_user, get_current_user_optional
from app.config import settings
from app.database import get_db
from app.schemas import (
    AdGenerationRequest,
    AdGenerationResponse,
    BrandIdentityCreate,
    BrandIdentityResponse,
    BrandIdentityUpdate,
    ErrorResponse,
    InitSubscriptionRequest,
    InitSubscriptionResponse,
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
    UsageLogResponse,
    UserAdResponse,
    UserAssetCreate,
    UserAssetResponse,
)
from app.services import (
    AdGenerationService,
    AssetService,
    BrandIdentityService,
    CreditsService,
    ProfileService,
    StripeService,
    get_user_credits_summary,
)
from app.storage import storage

router = APIRouter()

@router.get("/")
async def welcome():
    """Public welcome endpoint"""
    return {"message": "Welcome to Picads Backend!"}

@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's profile with credits"""
    profile = await ProfileService.get_profile(db, current_user.id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get credits for this user
    credits = await CreditsService.get_credits(db, current_user.id)
    
    # Create response with profile and credits data
    response_data = {
        "user_id": profile.user_id,
        "plan": profile.plan,
        "stripe_customer_id": profile.stripe_customer_id,
        "payment_status": profile.payment_status,
        "created_at": profile.created_at,
        # Include credits in the profile response
        "included_credits": credits.included_credits if credits else 0,
        "metered_credits": credits.metered_credits if credits else 0,
        "total_used": credits.total_used if credits else 0,
        "available_credits": credits.available_credits if credits else 0,
        # Include credits timestamps
        "last_refill": credits.last_refill if credits else None,
        "grace_until": credits.grace_until if credits else None,
        "updated_at": credits.updated_at if credits else None
    }
    
    return ProfileResponse.model_validate(response_data)

@router.post("/profile", response_model=ProfileResponse)
async def create_profile_endpoint(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create user profile - only used after successful Stripe payment"""
    # Check if profile already exists
    existing_profile = await ProfileService.get_profile(db, current_user.id)
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    # Create new profile
    profile = await ProfileService.create_profile(db, current_user.id, profile_data)
    
    # Get credits for this user  
    credits = await CreditsService.get_credits(db, current_user.id)
    
    # Create response with profile and credits data
    response_data = {
        "user_id": profile.user_id,
        "plan": profile.plan,
        "stripe_customer_id": profile.stripe_customer_id,
        "payment_status": profile.payment_status,
        "created_at": profile.created_at,
        # Include credits in the profile response
        "included_credits": credits.included_credits if credits else 0,
        "metered_credits": credits.metered_credits if credits else 0,
        "total_used": credits.total_used if credits else 0,
        "available_credits": credits.available_credits if credits else 0,
        # Include credits timestamps
        "last_refill": credits.last_refill if credits else None,
        "grace_until": credits.grace_until if credits else None,
        "updated_at": credits.updated_at if credits else None
    }
    
    return ProfileResponse.model_validate(response_data)

@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile with credits"""
    profile = await ProfileService.update_profile(db, current_user.id, profile_data)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get credits for this user
    credits = await CreditsService.get_credits(db, current_user.id)
    
    # Create response with profile and credits data
    response_data = {
        "user_id": profile.user_id,
        "plan": profile.plan,
        "stripe_customer_id": profile.stripe_customer_id,
        "payment_status": profile.payment_status,
        "created_at": profile.created_at,
        # Include credits in the profile response
        "included_credits": credits.included_credits if credits else 0,
        "metered_credits": credits.metered_credits if credits else 0,
        "total_used": credits.total_used if credits else 0,
        "available_credits": credits.available_credits if credits else 0,
        # Include credits timestamps
        "last_refill": credits.last_refill if credits else None,
        "grace_until": credits.grace_until if credits else None,
        "updated_at": credits.updated_at if credits else None
    }
    
    return ProfileResponse.model_validate(response_data)

# Ad Generation Endpoints
@router.post("/generate/text-ad")
async def generate_text_ad(
    request: AdGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate text ad with credit billing and usage tracking"""
    # Ensure ad_type is set correctly
    request.ad_type = "text_ad"
    
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    # Initialize ad generation service
    ad_service = AdGenerationService(db)
    
    # Generate ad
    response, error = await ad_service.generate_ad(user_uuid, request)
    
    if error:
        raise HTTPException(status_code=400, detail=error.dict())
    
    return response

@router.post("/generate/image-ad")
async def generate_image_ad(
    request: AdGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate image ad with credit billing and usage tracking"""
    # Ensure ad_type is set correctly
    request.ad_type = "image_ad"
    
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    # Initialize ad generation service
    ad_service = AdGenerationService(db)
    
    # Generate ad
    response, error = await ad_service.generate_ad(user_uuid, request)
    
    if error:
        raise HTTPException(status_code=400, detail=error.dict())
    
    return response

@router.post("/generate/video-ad")
async def generate_video_ad(
    request: AdGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate video ad with credit billing and usage tracking"""
    # Ensure ad_type is set correctly
    request.ad_type = "video_ad"
    
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    # Initialize ad generation service
    ad_service = AdGenerationService(db)
    
    # Generate ad
    response, error = await ad_service.generate_ad(user_uuid, request)
    
    if error:
        raise HTTPException(status_code=400, detail=error.dict())
    
    return response

# Credits and Usage Endpoints
@router.get("/credits/summary")
async def get_credits_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed credits summary for current user"""
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    credits_summary = await get_user_credits_summary(db, user_uuid)
    return credits_summary

@router.get("/usage-log")
async def get_usage_log(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get user's usage log with pagination"""
    from app.models import UsageLog

    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    result = await db.execute(
        select(UsageLog)
        .filter(UsageLog.user_id == user_uuid)
        .order_by(UsageLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    usage_logs = result.scalars().all()
    
    return [UsageLogResponse.model_validate(log) for log in usage_logs]

@router.get("/ads")
async def get_user_ads(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ad_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get user's generated ads with optional filtering by type"""
    from sqlalchemy import select

    from app.models import UserAds

    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    query = select(UserAds).filter(UserAds.user_id == user_uuid)
    
    if ad_type:
        query = query.filter(UserAds.ad_type == ad_type)
    
    result = await db.execute(
        query.order_by(UserAds.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    ads = result.scalars().all()
    
    return [UserAdResponse.model_validate(ad) for ad in ads]

@router.get("/assets")
async def get_user_assets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    asset_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get user's uploaded assets with optional filtering by type"""
    from sqlalchemy import select

    from app.models import UserAssets

    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    query = select(UserAssets).filter(UserAssets.user_id == user_uuid)
    
    if asset_type:
        query = query.filter(UserAssets.asset_type == asset_type)
    
    result = await db.execute(
        query.order_by(UserAssets.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    assets = result.scalars().all()
    
    return [UserAssetResponse.model_validate(asset) for asset in assets]

@router.post("/init-subscription", response_model=InitSubscriptionResponse)
async def init_subscription(
    request: InitSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Initialize subscription with Stripe checkout for the single plan (39.00 CHF/month)"""
    try:
        # Step 1: Verify user identity (already done by get_current_user dependency)
        
        # Step 2: Create or get Stripe customer
        customer_id = await StripeService.create_or_get_stripe_customer(
            user_email=current_user.email,
            user_name=current_user.full_name,
            user_id=current_user.id
        )
        
        # Step 3: Create Stripe checkout session
        # NOTE: Profile creation will happen in webhook after successful payment
        checkout_url = await StripeService.create_checkout_session(
            customer_id=customer_id,
            plan_info=request.plan.model_dump(),
            user_id=current_user.id
        )
        
        return InitSubscriptionResponse(
            checkoutUrl=checkout_url,
            customer_id=customer_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize subscription: {str(e)}"
        )

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe webhook events - creates profile only after successful payment"""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        # Verify webhook signature (if webhook secret is available and not in local dev)
        if settings.STRIPE_WEBHOOK_SECRET and not settings.FRONTEND_URL.startswith("http://localhost"):
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid payload")
            except stripe.SignatureVerificationError:
                raise HTTPException(status_code=400, detail="Invalid signature")
        else:
            # For local development - skip signature verification
            import json
            event = json.loads(payload)
        
        # Handle checkout.session.completed event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Extract user_id from metadata
            user_id = session['metadata'].get('user_id')
            customer_id = session['customer']
            
            if not user_id:
                print(f"No user_id in session metadata: {session['id']}")
                return {"status": "error", "message": "No user_id in metadata"}
            
            # Create profile with Stripe customer ID
            profile_data = ProfileCreate(stripe_customer_id=customer_id)
            
            try:
                # Check if profile already exists
                existing_profile = await ProfileService.get_profile(db, user_id)
                
                if not existing_profile:
                    # Create new profile
                    profile = await ProfileService.create_profile(db, user_id, profile_data)
                    
                    # Create credits record with 1000 included credits (default for the plan)
                    await CreditsService.create_credits(db, user_id, included_credits=1000)
                    
                    print(f"Profile and credits created for user {user_id} with pro plan and 1000 credits")
                else:
                    # Update existing profile with Stripe customer ID
                    profile_update = ProfileUpdate(stripe_customer_id=customer_id)
                    await ProfileService.update_profile(db, user_id, profile_update)
                    
                    # Check if credits exist, create if not
                    existing_credits = await CreditsService.get_credits(db, user_id)
                    if not existing_credits:
                        await CreditsService.create_credits(db, user_id, included_credits=1000)
                        print(f"Credits created for existing user {user_id} with 1000 credits")
                    
                    print(f"Profile updated for user {user_id} with Stripe customer {customer_id}")
                
            except Exception as e:
                print(f"Error creating/updating profile and credits for user {user_id}: {e}")
                return {"status": "error", "message": str(e)}
        
        # Handle subscription invoice events
        elif event['type'] == 'invoice.paid':
            invoice = event['data']['object']
            customer_id = invoice['customer']
            print(f"Invoice paid for customer {customer_id}")
            
        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            customer_id = invoice['customer']
            print(f"Invoice payment failed for customer {customer_id}")
            # Here you could disable access, send notification, etc.
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

@router.get("/public-data")
async def get_public_data(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Optional auth route - works with or without token"""
    if current_user:
        return {
            "message": "Personalized data for authenticated user",
            "user_email": current_user.email,
            "data": "Premium content here..."
        }
    else:
        return {
            "message": "Public data for anonymous user",
            "data": "Basic content here..."
        }

@router.get("/dashboard")
async def dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Protected dashboard endpoint that returns basic user info, profile data, and credits"""
    profile = await ProfileService.get_profile(db, current_user.id)
    credits = await CreditsService.get_credits(db, current_user.id)

    response: Dict[str, Any] = {
        "message": "Welcome to your dashboard!",
        "user_id": current_user.id,
        "email": current_user.email,
    }

    if profile:
        response["profile"] = {
            "plan": profile.plan,
            "payment_status": profile.payment_status,
            "stripe_customer_id": profile.stripe_customer_id,
        }
    
    if credits:
        response["credits"] = {
            "included_credits": credits.included_credits,
            "metered_credits": credits.metered_credits,
            "total_used": credits.total_used,
            "available": credits.available_credits if credits else 0
        }

    return response

@router.post("/brand-identity", response_model=BrandIdentityResponse)
async def create_brand_identity(
    brand_data: BrandIdentityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create brand identity for user"""
    try:
        brand = await BrandIdentityService.create_brand_identity(
            db=db,
            user_id=uuid.UUID(current_user.id),
            brand_data=brand_data
        )
        return brand
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create brand identity: {str(e)}"
        )

@router.get("/brand-identity", response_model=BrandIdentityResponse)
async def get_brand_identity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's brand identity"""
    brand = await BrandIdentityService.get_brand_identity(
        db=db, 
        user_id=uuid.UUID(current_user.id)
    )
    if not brand:
        raise HTTPException(status_code=404, detail="Brand identity not found")
    return brand

@router.put("/brand-identity", response_model=BrandIdentityResponse)
async def update_brand_identity(
    brand_data: BrandIdentityUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update brand identity"""
    brand = await BrandIdentityService.update_brand_identity(
        db=db,
        user_id=uuid.UUID(current_user.id),
        brand_data=brand_data
    )
    if not brand:
        raise HTTPException(status_code=404, detail="Brand identity not found")
    return brand

@router.post("/assets/upload", response_model=UserAssetResponse)
async def upload_asset(
    file: UploadFile,
    asset_type: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a new asset"""
    try:
        print(f"[UPLOAD_ASSET] Starting upload process...")
        print(f"[UPLOAD_ASSET] Received params: asset_type={asset_type}, description={description}")
        print(f"[UPLOAD_ASSET] File info: name={file.filename}, content_type={file.content_type}, size={file.size}")
        
        if not file.filename:
            print("[UPLOAD_ASSET] Error: No filename provided")
            raise HTTPException(
                status_code=400,
                detail="No filename provided"
            )
            
        # Generate unique filename
        file_ext = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = f"assets/{current_user.id}/{asset_type}/{unique_filename}"
        print(f"[UPLOAD_ASSET] Generated file path: {file_path}")
        
        # Upload file to storage
        print("[UPLOAD_ASSET] Attempting to upload file to storage...")
        file_url = await storage.upload_file(
            file=file,
            path=file_path,
            bucket="assets"
        )
        
        if not file_url:
            print("[UPLOAD_ASSET] Error: Failed to get file URL from storage")
            raise HTTPException(
                status_code=500,
                detail="Failed to upload file to storage"
            )
        
        print(f"[UPLOAD_ASSET] File uploaded successfully, URL: {file_url}")
        
        # Create asset record
        print("[UPLOAD_ASSET] Creating asset record in database...")
        asset_data = UserAssetCreate(
            asset_type=asset_type,
            file_path=file_path,
            original_filename=file.filename,
            size=file.size or 0,  # Default to 0 if size is None
            mime_type=file.content_type or 'application/octet-stream',  # Default if content_type is None
            description=description
        )
        print(f"[UPLOAD_ASSET] Asset data prepared: {asset_data}")
        
        asset = await AssetService.create_asset(
            db=db,
            user_id=uuid.UUID(current_user.id),
            asset_data=asset_data
        )
        print("[UPLOAD_ASSET] Asset record created successfully")
        
        return asset
    except ValidationError as ve:
        print(f"[UPLOAD_ASSET] Validation error: {str(ve)}")
        raise HTTPException(
            status_code=422,
            detail=f"Validation error: {str(ve)}"
        )
    except Exception as e:
        print(f"[UPLOAD_ASSET] Unexpected error: {str(e)}")
        print(f"[UPLOAD_ASSET] Error type: {type(e)}")
        import traceback
        print(f"[UPLOAD_ASSET] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to upload asset: {str(e)}"
        )

@router.get("/assets/{asset_id}", response_model=UserAssetResponse)
async def get_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get asset by ID"""
    asset = await AssetService.get_asset(db=db, asset_id=asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.user_id != uuid.UUID(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this asset")
    return asset

@router.get("/assets", response_model=List[UserAssetResponse])
async def list_assets(
    asset_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's assets"""
    assets = await AssetService.get_user_assets(
        db=db,
        user_id=uuid.UUID(current_user.id),
        asset_type=asset_type,
        limit=limit,
        offset=offset
    )
    return assets 