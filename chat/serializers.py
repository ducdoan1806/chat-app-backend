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
    member = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = "__all__"

    def get_messages(self, obj):
        try:
            qs_message = Message.objects.filter(room=obj)
            return MessageSerializer(qs_message[0], many=False).data["content"]
        except Exception as e:
            return None

    def get_member(self, obj):
        try:

            qs_message = Member.objects.filter(room_id=obj)
            members = MemberSerializer(qs_message, many=True).data

            return members
        except Exception as e:
            return None


class MemberSerializer(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = "__all__"

    def get_user_profile(self, obj):
        try:
            qs_user = User.objects.get(username=obj.user)
            return UserSerializer(qs_user, many=False).data
        except Exception as e:
            return None


class MessageSerializer(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Message
        fields = "__all__"

    def get_user_profile(self, obj):
        try:
            qs_message = User.objects.get(user=obj)
            return UserSerializer(qs_message, many=False).data
        except Exception as e:
            return None
