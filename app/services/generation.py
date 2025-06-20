import json
import random
import string
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import AD_PRICING, ASSETS_BASE_URL, settings
from app.models import Credits, Profile, UsageLog, UserAds
from app.schemas import AdGenerationRequest, BillingInfo, ErrorResponse
from app.storage import storage


class AdGenerationService:
    """Service class for handling ad generation, billing, and asset management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_ad_preview(self, user_id: uuid.UUID, request: AdGenerationRequest) -> Tuple[Optional[Dict[str, Any]], Optional[ErrorResponse]]:
        """
        Generate ad content for preview (draft mode) without billing
        
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
            
            # 2. Calculate credit cost (for display purposes)
            credit_cost = AD_PRICING.get(request.ad_type)
            if not credit_cost:
                return None, ErrorResponse(
                    message=f"Invalid ad type: {request.ad_type}",
                    error_code="INVALID_AD_TYPE"
                )
            
            # 3. Generate ad content
            generated_content = self._generate_ad_content(request)
            
            # 4. Store ad content in Supabase bucket
            file_path, file_url = await self._store_ad_content(user_id, request.ad_type, generated_content)
            
            # 5. Create user ad in draft mode
            ad = await self._create_user_ad_draft(user_id, request.ad_type, file_path, generated_content)
            
            # 6. Create usage log in draft mode
            usage_log = await self._create_usage_log_draft(user_id, request, credit_cost, ad.id)
            
            # 7. Prepare response
            response = {
                "success": True,
                "message": f"{request.ad_type.replace('_', ' ').title()} preview generated successfully",
                "ad_type": request.ad_type,
                "ad_id": ad.id,
                "usage_log_id": usage_log.id,
                "preview_url": file_url,
                "credit_cost": credit_cost,  # Show cost but don't charge yet
                "generated_content": generated_content,
                "is_draft": True
            }
            
            return response, None
            
        except Exception as e:
            return None, ErrorResponse(
                message=f"Internal server error: {str(e)}",
                error_code="INTERNAL_ERROR"
            )
    
    async def save_ad(self, user_id: uuid.UUID, ad_id: uuid.UUID) -> Tuple[Optional[Dict[str, Any]], Optional[ErrorResponse]]:
        """
        Save ad from draft to final (trigger billing and credit deduction)
        
        Returns:
            Tuple of (success_response, error_response)
        """
        try:
            # 1. Get the ad and usage log
            ad_result = await self.db.execute(select(UserAds).filter(UserAds.id == ad_id, UserAds.user_id == user_id))
            ad = ad_result.scalar_one_or_none()
            if not ad:
                return None, ErrorResponse(
                    message="Ad not found",
                    error_code="AD_NOT_FOUND"
                )
            
            if not ad.is_draft:
                return None, ErrorResponse(
                    message="Ad is already saved",
                    error_code="AD_ALREADY_SAVED"
                )
            
            # 2. Get the associated usage log
            usage_log_result = await self.db.execute(
                select(UsageLog).filter(UsageLog.ad_id == ad_id, UsageLog.is_draft == True)
            )
            usage_log = usage_log_result.scalar_one_or_none()
            if not usage_log:
                return None, ErrorResponse(
                    message="Usage log not found",
                    error_code="USAGE_LOG_NOT_FOUND"
                )
            
            # 3. Get user profile and credits
            profile_result = await self.db.execute(select(Profile).filter(Profile.user_id == user_id))
            profile = profile_result.scalar_one_or_none()
            
            credits_result = await self.db.execute(select(Credits).filter(Credits.user_id == user_id))
            credits = credits_result.scalar_one_or_none()
            if not credits:
                return None, ErrorResponse(
                    message="User credits record not found",
                    error_code="CREDITS_NOT_FOUND"
                )
            
            # 4. Handle billing
            billing_result = self._handle_billing(
                credits, usage_log.credits_used, profile.stripe_customer_id if profile else None
            )
            
            # 5. Update credits in database
            await self._update_credits(credits, usage_log.credits_used, billing_result.get("shortage", 0))
            
            # 6. Update usage log (mark as not draft and add billing info)
            usage_log.is_draft = False
            usage_log.extra_data = usage_log.extra_data or {}
            usage_log.extra_data.update({
                "metered_credits": billing_result.get("metered_credits"),
                "billing_status": "billed",
                "saved_at": datetime.utcnow().isoformat()
            })
            
            # 7. Update ad (mark as not draft)
            ad.is_draft = False
            ad.tags = ad.tags.replace("draft", "saved") if ad.tags else "saved"
            
            await self.db.commit()
            
            # 8. Get the file URL for download
            file_url = storage.get_file_url(ad.file_path, "ads")
            
            # 9. Prepare response
            response = {
                "success": True,
                "message": f"{ad.ad_type.replace('_', ' ').title()} saved successfully",
                "ad_id": ad.id,
                "usage_log_id": usage_log.id,
                "download_url": file_url,
                "billing_info": BillingInfo(
                    credits_used=usage_log.credits_used,
                    metered_credits=billing_result.get("metered_credits")
                ),
                "is_draft": False
            }
            
            return response, None
            
        except Exception as e:
            return None, ErrorResponse(
                message=f"Internal server error: {str(e)}",
                error_code="INTERNAL_ERROR"
            )
    
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
            
            # 5. Store ad content in Supabase bucket
            file_path, file_url = await self._store_ad_content(user_id, request.ad_type, generated_content)
            
            # 6. Only if generation succeeds, handle billing
            billing_result = self._handle_billing(
                credits, credit_cost, profile.stripe_customer_id
            )
            
            # 7. Update credits in database
            await self._update_credits(credits, credit_cost, billing_result.get("shortage", 0))
            
            # 8. Create usage log
            usage_log = await self._create_usage_log(user_id, request, credit_cost, billing_result)
            
            # 9. Create user ad (placeholder)
            ad = await self._create_user_ad(user_id, request.ad_type, file_path, generated_content)
            
            # 10. Prepare response
            response = {
                "success": True,
                "message": f"{request.ad_type.replace('_', ' ').title()} generated successfully",
                "ad_type": request.ad_type,
                "ad_id": ad.id,
                "ad_url": file_url,
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
    
    async def _store_ad_content(self, user_id: uuid.UUID, ad_type: str, generated_content: Dict[str, Any]) -> Tuple[str, str]:
        """
        Store generated ad content in Supabase bucket
        
        Args:
            user_id: The user ID
            ad_type: The type of ad (text_ad, image_ad, video_ad)
            generated_content: The generated ad content
            
        Returns:
            Tuple of (file_path, file_url)
        """
        try:
            # Generate unique filename
            random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            
            # Determine file path and content based on ad type
            if ad_type == "text_ad":
                file_path = f"ads/{user_id}/text_ads/{random_id}.json"
                content = json.dumps(generated_content, indent=2)
                content_type = "application/json"
            elif ad_type == "image_ad":
                # For now, store image metadata as JSON
                # In a real implementation, you'd generate and store the actual image
                file_path = f"ads/{user_id}/image_ads/{random_id}.json"
                content = json.dumps(generated_content, indent=2)
                content_type = "application/json"
            elif ad_type == "video_ad":
                # For now, store video metadata as JSON
                # In a real implementation, you'd generate and store the actual video
                file_path = f"ads/{user_id}/video_ads/{random_id}.json"
                content = json.dumps(generated_content, indent=2)
                content_type = "application/json"
            else:
                raise ValueError(f"Unsupported ad type: {ad_type}")
            
            # Convert content to bytes
            content_bytes = content.encode('utf-8')
            
            # Upload directly to Supabase Storage
            result = storage.supabase.storage.from_("ads").upload(
                file_path,
                content_bytes,
                file_options={"contentType": content_type}
            )

            if result:
                file_url = storage.supabase.storage.from_("ads").get_public_url(file_path)
            else:
                raise Exception("Failed to upload ad content to storage")

            return file_path, file_url
            
        except Exception as e:
            print(f"Error storing ad content: {e}")
            raise e
    
    async def _create_user_ad_draft(self, user_id: uuid.UUID, ad_type: str, file_path: str, generated_content: Dict[str, Any]) -> UserAds:
        """Create a user ad record in draft mode"""
        
        # Calculate file size from content
        content_size = len(json.dumps(generated_content, indent=2).encode('utf-8'))
        
        ad_config = {
            "text_ad": {
                "mime_type": "application/json",
                "name": f"Text Ad - {file_path.split('/')[-1].split('.')[0]}"
            },
            "image_ad": {
                "mime_type": "application/json",  # For now, storing metadata as JSON
                "name": f"Image Ad - {file_path.split('/')[-1].split('.')[0]}"
            },
            "video_ad": {
                "mime_type": "application/json",  # For now, storing metadata as JSON
                "name": f"Video Ad - {file_path.split('/')[-1].split('.')[0]}"
            }
        }
        
        config = ad_config.get(ad_type, ad_config["text_ad"])
        
        ad = UserAds(
            user_id=user_id,
            ad_type=ad_type,
            file_path=file_path,
            name=config["name"],
            size=content_size,
            mime_type=config["mime_type"],
            tags=f"{ad_type},generated,draft",
            is_draft=True
        )
        
        self.db.add(ad)
        await self.db.commit()
        await self.db.refresh(ad)
        return ad
    
    async def _create_usage_log_draft(self, user_id: uuid.UUID, request: AdGenerationRequest, credit_cost: int, ad_id: uuid.UUID) -> UsageLog:
        """Create a usage log entry in draft mode"""
        usage_log = UsageLog(
            user_id=user_id,
            ad_type=request.ad_type,
            credits_used=credit_cost,
            source="preview_generation",
            is_draft=True,
            ad_id=ad_id,
            extra_data={
                "prompt": request.prompt,
                "target_audience": request.target_audience,
                "platform": request.platform,
                "additional_params": request.additional_params
            }
        )
        
        self.db.add(usage_log)
        await self.db.commit()
        await self.db.refresh(usage_log)
        return usage_log

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
    
    async def _create_user_ad(self, user_id: uuid.UUID, ad_type: str, file_path: str, generated_content: Dict[str, Any]) -> UserAds:
        """Create a user ad record with placeholder data"""
        
        # Calculate file size from content
        content_size = len(json.dumps(generated_content, indent=2).encode('utf-8'))
        
        ad_config = {
            "text_ad": {
                "mime_type": "application/json",
                "name": f"Text Ad - {file_path.split('/')[-1].split('.')[0]}"
            },
            "image_ad": {
                "mime_type": "application/json",  # For now, storing metadata as JSON
                "name": f"Image Ad - {file_path.split('/')[-1].split('.')[0]}"
            },
            "video_ad": {
                "mime_type": "application/json",  # For now, storing metadata as JSON
                "name": f"Video Ad - {file_path.split('/')[-1].split('.')[0]}"
            }
        }
        
        config = ad_config.get(ad_type, ad_config["text_ad"])
        
        ad = UserAds(
            user_id=user_id,
            ad_type=ad_type,
            file_path=file_path,
            name=config["name"],
            size=content_size,
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