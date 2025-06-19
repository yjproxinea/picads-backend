from typing import Optional

import stripe

from app.config import STRIPE_SECRET_KEY, settings

# Configure Stripe
stripe.api_key = STRIPE_SECRET_KEY


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