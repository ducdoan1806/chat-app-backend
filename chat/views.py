import sys, os, socketio
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.contrib.auth.models import User
from django.conf import settings
from .models import *
from .serializers import *
from datetime import time
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import viewsets, permissions


sio = socketio.Client()


@sio.event
def connect_error(data):
    print(f"Connection error: {data}")
    reconnect()


@sio.event
def disconnect():
    print("Disconnected from server")


def reconnect():
    print("Attempting to reconnect...")
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            print(f"Reconnection attempt {attempt + 1}")
            sio.connect("http://localhost:3000", wait=True, wait_timeout=10)
            print("Reconnected successfully")
            return
        except socketio.exceptions.ConnectionError as e:
            if e == "Already connected":
                break
            print(f"Reconnection failed: {e}")
            time.sleep(5)


def connect_to_server():
    try:
        headers = {"cookie": "BE connect"}
        sio.connect(
            "http://localhost:3000", headers=headers, wait=True, wait_timeout=10
        )
    except socketio.exceptions.ConnectionError as e:
        print(f"Connection failed: {e}")
        reconnect()


connect_to_server()


class StandardPagesPagination(PageNumberPagination):
    page_size = 10


class AuthInfo(APIView):
    def get(self, request):
        return Response(settings.OAUTH2_INFO, status=status.HTTP_200_OK)


# Create your views here.
class RegisterView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                first_name = serializer.data.pop("first_name")
                last_name = serializer.data.pop("last_name")
                user = User.objects.create_user(
                    username=serializer.data["username"],
                    email=serializer.data["email"],
                    password=serializer.data["password"],
                )
                UserProfile.objects.create(
                    user=user, last_name=last_name, first_name=first_name
                )
                sio.emit("user-list", UserSerializer(user, many=False).data)
                return Response(
                    {
                        "status": True,
                        "message": "Registration successful",
                        "data": UserSerializer(user, many=False).data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                errors = []
                fields_with_errors = []

                for field, field_errors in serializer.errors.items():
                    fields_with_errors.append(field)
                    errors.extend([str(error) for error in field_errors])

                return Response(
                    {
                        "status": False,
                        "message": " ".join(errors),
                        "fields": fields_with_errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            serializer = UserSerializer(user)
            data = serializer.data
            data.pop("first_name")
            data.pop("last_name")
            data.pop("is_staff")
            data.pop("groups")
            data.pop("user_permissions")
            data.pop("is_superuser")
            data.pop("last_login")

            return Response(
                {"status": True, "message": "Success", "data": data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user

            serializer_user = UserSerializer(user)
            serializers = RoomSerializer(data=request.data)

            if serializers.is_valid():
                data = serializers.data
                data_user = serializer_user.data
                qs_user = User.objects.get(id=data_user.get("id", None))
                newRoom = Room.objects.create(name=data["name"], user_created=qs_user)

                return Response(
                    {
                        "status": True,
                        "message": "",
                        "data": RoomSerializer(newRoom).data,
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserList(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    pagination_class = StandardPagesPagination
    permission_classes_by_action = {
        "list": [permissions.AllowAny()],
    }

    def get_permissions(self):
        default_permissions = [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return self.permission_classes_by_action.get(self.action, default_permissions)

    def list(self, request):
        try:
            qs_data = self.get_queryset()
            current_user = request.user
            qs_data = qs_data.exclude(id=current_user.id).exclude(is_superuser=True)
            search_query = request.query_params.get("search", None)

            if search_query is not None:
                qs_data = qs_data.filter(Q(email__icontains=search_query))

            page_size = self.request.query_params.get("page_size")
            self.pagination_class.page_size = (
                int(page_size) if page_size is not None else 15
            )

            page = self.paginate_queryset(qs_data)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(qs_data, many=True)
            return Response(serializer.data)
        except Exception as e:
            exc_tb = sys.exc_info()
            lineno = exc_tb.tb_lineno
            file_path = exc_tb.tb_frame.f_code.co_filename
            file_name = os.path.basename(file_path)
            message = f"[{file_name}_{lineno}] {str(e)}"
            return Response(message, status=status.HTTP_404_NOT_FOUND)
