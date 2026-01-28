from django.contrib import admin

from .models import CreatorProfile


class CreatorProfileAdmin(admin.ModelAdmin):
    """Admin for CreatorProfile model."""

    list_display = ('get_creator_name', 'status', 'verified', 'followers_count', 'total_earnings', 'rating', 'created_at')
    list_filter = ('status', 'verified', 'created_at')
    search_fields = ('user__email', 'user__username', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'followers_count', 'total_earnings')

    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Profile Info', {'fields': ('bio', 'profile_image', 'cover_image', 'website')}),
        ('Stats', {'fields': ('followers_count', 'total_earnings', 'rating')}),
        ('Status', {'fields': ('status', 'verified')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )

    def get_creator_name(self, obj):
        """Get creator's full name or username."""
        return obj.user.get_full_name() or obj.user.username

    get_creator_name.short_description = 'Creator Name'


admin.site.register(CreatorProfile, CreatorProfileAdmin)
