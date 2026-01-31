from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages

from lipila.models.payment_related import WalletKYC
from apps.wallets.services.wallet_service import WalletService
from lipila.forms import WalletKYCForm


@login_required
def wallet_kyc(request, slug):
    wallet = WalletService.get_wallet_for_user(request.user)

    kyc, created = WalletKYC.objects.get_or_create(wallet=wallet)

    if request.method == "POST":
        form = WalletKYCForm(request.POST, request.FILES, instance=kyc)
        if form.is_valid():
            kyc = form.save(commit=False)

            # Reset verification if user updates KYC
            if not created:
                kyc.verified = False

            kyc.save()
            messages.success(
                request, "KYC details submitted successfully."
                "Verification pending."
            )
            return redirect(reverse("lipila:settings", kwargs={"slug": slug}))
    else:
        form = WalletKYCForm(instance=kyc)

    return render(
        request,
        "billing/kyc_form.html",
        {
            "form": form,
            "kyc": kyc,
        },
    )
