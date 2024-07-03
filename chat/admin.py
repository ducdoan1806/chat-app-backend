from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import *


class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "first_name",
        "last_name",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "id",
        "first_name",
        "last_name",
        "created_at",
        "updated_at",
    )
    list_per_page = 10


class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "is_group",
        "user_created",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "id",
        "name",
        "is_group",
        "user_created",
        "created_at",
        "updated_at",
    )
    list_per_page = 10


class MemberAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "role",
        "user",
        "room",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "id",
        "role",
        "user",
        "room",
        "created_at",
        "updated_at",
    )
    list_per_page = 10


class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "room",
        "user",
        "content",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "id",
        "room",
        "user",
        "content",
        "created_at",
        "updated_at",
    )
    list_per_page = 10


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Message, MessageAdmin)
