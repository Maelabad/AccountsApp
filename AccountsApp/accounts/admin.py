from django.contrib import admin
from .models import UserProfile, Address, UserModel
from django.utils.html import format_html
from django.contrib import admin

# Register your models here.

admin.site.register(UserModel)

admin.site.register(Address)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'image_preview')

    def name(self, obj):
        name = obj.user.username + " / "
        if obj.user.first_name and obj.user.last_name:
            name += f"{obj.user.first_name} {obj.user.last_name}"
        return name

    def city(self, obj):
        return obj.address.city

    def image_preview(self, obj):
        """Affiche un aperçu de l'image dans l'admin Django"""
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" height="50"/>'.format(obj.profile_picture.url))
        return "Pas d'image"




