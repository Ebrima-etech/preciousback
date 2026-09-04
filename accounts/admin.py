from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address

class AddressInline(admin.TabularInline):
    model = Address
    extra = 0

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [AddressInline]
    list_display = ['email', 'first_name', 'last_name', 'phone', 'date_joined']
    list_filter = ['date_joined', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    fieldsets = (
        ('Login Information', {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'date_of_birth')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'street', 'city', 'state', 'country', 'is_default']
    list_filter = ['is_default', 'country']
    search_fields = ['user__email', 'street', 'city']
    readonly_fields = ['created_at']
