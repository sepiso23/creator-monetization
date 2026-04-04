from celery import shared_task
from apps.wallets.models import Wallet
from apps.payments.services.payout_orchestrator import PayoutOrchestrator
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def auto_payout_wallets():
    # get superuser
    system_user = User.objects.filter(is_superuser=True).first()
    for wallet in Wallet.objects.filter(balance__gt=0, is_verified=True):
        PayoutOrchestrator.initiate_payout(
            wallet=wallet,
            initiated_by=system_user,  # System initiated
        )


@shared_task
def send_missing_payout_account_email_task(wallet_id):
    """
    Async task to send an email to the wallet owner/creator requesting 
    them to set up a payout account.
    
    Args:
        wallet_id (UUID): The wallet id
    """
    try:
        wallet = Wallet.objects.get(id=wallet_id)
        creator_user = wallet.creator.user
        subject = "Action Required: Set Up Your Payout Account"
        
        message = f"""
Hello {creator_user.first_name or creator_user.username},

We are writing to inform you that an administrator is attempting to process a payout
for your account.
However, we were unable to complete the payout because you have not yet set up a payout account.

To receive your earnings, please:
1. Log into your creator dashboard
2. Navigate to your wallet settings
3. Add your payout account details (mobile money provider, account name, and phone number)

Once you've set up your payout account, the admin can proceed with the payout.

If you have any questions or need assistance, please don't hesitate to contact our support team.

Best regards,
TipZed Admin Team
        """
        
        html_message = f"""
<html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>Action Required: Set Up Your Payout Account</h2>
            
            <p>Hello {creator_user.first_name or creator_user.username},</p>
            
            <p>We are writing to inform you that an administrator is attempting to process a payout for your account.
            However, we were unable to complete the payout because you have not yet set up a payout account.</p>
            
            <h3>To receive your earnings, please:</h3>
            <ol>
                <li>Log into your creator dashboard</li>
                <li>Navigate to your wallet settings</li>
                <li>Add your payout account details (mobile money provider, account name, and phone number)</li>
            </ol>
            
            <p>Once you've set up your payout account, the admin can proceed with the payout.</p>
            
            <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
            
            <p style="margin-top: 30px; color: #666;">
                Best regards,<br>
                <strong>TipZed Admin Team</strong>
            </p>
        </div>
    </body>
</html>
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@tipzed.space',
            recipient_list=[creator_user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Successfully sent payout account setup email to {creator_user.email}")
        
    except Wallet.DoesNotExist:
        logger.error(f"Wallet with id {wallet_id} not found")
    except Exception as e:
        logger.error(f"Failed to send payout account email for wallet {wallet_id}: {str(e)}")
        raise

