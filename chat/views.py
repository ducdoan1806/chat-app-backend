import sys, os, socketio
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.contrib.auth.models import User
from django.conf import settings
from .models import *
from django.db import IntegrityError, transaction
from .serializers import *
from datetime import time
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import viewsets, permissions
from rest_framework.decorators import action

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
            sio.connect("http://localhost:3000",transports=['websocket', 'polling'], wait=True, wait_timeout=10)
            sio.wait()
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

def check_room(user, userId):
    room_with_users = (
        Member.objects.filter(user_id__in=[user.data["id"], userId])
        .values("room_id")
        .annotate(user_count=Count("user_id"))
        .filter(user_count=2)
    )

    for room in room_with_users:
        room_id = room["room_id"]
        user_ids_in_room = Member.objects.filter(room_id=room_id).values_list(
            "user_id", flat=True
        )
        if set(user_ids_in_room) == {user.data["id"], int(userId)}:
            return room_id
    return None

class StandardPagesPagination(PageNumberPagination):
    page_size = 10

class AuthInfo(APIView):
    def get(self, request):
        return Response(settings.OAUTH2_INFO, status=status.HTTP_200_OK)

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
            exc_type, exc_obj, exc_tb = sys.exc_info()
            lineno = exc_tb.tb_lineno
            file_path = exc_tb.tb_frame.f_code.co_filename
            file_name = os.path.basename(file_path)
            message = f"[{file_name}_{lineno}] {str(e)}"
            return Response(
                {"status": True, "message": message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            serializer = UserSerializer(user)
            data = serializer.data
            return Response(
                {"status": True, "message": "Success", "data": data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            lineno = exc_tb.tb_lineno
            file_path = exc_tb.tb_frame.f_code.co_filename
            file_name = os.path.basename(file_path)
            message = f"[{file_name}_{lineno}] {str(e)}"
            return Response(
                {"status": True, "message": message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class RoomView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RoomSerializer
    pagination_class = StandardPagesPagination
    queryset = Room.objects.all()
    def list(self, request):
        try:
            user = request.user
            user = UserSerializer(user)
            qs_data = Room.objects.filter(member__user=user.data['id'])
            page_size = self.request.query_params.get("page_size")
            self.pagination_class.page_size = (
                int(page_size) if page_size is not None else 15
            )
            # qs_Message_room=Message.objects.all().values_list("room",flat=True).distinct()
            # qs_data=qs_data.filter(id__in=qs_Message_room)
            page = self.paginate_queryset(qs_data)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(qs_data, many=True)
            return Response(
                {"status": True, "message": "Success",'data':serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            lineno = exc_tb.tb_lineno
            file_path = exc_tb.tb_frame.f_code.co_filename
            file_name = os.path.basename(file_path)
            message = f"[{file_name}_{lineno}] {str(e)}"
            return Response(
                {"status": True, "message": message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
   
    @action(methods=['post'], detail=False,url_path='create-room',url_name='createRoom')
    def createRoom(self, request):
        try:
            sender = request.user
            sender_serializer = UserSerializer(sender, many=False)

            receiver_id = request.data["receiver_id"]
            receiver = User.objects.filter(id=receiver_id).first()

            if not receiver:
                return Response(
                {"status": False, "message": "receiver not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
            receiver_serializer = UserSerializer(receiver, many=False)
            check = check_room(sender_serializer, receiver_id)
            
            if sender_serializer.data['id']==receiver_id:
                return Response(
                {"status": False, "message": "Cannot create a room with yourself."},
                status=status.HTTP_400_BAD_REQUEST,)
            if check != None:
                room_checked = Room.objects.get(id=check)
                return Response(
                {"status": True, "message": "Success",'data':RoomSerializer(room_checked).data},
                status=status.HTTP_200_OK,
            )
            with transaction.atomic():
                room_data={ "name":f"{sender_serializer.data["profile"]['first_name']} {sender_serializer.data["profile"]['last_name']}, {receiver_serializer.data["profile"]['first_name']} {receiver_serializer.data["profile"]['last_name']}",'user_created':sender_serializer.data['id']}
                room_serializer=RoomSerializer(data=room_data)
                if not room_serializer.is_valid():
                    return Response(room_serializer.errors, status=status.HTTP_400_BAD_REQUEST)   
                room = room_serializer.save()
                
                senderMember={ "user":sender_serializer.data['id'],"room":room.id}
                senderMember_serializer=MemberSerializer(data=senderMember)
                if not senderMember_serializer.is_valid():
                    return Response(senderMember_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                senderMember_serializer.save()
            
                receiverMember={ "user":receiver_serializer.data['id'],"room":room.id}
                receiverMember_serializer=MemberSerializer(data=receiverMember)
                if not receiverMember_serializer.is_valid():
                    return Response(receiverMember_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                receiverMember_serializer.save()
                    
                return Response({
                    "status": True,
                    "message": "Success",
                    "data":RoomSerializer(room).data,
                    },
                    status=status.HTTP_201_CREATED,
                ) 
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            lineno = exc_tb.tb_lineno
            file_path = exc_tb.tb_frame.f_code.co_filename
            file_name = os.path.basename(file_path)
            message = f"[{file_name}_{lineno}] {str(e)}"
            return Response(
                {"status": True, "message": message},
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
            exc_type, exc_obj, exc_tb = sys.exc_info()
            lineno = exc_tb.tb_lineno
            file_path = exc_tb.tb_frame.f_code.co_filename
            file_name = os.path.basename(file_path)
            message = f"[{file_name}_{lineno}] {str(e)}"
            return Response(
                {"status": True, "message": message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class MessageView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    queryset = Message.objects.all()

    def list(self,request):
        try:
            user=request.user
            room_id = request.query_params.get("room_id")
            qs_member = Member.objects.filter(user=user,room=room_id).exists()
            if not qs_member:
                return Response(
                {"status": False, "message": "You don't join this room"},
                status=status.HTTP_400_BAD_REQUEST,
            ) 
            qs_data = Message.objects.filter(room=room_id)
            page_size = self.request.query_params.get("page_size")
            self.pagination_class.page_size = (
                int(page_size) if page_size is not None else 15
            )

            page = self.paginate_queryset(qs_data)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(qs_data, many=True)
            return Response(
                {"status": True, "message": "Success",'data':serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            exc_tb = sys.exc_info()
            lineno = exc_tb.tb_lineno
            file_path = exc_tb.tb_frame.f_code.co_filename
            file_name = os.path.basename(file_path)
            message = f"[{file_name}_{lineno}] {str(e)}"
            return Response({status:False,"message":message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['post'], detail=False,url_path='create-message',url_name='createMessage')
    def createMessage(self,request):
        try:
            user = request.user
            user_serializer = UserSerializer(user).data
            room_id = request.data.get("room_id")
            content= request.data.get("content")
            messageData={ "user":user_serializer['id'],"room":room_id,"content":content}
            print(messageData)
            message_serializer = MessageSerializer(data=messageData)
            
            if not message_serializer.is_valid():
                 return Response(
                {"status": False, "message": "message is not created",},
                status=status.HTTP_200_OK,
            )
            message_serializer.save()
            return Response(
                {"status": True, "message": "Success",'data':message_serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            lineno = exc_tb.tb_lineno
            file_path = exc_tb.tb_frame.f_code.co_filename
            file_name = os.path.basename(file_path)
            message = f"[{file_name}_{lineno}] {str(e)}"
            return Response(
                {"status": True, "message": message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
