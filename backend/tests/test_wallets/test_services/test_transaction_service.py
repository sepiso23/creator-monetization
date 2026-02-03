from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from lipila.models.payment_related import Wallet, WalletTransaction
from lipila.services.wallet_service import WalletService
from lipila.services.transaction_service import WalletTransactionService
from lipila.exceptions import (
    InsufficientBalance,
    DuplicateTransaction,
    InvalidTransaction,
)

User = get_user_model()


class WalletServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com", password="pass123")
        self.wallet = Wallet.objects.create(
            user=self.user, balance=Decimal("0.00"))
        # Assumet Wallet is Verified
        self.wallet.kyc.verified = True
        self.wallet.kyc.save()

    def test_wallet_balance_matches_transactions(self):
        WalletTransactionService.cash_in(
            wallet=self.wallet,
            amount=Decimal("5.00"), payment=None, reference="A"
        )

        WalletTransactionService.cash_in(
            wallet=self.wallet,
            amount=Decimal("15.00"), payment=None, reference="B"
        )

        WalletTransactionService.payout(
            wallet=self.wallet, amount=Decimal("3.00"), correlation_id="C"
        )

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("9.4"))

    def test_get_wallet_for_user(self):
        wallet = WalletService.get_wallet_for_user(self.user)
        self.assertEqual(wallet, self.wallet)

    def test_recalculate_wallet_balance(self):
        WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("10.00"),
            transaction_type="CASH_IN",
            status="COMPLETED",
            reference="TX1",
        )
        WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("-3.00"),
            transaction_type="PAYOUT",
            status="COMPLETED",
            reference="TX2",
        )

        WalletService.recalculate_wallet_balance(self.wallet)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("7.00"))

    def test_cash_in_creates_transaction_and_updates_balance(self):
        tx = WalletTransactionService.cash_in(
            wallet=self.wallet,
            amount=Decimal("20.00"),
            payment=None,
            reference="CASHIN-1",
        )

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("19.4"))
        self.assertEqual(tx.transaction_type, "CASH_IN")
        self.assertEqual(tx.status, "COMPLETED")

    def test_payout_transaction_reduces_balance(self):
        # First cash-in
        WalletTransactionService.cash_in(
            wallet=self.wallet,
            amount=Decimal("50.00"),
            payment=None,
            reference="CASHIN-2",
        )

        # Payout
        tx = WalletTransactionService.payout(
            wallet=self.wallet,
            amount=Decimal("30.00"), correlation_id="PAYOUT-1"
        )

        self.assertEqual(tx.amount, Decimal("-30.00"))
        self.assertEqual(tx.status, "PENDING")

    def test_payout_raises_insufficient_balance(self):
        with self.assertRaises(InsufficientBalance):
            WalletTransactionService.payout(
                wallet=self.wallet,
                amount=Decimal("10.00"),
                correlation_id="PAYOUT-FAIL",
            )

    def test_duplicate_transaction_raises(self):
        WalletTransactionService.cash_in(
            wallet=self.wallet,
            amount=Decimal("10.00"), payment=None, reference="DUP-1"
        )

        with self.assertRaises(DuplicateTransaction):
            WalletTransactionService.cash_in(
                wallet=self.wallet,
                amount=Decimal("10.00"),
                payment=None,
                reference="DUP-1",
            )

    def test_finalize_payout_completes_and_updates_balance(self):
        WalletTransactionService.cash_in(
            wallet=self.wallet,
            amount=Decimal("50.00"),
            payment=None,
            reference="CASHIN-3",
        )

        payout_tx = WalletTransactionService.payout(
            wallet=self.wallet,
            amount=Decimal("30.00"), correlation_id="PAYOUT-2"
        )

        WalletTransactionService.finalize_payout(
            payout_tx=payout_tx, success=True)

        self.wallet.refresh_from_db()
        # cashin(50 - 3%) - cashout(k30) - fee(k10)= 8.5
        self.assertEqual(
            self.wallet.balance, Decimal("8.5")
        )  # after cashin  7 cashout fee

        payout_tx.refresh_from_db()
        self.assertEqual(payout_tx.status, "COMPLETED")

    def test_finalize_failed_payout_updates_status_but_not_balance(self):
        WalletTransactionService.cash_in(
            wallet=self.wallet,
            amount=Decimal("40.00"),
            payment=None,
            reference="CASHIN-4",
        )

        payout_tx = WalletTransactionService.payout(
            wallet=self.wallet,
            amount=Decimal("25.00"), correlation_id="PAYOUT-3"
        )

        WalletTransactionService.finalize_payout(
            payout_tx=payout_tx, success=False)

        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance, Decimal("38.8")
        )  # after fee deduction no payout fee

        payout_tx.refresh_from_db()
        self.assertEqual(payout_tx.status, "FAILED")

    def test_cash_in_creates_fee_transaction(self):
        tx = WalletTransactionService.cash_in(
            wallet=self.wallet,
            amount=Decimal("20.00"),
            payment=None,
            reference="CASHIN-FEE-1",
        )

        fee_tx = WalletTransaction.objects.get(
            related_transaction=tx, transaction_type="FEE"
        )

        self.assertEqual(fee_tx.amount, Decimal("-0.60"))  # 3% fee
        fees = tx.related_fees.all()
        self.assertEqual(fees.count(), 1)
        self.assertEqual(tx.wallet.balance, Decimal("19.4"))

    def test_payout_creates_single_fee(self):
        WalletTransactionService.cash_in(
            wallet=self.wallet,
            amount=Decimal("100.00"),
            payment=None,
            reference="CASHIN-PAYOUT-FEE",
        )

        payout_tx = WalletTransactionService.payout(
            wallet=self.wallet,
            amount=Decimal("30.00"),
            correlation_id="PAYOUT-FEE-TEST",
        )

        fees = payout_tx.related_fees.all()
        self.assertEqual(fees.count(), 1)

    def test_finalize_payout_is_idempotent(self):
        WalletTransactionService.cash_in(
            wallet=self.wallet,
            amount=Decimal("50.00"),
            payment=None,
            reference="CASHIN-IDEMP",
        )

        payout_tx = WalletTransactionService.payout(
            wallet=self.wallet,
            amount=Decimal("20.00"), correlation_id="PAYOUT-IDEMP"
        )

        WalletTransactionService.finalize_payout(
            payout_tx=payout_tx, success=True)
        self.wallet.refresh_from_db()
        balance_after_first = self.wallet.balance

        WalletTransactionService.finalize_payout(
            payout_tx=payout_tx, success=True)
        self.wallet.refresh_from_db()

        self.assertEqual(self.wallet.balance, balance_after_first)

    def test_failed_payout_creates_fee_reversal(self):
        WalletTransactionService.cash_in(
            wallet=self.wallet,
            amount=Decimal("40.00"),
            payment=None,
            reference="CASHIN-REVERSAL",
        )

        payout_tx = WalletTransactionService.payout(
            wallet=self.wallet,
            amount=Decimal("20.00"),
            correlation_id="PAYOUT-REVERSAL",
        )

        WalletTransactionService.finalize_payout(
            payout_tx=payout_tx, success=False)

        fee_tx = payout_tx.related_fees.first()
        reversal = WalletTransaction.objects.get(
            related_transaction=fee_tx, transaction_type="FEE_REVERSAL"
        )

        self.assertEqual(reversal.amount, abs(fee_tx.amount))

    def test_cash_in_zero_amount_fails(self):
        with self.assertRaises(InvalidTransaction):
            WalletTransactionService.cash_in(
                wallet=self.wallet,
                amount=Decimal("0.00"),
                payment=None,
                reference="ZERO",
            )

    def test_payout_negative_amount_fails(self):
        with self.assertRaises(InvalidTransaction):
            WalletTransactionService.payout(
                wallet=self.wallet,
                amount=Decimal("-5.00"), correlation_id="NEGATIVE"
            )

    def test_finalize_non_payout_raises(self):
        tx = WalletTransactionService.cash_in(
            wallet=self.wallet,
            amount=Decimal("10.00"),
            payment=None,
            reference="CASHIN-NOT-PAYOUT",
        )

        with self.assertRaises(Exception):
            WalletTransactionService.finalize_payout(
                payout_tx=tx, success=True)

    def test_wallet_balance_never_negative(self):
        WalletTransactionService.cash_in(
            wallet=self.wallet,
            amount=Decimal("20.00"), payment=None, reference="SAFE"
        )

        self.wallet.refresh_from_db()
        self.assertGreaterEqual(self.wallet.balance, Decimal("0.00"))