from django.shortcuts import redirect, render
from django.contrib import messages
from identity.decorators import admin_role_required
from schadmin.plans import PLANS
from schadmin.utils.helpers import get_user_school


@admin_role_required
def billing(request):
    school = get_user_school(request.user)

    context = {
        "school": school,
        "plans": PLANS,
        "current_plan": school.plan,
    }
    return render(request, "billing/school/billing.html", context)


@admin_role_required
def upgrade_plan(request, plan):
    school = get_user_school(request.user)

    if plan not in PLANS:
        messages.error(request, "Invalid plan selected.")
        return redirect("lipila:billing")

    # Prevent downgrade for now
    PLAN_ORDER = ["starter", "pro", "gold"]
    if PLAN_ORDER.index(plan) <= PLAN_ORDER.index(school.plan):
        messages.warning(request, "You can only upgrade your plan.")
        return redirect("lipila:billing")

    school.plan = plan
    school.save()

    messages.success(
        request, f"🎉 You have successfully upgraded to the {
            plan.capitalize()} plan!"
    )
    return redirect("lipila:billing")
