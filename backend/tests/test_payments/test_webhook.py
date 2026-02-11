import json
import pytest
import uuid
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from apps.payments.models import Payment, PaymentWebhookLog
from apps.wallets.models import Wallet, WalletTransaction
from tests.factories import PaymentFactory

User = get_user_model()


@pytest.mark.django_db
class TestPaymentWebhookView:

    def test_completed_deposit_credits_wallet(self, api_client, payment_factory):
        """Test that a completed deposit callback credits the wallet
        and records transactions"""
        payment = payment_factory()
        wallet = payment.wallet

        payload = {
            "depositId": str(payment.id),
            "status": "COMPLETED",
            "amount": payment.amount,
            "providerTransactionId": "ABC123",
        }

        response = api_client.post(
            reverse("payments:webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        wallet.refresh_from_db()
        assert wallet.balance == payment.amount
        assert WalletTransaction.objects.filter(
            wallet=wallet, transaction_type="CASH_IN"
        ).exists()
        assert WalletTransaction.objects.filter(
            wallet=wallet, transaction_type="FEE"
        ).exists()
        assert not WalletTransaction.objects.filter(
            wallet=wallet, transaction_type="PAYOUT"
        ).exists()
        assert PaymentWebhookLog.objects.filter(
            payment=payment,
            provider="pawapay",
            external_id="ABC123",
            event_type="deposit.completed",
        ).exists()
        assert PaymentWebhookLog.objects.filter(
            payment=payment,
            provider="pawapay",
            external_id="ABC123",
            event_type="deposit.completed",
        ).first().parsed_payload["amount"] == str(payment.amount)
        assert (
            PaymentWebhookLog.objects.filter(
                payment=payment,
                provider="pawapay",
                external_id="ABC123",
                event_type="deposit.completed",
            )
            .first()
            .parsed_payload["currency"]
            == "ZMW"
        )
        # Check Wallet Transaction and wallet reference same payment
        cash_in_tx = WalletTransaction.objects.filter(
            wallet=wallet, transaction_type="CASH_IN"
        ).first()
        assert cash_in_tx is not None
        assert cash_in_tx.payment == payment

    def test_deposit_callback_is_idempotent_requests(self, api_client, user, wallet):
        deposit_id = uuid.uuid4()

        payment = PaymentFactory(
            id=deposit_id,
            user=user,
            wallet=wallet,
            amount=Decimal("20.00"),
        )

        payload = {
            "depositId": str(deposit_id),
            "status": "COMPLETED",
            "providerTransactionId": "DUPLICATE-TXN",
        }

        request_payload = json.dumps(payload)
        response1 = api_client.post(
            reverse("payments:webhook"),
            data=request_payload,
            content_type="application/json",
        )
        response2 = api_client.post(
            reverse("payments:webhook"),
            data=request_payload,
            content_type="application/json",
        )

        wallet.refresh_from_db()

        # Expect idempotent handling: wallet credited once, fee applied once
        assert wallet.balance == Decimal("19.4")
        assert payment.amount == Decimal("20")
        assert (
            WalletTransaction.objects.filter(
                wallet=wallet, transaction_type="CASH_IN"
            ).count()
            == 1
        )
        assert (
            WalletTransaction.objects.filter(
                wallet=wallet, transaction_type="FEE"
            ).count()
            == 1
        )
        assert (
            WalletTransaction.objects.filter(
                wallet=wallet, transaction_type="PAYOUT"
            ).count()
            == 0
        )
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_pending_deposit_does_not_credit_wallet(self, api_client, user, wallet):
        deposit_id = uuid.uuid4()

        PaymentFactory(
            id=deposit_id,
            user=user,
            wallet=wallet,
            amount=Decimal("10.00"),
        )

        payload = {
            "depositId": str(deposit_id),
            "status": "PENDING",
            "providerTransactionId": "PENDING-TXN",
        }

        response = api_client.post(
            reverse("payments:webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        wallet.refresh_from_db()
        assert response.status_code == 200
        assert wallet.balance == Decimal("0.00")
        assert not WalletTransaction.objects.exists()

    def test_deposit_callback_updates_payment_failed(self, api_client):
        deposit_id = uuid.uuid4()
        payment = PaymentFactory(
            id=deposit_id,
            provider="pawapay",
            isp_provider="AIRTEL_OAPI_ZMB",
            customer_phone="260700111222",
            amount=10,
            status="accepted",
        )

        payload = {
            "depositId": str(deposit_id),
            "status": "FAILED",
            "amount": "10",
            "currency": "ZMW",
            "country": "ZMB",
            "payer": {
                "type": "MMO",
                "accountDetails": {
                    "phoneNumber": "260763456789",
                    "provider": "MTN_MOMO_ZMB",
                },
            },
            "created": "2020-02-21T17:32:29Z",
            "customerMessage": "Note of 4 to 22 chars",
            "providerTransactionId": "ABC123",
            "failureReason": {
                "failureCode": "INSUFFICIENT_BALANCE",
                "failureMessage": "The customer does not have enough funds to complete this payment.",
            },
        }

        response = api_client.post(
            reverse("payments:webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200

        payment.refresh_from_db()
        assert payment.status == "failed"

        webhook = PaymentWebhookLog.objects.all().first()
        assert webhook is not None
        assert webhook.payment == payment
        assert webhook.provider == "pawapay"
        assert webhook.external_id == "ABC123"
        assert webhook.event_type == "deposit.failed"
        assert "failureCode" in webhook.parsed_payload["failureReason"]
        assert "failureMessage" in webhook.parsed_payload["failureReason"]
        assert (
            webhook.parsed_payload["failureReason"]["failureCode"]
            == "INSUFFICIENT_BALANCE"
        )

    def test_deposit_callback_is_idempotent_duplicate(self, api_client):
        """Check the endpoint handles duplicate requests correctly"""
        deposit_id = uuid.uuid4()
        payment = PaymentFactory(
            id=deposit_id,
            provider="pawapay",
            isp_provider="MTN_MOMO_ZMB",
            customer_phone="260700111222",
            amount=10,
            status="accepted",
        )

        payload = {
            "depositId": str(deposit_id),
            "status": "COMPLETED",
            "amount": "10",
            "currency": "ZMW",
            "country": "ZMB",
            "payer": {
                "type": "MMO",
                "accountDetails": {
                    "phoneNumber": "260763456789",
                    "provider": "MTN_MOMO_ZMB",
                },
            },
            "created": "2020-02-21T17:32:29Z",
            "customerMessage": "Note of 4 to 22 chars",
            "providerTransactionId": "ABC123",
        }

        request_payload = json.dumps(payload)

        response1 = api_client.post(
            reverse("payments:webhook"),
            data=request_payload,
            content_type="application/json",
        )
        assert response1.status_code == 200

        payment.refresh_from_db()
        assert payment.status == "completed"

        # Check webhook saved once
        webhooks = PaymentWebhookLog.objects.all()
        assert webhooks.count() == 1

        # duplicate callback
        response2 = api_client.post(
            reverse("payments:webhook"),
            data=request_payload,
            content_type="application/json",
        )
        assert response2.status_code == 200
        assert "Duplicate callback ignored" in response2.content.decode("utf-8")
        assert webhooks.count() == 1
        payment.refresh_from_db()
        assert payment.status == "completed"

    def test_webhook_rejects_non_post(self, api_client):
        response = api_client.get(reverse("payments:webhook"))
        assert response.status_code == 405 or response.status_code == 400

    def test_rejected_deposit_does_not_credit_wallet(self, api_client, user, wallet):
        """Test that rejected deposits don't credit wallet"""
        deposit_id = uuid.uuid4()
        payment = PaymentFactory(
            id=deposit_id,
            user=user,
            wallet=wallet,
            amount=Decimal("50.00"),
        )

        payload = {
            "depositId": str(deposit_id),
            "status": "REJECTED",
            "providerTransactionId": "REJECTED-TXN",
        }

        response = api_client.post(
            reverse("payments:webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200

        wallet.refresh_from_db()
        assert wallet.balance == Decimal("0.00")
        payment.refresh_from_db()
        assert payment.status == "rejected"

    def test_callback_with_different_isp_providers(self, api_client, user, wallet):
        """Test callbacks for different ISP providers"""
        providers = ["MTN_MOMO_ZMB", "AIRTEL_OAPI_ZMB", "ZAMTEL_ZMB"]

        for provider in providers:
            deposit_id = uuid.uuid4()
            payment = PaymentFactory(
                id=deposit_id,
                user=user,
                wallet=wallet,
                provider="pawapay",
                isp_provider=provider,
                customer_phone="260700111222",
                amount=Decimal("10.00"),
            )

            payload = {
                "depositId": str(deposit_id),
                "status": "COMPLETED",
                "providerTransactionId": f"TXN-{provider}",
            }

            response = api_client.post(
                reverse("payments:webhook"),
                data=json.dumps(payload),
                content_type="application/json",
            )
            assert response.status_code == 200

            payment.refresh_from_db()
            assert payment.status == "completed"

    def test_callback_fee_deduction_accuracy(self, api_client):
        """Test that fee deduction is accurate for different amounts"""
        test_cases = [
            (Decimal("100.00"), Decimal("97.00")),  # 3% fee = 3
            (Decimal("50.00"), Decimal("48.50")),  # 3% fee = 1.50
            (Decimal("1000.00"), Decimal("970.00")),  # 3% fee = 30
        ]

        for idx, (amount, expected_balance) in enumerate(test_cases):
            user = User.objects.create_user(
                email=f"test{idx}@user.io", password="testpass"
            )
            wallet = Wallet.objects.create(user=user, balance=Decimal("0.00"))

            deposit_id = uuid.uuid4()
            PaymentFactory(
                id=deposit_id,
                user=user,
                wallet=wallet,
                amount=amount,
            )

            payload = {
                "depositId": str(deposit_id),
                "status": "COMPLETED",
                "providerTransactionId": f"TXN-{amount}",
            }

            response = api_client.post(
                reverse("payments:webhook"),
                data=json.dumps(payload),
                content_type="application/json",
            )
            assert response.status_code == 200

            wallet.refresh_from_db()
            assert wallet.balance == expected_balance
            user.delete()

    def test_callback_invalid_json(self, api_client):
        """Test callback with invalid JSON"""
        response = api_client.post(
            reverse("payments:webhook"),
            data="invalid json",
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_callback_missing_deposit_id(self, api_client):
        """Test callback with missing depositId"""
        payload = {
            "status": "COMPLETED",
            "providerTransactionId": "ABC123",
        }

        response = api_client.post(
            reverse("payments:webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_callback_payment_not_found(self, api_client):
        """Test callback when payment doesn't exist"""
        non_existent_id = uuid.uuid4()
        payload = {
            "depositId": str(non_existent_id),
            "status": "COMPLETED",
            "providerTransactionId": "ABC123",
        }

        response = api_client.post(
            reverse("payments:webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_callback_without_wallet(self, api_client, user):
        """Test completed callback for payment without wallet"""
        deposit_id = uuid.uuid4()
        PaymentFactory(
            id=deposit_id,
            user=user,
            wallet=None,  # No wallet
            amount=Decimal("10.00"),
        )

        payload = {
            "depositId": str(deposit_id),
            "status": "COMPLETED",
            "providerTransactionId": "ABC123",
        }

        response = api_client.post(
            reverse("payments:webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code in (200, 400)

    def test_webhook_logs_all_fields(self, api_client):
        """Test that webhook logs capture all payload fields"""
        deposit_id = uuid.uuid4()
        PaymentFactory(
            id=deposit_id,
            provider="pawapay",
            amount=100,
        )

        payload = {
            "depositId": str(deposit_id),
            "status": "COMPLETED",
            "amount": "100",
            "currency": "ZMW",
            "country": "ZMB",
            "payer": {
                "type": "MMO",
                "accountDetails": {
                    "phoneNumber": "260763456789",
                    "provider": "MTN_MOMO_ZMB",
                },
            },
            "created": "2020-02-21T17:32:29Z",
            "customerMessage": "Test message",
            "providerTransactionId": "EXT-123",
        }

        response = api_client.post(
            reverse("payments:webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200

        webhook = PaymentWebhookLog.objects.first()
        assert webhook is not None
        assert webhook.parsed_payload["country"] == "ZMB"
        assert (
            webhook.parsed_payload["payer"]["accountDetails"]["provider"]
            == "MTN_MOMO_ZMB"
        )

    def test_multiple_callbacks_same_payment(self, api_client, user, wallet):
        """Test multiple callbacks for same payment with different statuses"""
        deposit_id = uuid.uuid4()
        payment = PaymentFactory(
            id=deposit_id,
            user=user,
            wallet=wallet,
            amount=Decimal("100.00"),
            status="accepted",
        )

        # First callback - PENDING
        payload_pending = {
            "depositId": str(deposit_id),
            "status": "PENDING",
            "providerTransactionId": "TXN-PENDING",
        }

        response = api_client.post(
            reverse("payments:webhook"),
            data=json.dumps(payload_pending),
            content_type="application/json",
        )
        assert response.status_code == 200

        payment.refresh_from_db()
        assert payment.status == "accepted"  # Status remains accepted
        wallet.refresh_from_db()
        assert wallet.balance == Decimal("0.00")

        # Second callback - COMPLETED
        payload_completed = {
            "depositId": str(deposit_id),
            "status": "COMPLETED",
            "providerTransactionId": "TXN-COMPLETED",
        }
        response = api_client.post(
            reverse("payments:webhook"),
            data=json.dumps(payload_completed),
            content_type="application/json",
        )
        assert response.status_code == 200

        payment.refresh_from_db()
        assert payment.status == "completed"
        wallet.refresh_from_db()
        assert wallet.balance == Decimal("97.00")

    def test_callback_with_large_amount(self, api_client, user, wallet):
        """Test callback with large payment amount"""
        from lipila.services.fee_service import FeeService

        deposit_id = uuid.uuid4()
        large_amount = Decimal("999999.99")

        PaymentFactory(
            id=deposit_id,
            user=user,
            wallet=wallet,
            amount=large_amount,
        )

        payload = {
            "depositId": str(deposit_id),
            "status": "COMPLETED",
            "providerTransactionId": "LARGE-TXN",
        }

        response = api_client.post(
            reverse("payments:webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200

        wallet.refresh_from_db()
        fee = FeeService.calculate_cash_in_fee(large_amount)
        expected_balance = large_amount - fee
        assert wallet.balance == expected_balance

    def test_callback_transaction_atomicity(self, api_client, user, wallet):
        """Test that callback transaction is atomic"""
        deposit_id = uuid.uuid4()
        PaymentFactory(
            id=deposit_id,
            user=user,
            wallet=wallet,
            amount=Decimal("100.00"),
        )

        payload = {
            "depositId": str(deposit_id),
            "status": "COMPLETED",
            "providerTransactionId": "ATOMIC-TXN",
        }

        initial_tx_count = WalletTransaction.objects.count()
        response = api_client.post(
            reverse("payments:webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        final_tx_count = WalletTransaction.objects.count()

        assert response.status_code == 200
        assert final_tx_count > initial_tx_count

        cash_in_txs = WalletTransaction.objects.filter(transaction_type="CASH_IN")
        fee_txs = WalletTransaction.objects.filter(transaction_type="FEE")
        assert cash_in_txs.count() == 1
        assert fee_txs.count() == 1

    def test_callback_with_special_characters_in_message(self, api_client):
        """Test callback with special characters in messages"""
        deposit_id = uuid.uuid4()
        PaymentFactory(
            id=deposit_id,
            provider="pawapay",
            amount=50,
        )

        payload = {
            "depositId": str(deposit_id),
            "status": "COMPLETED",
            "providerTransactionId": "ABC123",
            "customerMessage": "Payment for services & fees - Invoice #123",
        }

        response = api_client.post(
            reverse("payments:webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200

        webhook = PaymentWebhookLog.objects.first()
        assert webhook is not None
        assert "Invoice #123" in webhook.parsed_payload.get("customerMessage", "")
