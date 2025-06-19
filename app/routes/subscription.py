import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import User, get_current_user
from app.config import settings
from app.database import get_db
from app.schemas import (
    InitSubscriptionRequest,
    InitSubscriptionResponse,
    ProfileCreate,
    ProfileUpdate,
)
from app.services import CreditsService, ProfileService, StripeService

router = APIRouter()

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