from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, RecycleUser, UserPreviousDetailHistory, UserPasswordResetToken, UserSearchHistory, \
    UserFavoriteProduct, UserRecentVisitedProduct


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "email",
            "phone",
            "first_name",
            "last_name",
            "is_superuser",
            "is_staff",
            "national_code",
            "last_login",
        )


@admin.register(User)
class UserAdmin(UserAdmin):
    form = UserForm
    list_display = (
        "username",
        "email",
        "phone",
        "first_name",
        "last_name",
        "is_superuser",
    )
    search_fields = (
        "username",
        "email",
        "phone",
        "first_name",
        "last_name",
        "is_superuser",
    )
    list_editable = (
        "first_name",
        "last_name",
        "is_superuser",
    )

    def get_queryset(self, request):
        return User.objects.filter(is_deleted=False)

    def delete_model(self, request, obj):
        obj.delete()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()


@admin.register(UserSearchHistory)
class UserSearchHistoryAdmin(admin.ModelAdmin):
    pass


@admin.register(UserFavoriteProduct)
class UserFavoriteProductAdmin(admin.ModelAdmin):
    pass


@admin.register(UserRecentVisitedProduct)
class UserRecentVisitedProductAdmin(admin.ModelAdmin):
    pass


@admin.register(RecycleUser)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "email",
        "phone",
        "first_name",
        "last_name",
        "is_superuser",
    )
    actions = ["recover_items"]

    def get_queryset(self, request):
        return RecycleUser.deleted.filter(is_deleted=True)

    @admin.action(description="Recover Items")
    def recover_items(self, request, queryset):
        queryset.update(is_deleted=False, deleted_at=None)


@admin.register(UserPreviousDetailHistory)
class UserPreviousDetailHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "old_value", "new_value", "field", "created_at")
    search_fields = ("user", "old_value", "new_value", "field", "created_at")


@admin.register(UserPasswordResetToken)
class UserPasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "token",
        "expire_at",
    )
    search_fields = (
        "user",
        "token",
        "expire_at",
    )

    @staticmethod
    def is_expired(obj):
        return obj.is_expired()
