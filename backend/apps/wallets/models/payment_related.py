from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from identity.models import SchoolProfile
from .payment import UUIDModel, TimeStampedModel, SoftDeleteModel
from .payment import (
    Payment, PaymentProvider, PaymentMethod, PaymentStatus, Currency)
from django.contrib.auth import get_user_model


User = get_user_model()


class Wallet(UUIDModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="wallet")

    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    currency = models.CharField(max_length=3, default="ZMW")

    is_active = models.BooleanField(default=True)

    # KYC
    kyc_level = models.CharField(max_length=20, default="BASIC")
    kyc_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet({self.user}) - {self.currency}"

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(balance__gte=0),
                name="wallet_balance_non_negative",
            )
        ]


class WalletPayoutAccount(models.Model):
    PROVIDER_CHOICES = (
        ("MTN_MOMO_ZMB", "MTN"),
        ("AIRTEL_OAPI_ZMB", "Airtel"),
        ("ZAMTEL_ZMB", "Zamtel"),
    )

    wallet = models.OneToOneField(
        Wallet, on_delete=models.CASCADE, related_name="payout_account"
    )

    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)

    phone_number = models.CharField(max_length=20)

    verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)


class WalletTransaction(UUIDModel):

    TRANSACTION_TYPE = (
        ("CASH_IN", "Cash In"),
        ("PAYOUT", "Payout"),
        ("REVERSAL", "Reversal"),
        ("FEE", "Fee"),
    )

    STATUS = (
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    )
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="transactions"
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    transaction_type = models.CharField(
        max_length=20, choices=TRANSACTION_TYPE)

    status = models.CharField(max_length=20, choices=STATUS, default="PENDING")

    # Link to Payment or Payout
    payment = models.ForeignKey(
        Payment, null=True, blank=True, on_delete=models.SET_NULL
    )
    # link to WalletTransaction (Payout)
    related_transaction = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="related_fees",
    )

    reference = models.CharField(max_length=100, unique=True)
    correlation_id = models.CharField(max_length=100, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_payouts",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"TXN - {self.transaction_type} - {self.amount}"


class WalletKYC(models.Model):

    ID_DOCUMENT_TYPE = (
        ("NRC", "National Registration Card"),
        ("PASSPORT", "Passport"),
        ("DRIVERS_LICENSE", "Drivers License"),
        ("VOTERS_CARD", "Voters Card"),
    )
    wallet = models.OneToOneField(
        Wallet, on_delete=models.CASCADE, related_name="kyc")
    id_document_type = models.CharField(
        max_length=20, choices=ID_DOCUMENT_TYPE)
    id_document_number = models.CharField(max_length=50)
    full_name = models.CharField(
        max_length=200, help_text="Name you want displayed on Invoices"
    )
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    id_document_copy = models.FileField(
        upload_to="kyc_ids/", blank=True, null=True)
    pacra_certificate_copy = models.FileField(
        upload_to="kyc_certificates/", blank=True, null=True
    )
    tax_certificate_copy = models.FileField(
        upload_to="kyc_certificates/", blank=True, null=True
    )
    bank_name = models.CharField(
        max_length=200, help_text="Prefered bank/mobile money to receive funds"
    )
    bank_account_name = models.CharField(
        max_length=200, help_text="Names on your bank account"
    )
    bank_account_number = models.CharField(
        max_length=200, help_text="Bank ot Mobile money account number"
    )

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ("verified",)
        return self.readonly_fields


class Customer(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """Model for storing customer information for our partners"""

    owner = models.ForeignKey(
        User,  # The user who owns this customer
        on_delete=models.CASCADE,
        related_name="customers",
    )
    user = models.ForeignKey(
        User,  # The user profile associated with this customer
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    external_id = models.CharField(
        max_length=255, db_index=True, null=True, blank=True)
    company = models.CharField(max_length=200, blank=True)

    # Billing address
    billing_address_line1 = models.CharField(max_length=255, blank=True)
    billing_address_line2 = models.CharField(max_length=255, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_country = models.CharField(max_length=2, blank=True)

    # Provider-specific customer IDs
    pawapay_customer_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    # Add other provider customer IDs as needed

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        indexes = [
            models.Index(fields=["external_id"]),
        ]

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Invoice(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """Customer model for storing customer information"""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="invoices",
        null=True,
        blank=True,
    )

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="platform_invoices",
        null=True,
        blank=True,
    )

    invoice_type = models.CharField(
        max_length=30,
        choices=[
            ("CUSTOMER", "Customer Invoice"),
            ("PLATFORM_FEE", "Platform Fee"),
        ],
        db_index=True,
        default="CUSTOMER",
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )

    amount = models.DecimalField(max_digits=20, decimal_places=2)

    # NEW: flat discount amount
    discount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
        help_text="Flat discount amount",
    )
    multiple_payers = models.BooleanField(default=False)

    remarks = models.CharField(
        max_length=500, help_text=_("Short Message to Payer"))
    created_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=50, choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )

    from django.core.exceptions import ValidationError

    def clean(self):
        # --- Basic invariants (always enforced) ---
        if self.invoice_type == "CUSTOMER" and not self.customer:
            raise ValidationError("Customer invoice must have a customer")

        if self.invoice_type == "PLATFORM_FEE" and not self.school:
            raise ValidationError("Platform fee invoice must have a school")

        # --- Creation-only constraint ---
        if not self.pk:  # object is being created
            if self.customer and self.school:
                raise ValidationError(
                    "Invoice cannot belong to both customer and school"
                )

        # --- Update constraint (extra safety) ---
        # if self.pk:
        #     original = type(self).objects.get(pk=self.pk)

        #     if original.customer != self.customer:
        #         raise ValidationError(
        # "Changing invoice customer is not allowed")

        #     if original.school != self.school:
        #         raise ValidationError(
        # "Changing invoice school is not allowed")

    def subtotal(self):
        """
        Returns the invoice amount after discount is applied.
        Ensures subtotal never goes below zero.
        """
        return max(self.amount - self.discount, Decimal("0.00"))

    def __str__(self):
        return f"Invoice {self.id} - {self.subtotal()}"


class PaymentMethodToken(UUIDModel, TimeStampedModel):
    """Store payment method tokens for recurring payments"""

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="payment_methods"
    )
    provider = models.CharField(max_length=30, choices=PaymentProvider.choices)
    payment_method = models.CharField(
        max_length=30, choices=PaymentMethod.choices)

    # Token information
    token = models.CharField(
        max_length=500, help_text=_("Payment method token from provider")
    )
    external_id = models.CharField(
        max_length=255, db_index=True, null=True, blank=True)

    # Card details (if applicable)
    card_brand = models.CharField(max_length=50, blank=True)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_exp_month = models.PositiveSmallIntegerField(null=True, blank=True)
    card_exp_year = models.PositiveSmallIntegerField(null=True, blank=True)

    # Digital wallet details
    wallet_type = models.CharField(max_length=50, blank=True)
    wallet_email = models.EmailField(blank=True)

    # Status
    is_default = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Security
    fingerprint = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Unique fingerprint for fraud detection"),
    )

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Payment Method Token")
        verbose_name_plural = _("Payment Method Tokens")
        unique_together = ["customer", "provider", "token"]
        indexes = [
            models.Index(fields=["customer", "is_default"]),
            models.Index(fields=["provider", "external_id"]),
        ]

    def __str__(self):
        return f"{self.get_payment_method_display()} - {self.customer.email}"


class PaymentAttempt(UUIDModel, TimeStampedModel):
    """Track individual payment attempts (useful for retries)"""

    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="attempts"
    )
    attempt_number = models.PositiveIntegerField(default=1)

    # Attempt details
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Currency.choices)
    payment_method_token = models.ForeignKey(
        PaymentMethodToken, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Status
    status = models.CharField(max_length=30, choices=PaymentStatus.choices)
    error_code = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)

    # Provider response
    provider_request = models.JSONField(default=dict, blank=True)
    provider_response = models.JSONField(default=dict, blank=True)
    provider_id = models.CharField(max_length=255, blank=True)

    # Timing
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Payment Attempt")
        verbose_name_plural = _("Payment Attempts")
        ordering = ["-created_at"]

    @property
    def duration(self):
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class Refund(UUIDModel, TimeStampedModel):
    """Track refunds separately for detailed reporting"""

    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="refund_records"
    )

    # Refund details
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Currency.choices)
    reason = models.TextField(blank=True)

    # Status
    status = models.CharField(
        max_length=30,
        choices=[
            ("pending", _("Pending")),
            ("succeeded", _("Succeeded")),
            ("failed", _("Failed")),
            ("cancelled", _("Cancelled")),
        ],
        default="pending",
    )

    # Provider information
    provider = models.CharField(max_length=30, choices=PaymentProvider.choices)
    external_id = models.CharField(max_length=255, db_index=True, blank=True)
    provider_data = models.JSONField(default=dict, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Refund")
        verbose_name_plural = _("Refunds")
        indexes = [
            models.Index(fields=["payment", "status"]),
            models.Index(fields=["external_id", "provider"]),
        ]

    def __str__(self):
        return f"Refund {self.amount} {self.currency}\
              for {self.payment.reference}"


class Dispute(UUIDModel, TimeStampedModel):
    """Track payment disputes/chargebacks"""

    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="disputes"
    )

    # Dispute details
    external_id = models.CharField(max_length=255, db_index=True)
    reason = models.CharField(max_length=200)
    status = models.CharField(
        max_length=30,
        choices=[
            ("warning_needs_response", _("Warning Needs Response")),
            ("needs_response", _("Needs Response")),
            ("under_review", _("Under Review")),
            ("won", _("Won")),
            ("lost", _("Lost")),
            ("charge_refunded", _("Charge Refunded")),
        ],
    )
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Currency.choices)

    # Dates
    initiated_at = models.DateTimeField()
    due_by = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Evidence and communication
    evidence = models.JSONField(default=dict, blank=True)
    communication = models.JSONField(default=dict, blank=True)

    # Provider data
    provider = models.CharField(max_length=30, choices=PaymentProvider.choices)
    provider_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Dispute")
        verbose_name_plural = _("Disputes")
        indexes = [
            models.Index(fields=["payment", "status"]),
            models.Index(fields=["external_id", "provider"]),
        ]


class WebhookEventType(models.TextChoices):
    DEPOSIT_INITIATED = "deposit.initiated"
    DEPOSIT_ACCEPTED = "deposit.accepted"
    DEPOSIT_COMPLETED = "deposit.completed"
    DEPOSIT_FAILED = "deposit.failed"
    DEPOSIT_CALLBACK_RECEIVED = "deposit.callback_received"


class PaymentWebhookLog(UUIDModel, TimeStampedModel):
    """Log webhook events from payment providers"""

    provider = models.CharField(max_length=30, choices=PaymentProvider.choices)
    event_type = models.CharField(
        max_length=200,
        db_index=True,
        choices=WebhookEventType,
        default=WebhookEventType.DEPOSIT_ACCEPTED,
    )
    external_id = models.CharField(max_length=255, db_index=True, blank=True)

    # Payload
    raw_payload = models.TextField(help_text=_("Raw webhook payload"))
    parsed_payload = models.JSONField(default=dict, blank=True)

    # Headers
    headers = models.JSONField(default=dict, blank=True)

    # Processing status
    status = models.CharField(
        max_length=20,
        choices=[
            ("received", _("Received")),
            ("processing", _("Processing")),
            ("processed", _("Processed")),
            ("failed", _("Failed")),
            ("ignored", _("Ignored")),
        ],
        default="received",
    )
    error_message = models.TextField(blank=True)

    # Related payment
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="webhook_logs",
    )

    # Processing metadata
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_time_ms = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = _("Payment Webhook Log")
        verbose_name_plural = _("Payment Webhook Logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["provider", "event_type"]),
            models.Index(fields=["created_at", "status"]),
            models.Index(fields=["payment", "created_at"]),
        ]

    def __str__(self):
        return f"{self.provider} - {self.event_type} - {self.status}"
