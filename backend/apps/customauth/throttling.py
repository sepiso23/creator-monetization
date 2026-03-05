from rest_framework.throttling import UserRateThrottle


class PremiumUserThrottle(UserRateThrottle):
    scope = 'premium'

    def allow_request(self, request, view):
        if request.user.is_authenticated and hasattr(request.user, 'is_premium'):
            return super().allow_request(request, view)
        return False