from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
from django.core.exceptions import ValidationError


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["username", "email", "id", "profile"]
        extra_kwargs = {"password": {"write_only": True}}

    def get_profile(self, obj):
        try:

            qs_profile = UserProfile.objects.get(user=obj)
            return UserProfileSerializer(qs_profile, many=False).data
        except Exception as e:
            return None


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = ["first_name", "last_name"]


class RegisterSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)

    class Meta:
        model = User
        fields = "__all__"

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value


class RoomSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()

    def get_messages(self, obj):
        try:
            qs_message = Message.objects.filter(room=obj)
            return MessageSerializer(qs_message[0], many=True).data
        except Exception as e:

            return None

    class Meta:
        model = Room
        fields = "__all__"


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = "__all__"
