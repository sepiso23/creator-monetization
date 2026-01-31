from identity.decorators import custom_login_required, admin_role_required
from django.db.models import Sum, Q
from django.shortcuts import render, redirect
from lipila.models.payment_related import WalletTransaction, Wallet, Invoice
from lipila.forms import WalletKYCForm
from lipila.utils.utils import pawapay_request
from apps.wallets.services.transaction_service import WalletTransactionService
from lipila.exceptions import DuplicateTransaction
from lipila.models.payment import Payment


@admin_role_required
def school_costs(request, slug):
    """
    A school admin can view invoices
    """
    invoices = Invoice.objects.filter(
        invoice_type="PLATFORM_FEE", school__admin=request.user
    )
    return render(
        request, "billing/school/invoice_list.html", {"invoices": invoices})


@custom_login_required
def settings_view(request, slug):
    if request.method == "GET":
        form = WalletKYCForm()
        form.fields["wallet"].queryset = Wallet.objects.filter(
            user=request.user)
        return render(request, "billing/settings_form.html", {"form": form})

    if request.method == "POST":
        form = WalletKYCForm(request.POST or None)
        form.save()
        return redirect("lipila:wallet_dashboard", slug)


@custom_login_required
def transactions(request, slug):
    try:
        wallet = request.user.wallet
    except Wallet.DoesNotExist:
        return redirect("lipila:authorize", slug)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by(
        "-created_at"
    )[:10]
    return render(
        request, "wallets/transactions.html", {"transactions": transactions})


@custom_login_required
def wallet_dashboard(request, slug):
    try:
        wallet = request.user.wallet
    except Wallet.DoesNotExist:
        return redirect("lipila:authorize", slug)
    transactions = WalletTransaction.objects.filter(
        wallet=wallet, transaction_type="CASH_IN"
    ).order_by("-created_at")[:10]
    payments = Payment.objects.filter(wallet=wallet)
    # Request payment status if a user has incomplete payments
    if payments:
        for payment in payments:
            skip_statuses = [
                "pending",
                "submitted",
                "accepted",
                "processing",
                "in_reconciliation",
            ]
            status = payment.status
            if status.lower() != "completed":
                data, code = pawapay_request(
                    "GET", f"/v2/deposits/{payment.id}")
                if code == 200 and "data" in data:
                    status = data["data"]["status"].lower()
                    # Dont update status if pending/submitted
                    # to avoid overwriting final state

                    if status in skip_statuses:
                        status = status
                    payment.status = status
                    payment.save()
                    if status == "completed" and payment.wallet is not None:
                        try:
                            WalletTransactionService.cash_in(
                                wallet=payment.user.wallet,
                                amount=payment.amount,
                                payment=payment,
                                reference=payment.reference,
                            )
                            try:
                                invoice = Invoice.objects.filter(
                                    payment=payment
                                ).first()
                                invoice.status = status
                                invoice.save()
                            except Exception:
                                pass
                        except DuplicateTransaction:
                            pass
                    try:
                        invoice = Invoice.objects.filter(
                            payment=payment).first()
                        invoice.status = status
                        invoice.save()
                    except Exception:
                        pass

    totals = WalletTransaction.objects.filter(
        wallet=wallet, status="COMPLETED"
    ).aggregate(
        cash_in=Sum("amount", filter=Q(amount__gt=0)),
        cash_out=Sum("amount",
                     filter=Q(amount__lt=0) & Q(transaction_type="PAYOUT")),
        cash_in_costs=Sum("amount",
                          filter=Q(amount__lt=0) & Q(transaction_type="FEE")),
    )

    context = {
        "wallet": wallet,
        "wallet_balance": wallet.balance,
        "cash_in": totals["cash_in"] or 0,
        "cash_out": abs(totals["cash_out"] or 0),
        "cash_in_costs": abs(totals["cash_in_costs"] or 0),
        "transactions": transactions,
    }

    return render(request, "wallets/dashboard.html", context)


@custom_login_required
def wallet_authorize(request, slug):
    # If wallet already exists, go straight to dashboard
    if hasattr(request.user, "wallet"):
        return redirect("lipila:wallet_dashboard", slug)

    if request.method == "POST":
        # Create wallet safely
        Wallet.objects.get_or_create(
            user=request.user, defaults={"balance": 0})
        return redirect("lipila:wallet_dashboard", slug)

    return render(request, "wallets/authorize.html")
