from rest_framework.throttling import UserRateThrottle


class AdminRateThrottle(UserRateThrottle):
    """
    Admin foydalanuvchilar uchun throttle - cheksiz so'rovlar
    """
    def allow_request(self, request, view):
        if request.user.is_authenticated and request.user.is_staff:
            return True  # Admin uchun cheksiz
        return super().allow_request(request, view)


class PremiumUserRateThrottle(UserRateThrottle):
    """
    Premium foydalanuvchilar uchun yuqori limit
    """
    def get_cache_key(self, request, view):
        if request.user.is_authenticated and getattr(request.user, 'is_premium', False):
            # Premium userlar uchun alohida cache key
            ident = request.user.pk
        else:
            # Oddiy userlar uchun standart
            ident = self.get_ident(request)
        
        return f'premium_throttle_{ident}'
