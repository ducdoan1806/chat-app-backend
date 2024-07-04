from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    friends = models.ManyToManyField(User, blank=True, related_name="friends")
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class Room(models.Model):
    name = models.CharField(max_length=255)
    is_group = models.BooleanField(default=False)
    user_created = models.ForeignKey(
        User,
        blank=True,
        on_delete=models.SET_NULL,
        null=True,
        related_name="user_profile",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class Member(models.Model):
    ACTION_CHOICES = (
        ["OWNER", "OWNER"],
        ["ADMIN", "ADMIN"],
        ["MEMBER", "MEMBER"],
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    role = models.CharField(
        max_length=20, default="ADMIN", choices=ACTION_CHOICES, null=True, blank=True
    )
    room = models.ForeignKey(
        Room,
        blank=True,
        on_delete=models.CASCADE,
        null=True,
        related_name="member",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="room")
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="user")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return str(self.id)
