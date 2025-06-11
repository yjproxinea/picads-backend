import random
import string
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Union

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.config import (
    AD_PRICING,
    ASSETS_BASE_URL,
    STRIPE_PRICE_ID_METERED,
    STRIPE_SECRET_KEY,
    settings,
)
from app.models import Credits, Profile, UsageLog, UserAds
from app.schemas import (
    AdGenerationRequest,
    BillingInfo,
    ErrorResponse,
    ProfileCreate,
    ProfileUpdate,
)

# Configure Stripe
stripe.api_key = STRIPE_SECRET_KEY


class ProfileService:
    """Service class for Profile business logic using SQLAlchemy with Supabase PostgreSQL"""
    
    @staticmethod
    async def get_profile(db: AsyncSession, user_id: str) -> Optional[Profile]:
        """Get profile by user ID"""
        user_uuid = uuid.UUID(user_id)  # Convert string to UUID
        result = await db.execute(select(Profile).filter(Profile.user_id == user_uuid))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_profile(db: AsyncSession, user_id: str, profile_data: ProfileCreate) -> Profile:
        """Create a new profile (credits are created separately via webhook after payment)"""
        print("[ProfileService] Creating profile...")  # DEBUG
        user_uuid = uuid.UUID(user_id)  # Convert string to UUID
        
        # Create profile with pro plan
        db_profile = Profile(
            user_id=user_uuid,
            plan='pro',  # Set to pro since we only have one plan
            stripe_customer_id=profile_data.stripe_customer_id if hasattr(profile_data, 'stripe_customer_id') else None,
            payment_status='active',
            created_at=datetime.utcnow()
        )
        db.add(db_profile)
        
        try:
            # Commit profile only (credits handled by webhook after payment)
            await db.commit()
            await db.refresh(db_profile)  # Refresh to get updated data
            print("[ProfileService] Profile committed and refreshed.")  # DEBUG
        except Exception as e:
            print(f"[ProfileService] Commit failed: {e}")
            raise
        return db_profile
    
    @staticmethod
    async def update_profile(db: AsyncSession, user_id: str, profile_data: ProfileUpdate) -> Optional[Profile]:
        """Update an existing profile"""
        user_uuid = uuid.UUID(user_id)  # Convert string to UUID
        result = await db.execute(select(Profile).filter(Profile.user_id == user_uuid))
        db_profile = result.scalar_one_or_none()
        
        if not db_profile:
            return None
        
        # Update only provided fields
        if hasattr(profile_data, 'plan') and profile_data.plan is not None:
            db_profile.plan = profile_data.plan
        if hasattr(profile_data, 'stripe_customer_id') and profile_data.stripe_customer_id is not None:
            db_profile.stripe_customer_id = profile_data.stripe_customer_id
        if hasattr(profile_data, 'payment_status') and profile_data.payment_status is not None:
            db_profile.payment_status = profile_data.payment_status
        
        await db.commit()  # Commit the transaction
        await db.refresh(db_profile)  # Refresh to get updated data
        return db_profile
    
    @staticmethod
    async def get_or_create_profile(db: AsyncSession, user_id: str, profile_data: Optional[ProfileCreate] = None) -> Tuple[Profile, bool]:
        """Get existing profile or create new one. Returns (profile, is_new)"""
        existing_profile = await ProfileService.get_profile(db, user_id)
        
        if existing_profile:
            return existing_profile, False
        
        # Create new profile
        create_data = profile_data or ProfileCreate()
        new_profile = await ProfileService.create_profile(db, user_id, create_data)
        return new_profile, True


class CreditsService:
    """Service class for Credits business logic"""
    
    @staticmethod
    async def get_credits(db: AsyncSession, user_id: str) -> Optional[Credits]:
        """Get credits by user ID"""
        user_uuid = uuid.UUID(user_id)  # Convert string to UUID
        result = await db.execute(select(Credits).filter(Credits.user_id == user_uuid))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_credits(db: AsyncSession, user_id: str, included_credits: int = 1000) -> Credits:
        """Create a new credits record for a user"""
        user_uuid = uuid.UUID(user_id)  # Convert string to UUID
        
        # Create credits record
        db_credits = Credits(
            user_id=user_uuid,
            included_credits=included_credits,
            available_credits=included_credits,  # Available credits start equal to included credits
            metered_credits=0,
            total_used=0,
            updated_at=datetime.utcnow()
        )
        db.add(db_credits)
        
        try:
            await db.commit()
            await db.refresh(db_credits)
            print(f"[CreditsService] Credits created for user {user_id} with {included_credits} credits")
        except Exception as e:
            print(f"[CreditsService] Commit failed: {e}")
            raise
        
        return db_credits


class StripeService:
    """Service class for Stripe operations"""
    
    @staticmethod
    async def create_or_get_stripe_customer(user_email: str, user_name: Optional[str] = None, user_id: Optional[str] = None) -> str:
        """Create a new Stripe customer or get existing one"""
        try:
            # Search for existing customer by email
            existing_customers = stripe.Customer.list(email=user_email, limit=1)
            
            if existing_customers.data:
                # Return existing customer ID
                return existing_customers.data[0].id
            
            # Create new customer
            customer = stripe.Customer.create(
                email=user_email,
                name=user_name or "",
                metadata={
                    'user_id': user_id or ''
                }
            )
            
            return customer.id
            
        except stripe.StripeError as e:
            raise Exception(f"Failed to create Stripe customer: {str(e)}")

    @staticmethod
    async def create_checkout_session(customer_id: str, plan_info: dict, user_id: str) -> str:
        """Create a Stripe Checkout session with both base subscription and metered billing"""
        try:
            # Get both price IDs from config
            base_price_id = settings.STRIPE_PRICE_ID_SUBSCRIPTION  # Base monthly subscription
            metered_price_id = settings.STRIPE_PRICE_ID_METERED  # Pay-as-you-go credits
            
            if not base_price_id:
                raise Exception("STRIPE_PRICE_ID_SUBSCRIPTION not configured in environment variables")
            if not metered_price_id:
                raise Exception("STRIPE_PRICE_ID_METERED not configured in environment variables")
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': base_price_id,  # CHF 39.00/month base subscription
                        'quantity': 1,
                    },
                    {
                        'price': metered_price_id,  # CHF 0.05/credit metered billing
                        # No quantity for metered usage types
                    }
                ],
                mode='subscription',
                # Let Stripe handle the billing start time automatically
                success_url=f"{settings.FRONTEND_URL}/signup-complete?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/signup?canceled=true",
                metadata={
                    'user_id': user_id,
                    'plan_id': plan_info['id'],
                    'plan_name': plan_info['name']
                }
            )
            
            return session.url or ""
            
        except stripe.StripeError as e:
            raise Exception(f"Failed to create checkout session: {str(e)}")


class AdGenerationService:
    """Service class for handling ad generation, billing, and asset management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_ad(self, user_id: uuid.UUID, request: AdGenerationRequest) -> Tuple[Optional[Dict[str, Any]], Optional[ErrorResponse]]:
        """
        Main method to generate ads with simplified credit billing
        
        Returns:
            Tuple of (success_response, error_response)
        """
        try:
            # 1. Check user payment status
            profile_result = await self.db.execute(select(Profile).filter(Profile.user_id == user_id))
            profile = profile_result.scalar_one_or_none()
            if not profile:
                return None, ErrorResponse(
                    message="User profile not found",
                    error_code="PROFILE_NOT_FOUND"
                )
            
            if profile.payment_status != "active":
                return None, ErrorResponse(
                    message="Payment status is not active. Please update your subscription.",
                    error_code="PAYMENT_INACTIVE"
                )
            
            # 2. Calculate credit cost
            credit_cost = AD_PRICING.get(request.ad_type)
            if not credit_cost:
                return None, ErrorResponse(
                    message=f"Invalid ad type: {request.ad_type}",
                    error_code="INVALID_AD_TYPE"
                )
            
            # 3. Get user credits
            credits_result = await self.db.execute(select(Credits).filter(Credits.user_id == user_id))
            credits = credits_result.scalar_one_or_none()
            if not credits:
                return None, ErrorResponse(
                    message="User credits record not found",
                    error_code="CREDITS_NOT_FOUND"
                )
            
            # 4. Generate ad content first (placeholder)
            generated_content = self._generate_ad_content(request)
            
            # 5. Only if generation succeeds, handle billing
            billing_result = self._handle_billing(
                credits, credit_cost, profile.stripe_customer_id
            )
            
            # 6. Update credits in database
            await self._update_credits(credits, credit_cost, billing_result.get("shortage", 0))
            
            # 7. Create usage log
            usage_log = await self._create_usage_log(user_id, request, credit_cost, billing_result)
            
            # 8. Create user ad (placeholder)
            ad = await self._create_user_ad(user_id, request.ad_type)
            
            # 9. Prepare response
            response = {
                "success": True,
                "message": f"{request.ad_type.replace('_', ' ').title()} generated successfully",
                "ad_type": request.ad_type,
                "ad_id": ad.id,
                "ad_url": f"{ASSETS_BASE_URL}/{ad.file_path}",
                "billing_info": BillingInfo(
                    credits_used=credit_cost,
                    metered_credits=billing_result.get("metered_credits")
                ),
                "usage_log_id": usage_log.id,
                "generated_content": generated_content
            }
            
            return response, None
            
        except Exception as e:
            return None, ErrorResponse(
                message=f"Internal server error: {str(e)}",
                error_code="INTERNAL_ERROR"
            )
    
    def _handle_billing(self, credits: Credits, credit_cost: int, stripe_customer_id: Optional[str]) -> Dict[str, Any]:
        """Simple billing: check credits and bill Stripe if needed"""
        
        # Calculate shortage once
        shortage = max(0, credit_cost - credits.available_credits)
        metered_credits = shortage if shortage > 0 else None
        
        # Bill Stripe for shortage if needed
        if shortage > 0:
            try:
                if stripe_customer_id:
                    # Report usage in real-time - let Stripe assign "now" timestamp
                    # This is more accurate since it uses the exact processing time
                    stripe.billing.MeterEvent.create(
                        event_name=settings.STRIPE_METER_NAME,  # Use configurable meter name
                        payload={
                            "stripe_customer_id": stripe_customer_id,
                            "value": str(shortage)  # Number of credits
                        }
                    )
                    print(f"[Billing] Successfully billed {shortage} credits to Stripe for customer {stripe_customer_id}")
                    print(f"[Billing] Meter event reported in real-time (Stripe will assign current timestamp)")
                    
            except stripe.StripeError as e:
                # Handle missing meter gracefully for testing
                error_message = str(e)
                if "No active meter found" in error_message:
                    print(f"[Billing] Warning: Stripe meter '{settings.STRIPE_METER_NAME}' not configured. Skipping Stripe billing for {shortage} credits.")
                    # Continue without billing for now - credits are still tracked locally
                else:
                    print(f"[Billing] Stripe billing error: {error_message}")
                    # For other Stripe errors, we might want to fail
                    # raise Exception(f"Stripe billing failed: {str(e)}")
                    # For now, continue without billing
                    print(f"[Billing] Warning: Stripe billing failed, continuing without billing: {error_message}")
        
        return {
            "metered_credits": metered_credits,
            "shortage": shortage
        }
    
    async def _update_credits(self, credits: Credits, credit_cost: int, shortage: int):
        """Update credits: deduct from available first, then track metered usage"""
        # Deduct from available credits (but don't go below 0)
        credits_from_available = min(credits.available_credits, credit_cost)
        credits.available_credits -= credits_from_available
        
        # Add shortage to metered credits (already calculated and billed)
        if shortage > 0:
            credits.metered_credits += shortage
        
        # Always increment total used
        credits.total_used += credit_cost
        credits.updated_at = datetime.utcnow()
        await self.db.commit()
    
    async def _create_usage_log(self, user_id: uuid.UUID, request: AdGenerationRequest, credit_cost: int, billing_result: Dict[str, Any]) -> UsageLog:
        """Create a usage log entry"""
        usage_log = UsageLog(
            user_id=user_id,
            ad_type=request.ad_type,
            credits_used=credit_cost,
            source="api_generation",
            extra_data={
                "prompt": request.prompt,
                "target_audience": request.target_audience,
                "platform": request.platform,
                "metered_credits": billing_result.get("metered_credits"),
                "additional_params": request.additional_params
            }
        )
        
        self.db.add(usage_log)
        await self.db.commit()
        await self.db.refresh(usage_log)
        return usage_log
    
    async def _create_user_ad(self, user_id: uuid.UUID, ad_type: str) -> UserAds:
        """Create a user ad record with placeholder data"""
        
        # Generate random file path and details
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        
        ad_config = {
            "text_ad": {
                "file_path": f"text_ads/{random_id}.json",
                "mime_type": "application/json",
                "size": random.randint(500, 2000),
                "name": f"Text Ad - {random_id[:6]}"
            },
            "image_ad": {
                "file_path": f"image_ads/{random_id}.png",
                "mime_type": "image/png",
                "size": random.randint(50000, 500000),
                "name": f"Image Ad - {random_id[:6]}"
            },
            "video_ad": {
                "file_path": f"video_ads/{random_id}.mp4",
                "mime_type": "video/mp4",
                "size": random.randint(1000000, 10000000),
                "name": f"Video Ad - {random_id[:6]}"
            }
        }
        
        config = ad_config.get(ad_type, ad_config["text_ad"])
        
        ad = UserAds(
            user_id=user_id,
            ad_type=ad_type,
            file_path=config["file_path"],
            name=config["name"],
            size=config["size"],
            mime_type=config["mime_type"],
            tags=f"{ad_type},generated,placeholder"  # Store as comma-separated string
        )
        
        self.db.add(ad)
        await self.db.commit()
        await self.db.refresh(ad)
        return ad
    
    def _generate_ad_content(self, request: AdGenerationRequest) -> Dict[str, Any]:
        """Generate placeholder ad content (to be replaced with actual AI generation)"""
        
        content_templates = {
            "text_ad": {
                "headline": f"Amazing {request.target_audience or 'Product'} Solution!",
                "description": f"Based on your prompt: '{request.prompt[:50]}...' - This is a placeholder text ad that will be generated by AI.",
                "call_to_action": "Learn More",
                "platform_optimized": request.platform or "general"
            },
            "image_ad": {
                "image_url": "/placeholder-image-ad.png",
                "alt_text": f"Generated image ad for {request.target_audience or 'target audience'}",
                "dimensions": "1080x1080",
                "format": "PNG",
                "description": f"AI-generated image based on: {request.prompt[:100]}..."
            },
            "video_ad": {
                "video_url": "/placeholder-video-ad.mp4",
                "duration": "30s",
                "format": "MP4",
                "resolution": "1920x1080",
                "description": f"AI-generated video based on: {request.prompt[:100]}...",
                "thumbnail_url": "/placeholder-video-thumbnail.png"
            }
        }
        
        return content_templates.get(request.ad_type, {})


async def get_user_credits_summary(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
    """Get detailed credits summary for a user"""
    result = await db.execute(select(Credits).filter(Credits.user_id == user_id))
    credits = result.scalar_one_or_none()
    
    if not credits:
        return {
            "included_credits": 0,
            "metered_credits": 0,
            "total_used": 0,
            "available_credits": 0,
            "last_refill": None,
            "grace_until": None
        }
    
    return {
        "included_credits": credits.included_credits,
        "metered_credits": credits.metered_credits,
        "total_used": credits.total_used,
        "available_credits": credits.available_credits,
        "last_refill": credits.last_refill,
        "grace_until": credits.grace_until,
        "updated_at": credits.updated_at
    } 