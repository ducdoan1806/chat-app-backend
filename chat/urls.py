from django.urls import path, include
from .views import *
from rest_framework import routers


router = routers.DefaultRouter()
router.register("user-list", UserList, basename="user-list")
router.register("room", RoomView, basename="room")
router.register("message", MessageView, basename="message")
urlpatterns = [
    path("", include(router.urls)),
    path("register/", RegisterView.as_view(), name="register"),
    path("oauth2-info/", AuthInfo.as_view()),
    path("user/", UserProfileView.as_view(), name="user"),
]
