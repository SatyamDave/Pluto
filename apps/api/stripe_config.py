"""
Stripe Configuration and Webhook Handler
Handles Stripe integration for subscription management
"""

import stripe
import os
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Stripe Product IDs (test mode)
STRIPE_PRODUCTS = {
    "learner": "prod_learner_free",
    "pro": "prod_pro_monthly",
    "quant": "prod_quant_monthly", 
    "enterprise": "prod_enterprise_monthly"
}

# Stripe Price IDs (test mode)
STRIPE_PRICES = {
    "learner": "price_learner_free",
    "pro": "price_pro_29_monthly",
    "quant": "price_quant_99_monthly",
    "enterprise": "price_enterprise_custom"
}

class StripeManager:
    def __init__(self):
        self.stripe = stripe
        
    def create_customer(self, email: str, name: str = None) -> str:
        """Create a Stripe customer"""
        try:
            customer = self.stripe.Customer.create(
                email=email,
                name=name,
                metadata={"source": "ai-market-terminal"}
            )
            return customer.id
        except Exception as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise HTTPException(status_code=500, detail="Failed to create customer")
    
    def create_checkout_session(self, customer_id: str, tier: str, success_url: str, cancel_url: str) -> str:
        """Create a Stripe checkout session"""
        try:
            if tier == "learner":
                # Free tier - create a subscription with $0 price
                session = self.stripe.checkout.Session.create(
                    customer=customer_id,
                    payment_method_types=['card'],
                    line_items=[{
                        'price': STRIPE_PRICES[tier],
                        'quantity': 1,
                    }],
                    mode='subscription',
                    success_url=success_url,
                    cancel_url=cancel_url,
                    metadata={"tier": tier}
                )
            else:
                # Paid tiers
                session = self.stripe.checkout.Session.create(
                    customer=customer_id,
                    payment_method_types=['card'],
                    line_items=[{
                        'price': STRIPE_PRICES[tier],
                        'quantity': 1,
                    }],
                    mode='subscription',
                    success_url=success_url,
                    cancel_url=cancel_url,
                    metadata={"tier": tier}
                )
            
            return session.id
        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise HTTPException(status_code=500, detail="Failed to create checkout session")
    
    def create_customer_portal_session(self, customer_id: str, return_url: str) -> str:
        """Create a customer portal session"""
        try:
            session = self.stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session.url
        except Exception as e:
            logger.error(f"Failed to create portal session: {e}")
            raise HTTPException(status_code=500, detail="Failed to create portal session")
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription details"""
        try:
            subscription = self.stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "items": [
                    {
                        "price_id": item.price.id,
                        "quantity": item.quantity
                    } for item in subscription.items.data
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get subscription: {e}")
            return None
    
    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> bool:
        """Cancel a subscription"""
        try:
            if at_period_end:
                self.stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                self.stripe.Subscription.cancel(subscription_id)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False
    
    def handle_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event = self.stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            # Handle the event
            if event['type'] == 'checkout.session.completed':
                return self._handle_checkout_completed(event['data']['object'])
            elif event['type'] == 'customer.subscription.created':
                return self._handle_subscription_created(event['data']['object'])
            elif event['type'] == 'customer.subscription.updated':
                return self._handle_subscription_updated(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                return self._handle_payment_succeeded(event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                return self._handle_payment_failed(event['data']['object'])
            else:
                logger.info(f"Unhandled event type: {event['type']}")
                return {"status": "ignored", "event_type": event['type']}
                
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            raise HTTPException(status_code=500, detail="Webhook error")
    
    def _handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle checkout.session.completed event"""
        customer_id = session['customer']
        subscription_id = session.get('subscription')
        tier = session['metadata'].get('tier', 'learner')
        
        logger.info(f"Checkout completed for customer {customer_id}, tier: {tier}")
        
        # Update user tier in database
        # This would typically update the user's subscription status
        return {
            "status": "processed",
            "event_type": "checkout.session.completed",
            "customer_id": customer_id,
            "subscription_id": subscription_id,
            "tier": tier
        }
    
    def _handle_subscription_created(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.subscription.created event"""
        subscription_id = subscription['id']
        customer_id = subscription['customer']
        status = subscription['status']
        
        logger.info(f"Subscription created: {subscription_id} for customer {customer_id}")
        
        return {
            "status": "processed",
            "event_type": "customer.subscription.created",
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "status": status
        }
    
    def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.subscription.updated event"""
        subscription_id = subscription['id']
        status = subscription['status']
        
        logger.info(f"Subscription updated: {subscription_id}, status: {status}")
        
        return {
            "status": "processed",
            "event_type": "customer.subscription.updated",
            "subscription_id": subscription_id,
            "status": status
        }
    
    def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.subscription.deleted event"""
        subscription_id = subscription['id']
        
        logger.info(f"Subscription deleted: {subscription_id}")
        
        return {
            "status": "processed",
            "event_type": "customer.subscription.deleted",
            "subscription_id": subscription_id
        }
    
    def _handle_payment_succeeded(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_succeeded event"""
        invoice_id = invoice['id']
        subscription_id = invoice.get('subscription')
        
        logger.info(f"Payment succeeded for invoice {invoice_id}")
        
        return {
            "status": "processed",
            "event_type": "invoice.payment_succeeded",
            "invoice_id": invoice_id,
            "subscription_id": subscription_id
        }
    
    def _handle_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_failed event"""
        invoice_id = invoice['id']
        subscription_id = invoice.get('subscription')
        
        logger.warning(f"Payment failed for invoice {invoice_id}")
        
        return {
            "status": "processed",
            "event_type": "invoice.payment_failed",
            "invoice_id": invoice_id,
            "subscription_id": subscription_id
        }

# Global Stripe manager instance
stripe_manager = StripeManager()
