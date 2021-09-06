from django.contrib import admin

from .models import CustomUser


@admin.register(CustomUser)
class UserBaseAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_staff', 'is_active',)
    list_filter = ('email', 'is_staff', 'is_active',)
    search_fields = ('email',)
    ordering = ('email',)