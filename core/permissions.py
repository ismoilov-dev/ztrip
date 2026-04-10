from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    GET, HEAD, OPTIONS  — hamma (anonymous ham)
    POST, PUT, PATCH, DELETE — faqat is_staff=True
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff


class IsPremiumOrFreeContent(BasePermission):
    """
    Object darajasida tekshiruv:
    - is_premium=False  → hamma ko'ra oladi
    - is_premium=True   → faqat aktiv subscriptioni bor user
    """
    def has_object_permission(self, request, view, obj):
        if not obj.is_premium:
            return True
        if not request.user.is_authenticated:
            return False
        return request.user.subscriptions.filter(
            is_active=True
        ).exists()