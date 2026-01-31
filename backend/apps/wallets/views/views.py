from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from lipila.models.payment_related import Customer, Invoice, WalletKYC
from lipila.forms import InvoiceForm, BulkProfileCreateForm, BulkInvoiceForm
from identity.decorators import admin_role_required
from schadmin.utils.helpers import get_user_school

User = get_user_model()


# --- CUSTOMER VIEWS ---
@admin_role_required
def customer_list(request, slug):
    customers = Customer.objects.filter(owner=request.user)
    return render(request,
                  "billing/customer_list.html", {"customers": customers})


@admin_role_required
def create_bulk_profiles(request, slug):
    school = get_user_school(request.user)
    if not school.can("allow_bulk_profiles"):
        messages.info(request,
                      "Bulk Profile Creation is available on the Pro plan.")
        return redirect("lipila:billing")
    if request.method == "POST":
        form = BulkProfileCreateForm(
            request.POST, school_profile=request.user.school)
        if form.is_valid():
            selected_users = form.cleaned_data["users"]

            # Create a separate profile for each selected user
            for user in selected_users:
                Customer.objects.get_or_create(
                    user=user,
                    owner=request.user,
                )
            messages.success(request, "Student Online billing account added.")
            return redirect("lipila:customer_list", slug=slug)
        messages.error(request, "Failed to add student billing")
    else:
        form = BulkProfileCreateForm(school_profile=request.user.school)

    return render(request, "billing/customer_form.html", {"form": form})


# ----- Invoice Creationg & Management views -----
@admin_role_required
def invoice_list(request, slug):
    """
    A reistered user views their created invoices
    """
    invoices = Invoice.objects.filter(
        customer__owner=request.user).select_related("customer")
    return render(request, "billing/invoice_list.html", {"invoices": invoices})


@admin_role_required
def create_multiple_invoices(request, slug):
    """
    Create multiple invoices for a selected customer
    """
    form = BulkInvoiceForm(request.POST or None)

    # Limit customer dropdown
    form.fields["customer"].queryset = Customer.objects.filter(
        owner=request.user)

    if form.is_valid():
        quantity = form.cleaned_data["quantity"]

        invoices = []
        with transaction.atomic():
            for _ in range(quantity):
                invoice = form.save(commit=False)
                invoice.pk = None  # ensure a new object
                invoice.invoice_type = "CUSTOMER"
                invoice.school = get_user_school(request.user)
                invoice.save()
                invoices.append(invoice)

        messages.success(request, f"{quantity} invoices created successfully.")
        return redirect("lipila:invoice_list", slug=slug)

    messages.error(request, f"Failed to create invoices. {form.errors}")

    return render(request, "billing/bulk_invoice_form.html", {"form": form})


@admin_role_required
def create_single_invoice(request, slug):
    """
    A reistered user creates invoices for customers
    """
    form = InvoiceForm(request.POST or None)

    # Limit customer dropdown
    form.fields["customer"].queryset = Customer.objects.filter(
        owner=request.user)

    if form.is_valid():
        invoice = form.save(commit=False)
        invoice.invoice_type = "CUSTOMER"
        invoice.school = get_user_school(request.user)
        invoice.save()
        messages.success(request, "Invoice Created successfully.")
        return redirect(
            "lipila:invoice_detail", slug=slug, invoice_id=invoice.id)
    messages.error(request, f"Failed to create Invoice.{form.errors}")

    return render(request, "billing/invoice_form.html", {"form": form})


@admin_role_required
def update_invoice(request, slug, invoice_id):
    """
    Update an existing invoice.
    Only the invoice owner (via customer.owner) can edit.
    """

    invoice = get_object_or_404(
        Invoice.objects.filter(customer__owner=request.user),
        id=invoice_id,
    )

    form = InvoiceForm(request.POST or None, instance=invoice)

    # Limit customer dropdown to owner's customers
    form.fields["customer"].queryset = Customer.objects.filter(
        owner=request.user)

    if form.is_valid():
        form.save()
        messages.success(request, "Invoice updated successfully.")
        return redirect("lipila:invoice_detail",
                        slug=slug, invoice_id=invoice.id)

    if request.method == "POST":
        messages.error(request, f"Failed to update invoice. {form.errors}")

    return render(
        request,
        "billing/invoice_form.html",
        {
            "form": form,
            "invoice": invoice,
            "is_update": True,
        },
    )


# --- PAYMENT INIT (just linking for now) ---
def initiate_invoice_payment(
    request,
    slug,
    invoice_id,
):
    """
    Redirect user to pawapay deposit url
    """
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    # Redirect to deposit page with amount + remarks preloaded
    subtotal = invoice.subtotal()
    remarks = invoice.remarks
    return redirect(
        reverse("lipila:deposit_invoice_payment", args=[invoice_id])
        + f"?amount={subtotal}&remarks={remarks}"
    )


def public_invoice_view(request, slug, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    kyc = WalletKYC.objects.filter(wallet__user=invoice.customer.owner).first()

    can_pay = invoice.status not in ["cancelled"] and (
        invoice.multiple_payers or not invoice.payment
    )
    payee = kyc.full_name if kyc else invoice.customer.owner.get_full_name()
    context = {
        "payee": payee,
        "invoice": invoice,
        "customer": invoice.customer,
        "slug": slug,
        "can_pay": can_pay,
    }

    return render(request, "billing/public_invoice.html", context)


@admin_role_required
def invoice_detail(request, slug, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    can_pay = invoice.status.lower() not in ["completed", "paid"]

    context = {
        "invoice": invoice,
        "customer": invoice.customer,
        "can_pay": can_pay,
    }
    return render(request, "billing/invoice_detail.html", context)
