from rest_framework.views import APIView

from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from .models import *
from .serializers import *
from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter



#登入登出模組
# 登入 API
class LoginView(GenericAPIView):
    serializer_class = LoginSerializer

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "refresh": {"type": "string"},
                    "access": {"type": "string"},
                    "role": {"type": "string"},
                    "name": {"type": "string"},
                    "user_id": {"type": "string"}
                }
            },
            401: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="使用者登入 API",
        summary="使用者登入"
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = serializer.validated_data['user_id']
        password = serializer.validated_data['password']
        user = authenticate(request, user_id=user_id, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'role': user.role,
                'name': user.name,
                'user_id': user.user_id
            }, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid credentials'}, 
                        status=status.HTTP_401_UNAUTHORIZED)


# 登出 API
# 自定義登出 API
class LogoutView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = None  # 登出不需要序列化器

    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "refresh": {"type": "string"}
            },
            "required": ["refresh"]
        },
        responses={
            205: None,
            400: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="使用者登出 API",
        summary="使用者登出"
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"detail": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
# 重設密碼 API
class ResetPasswordView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ResetPasswordSerializer

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="重設使用者密碼",
        summary="密碼重設"
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        new_password = serializer.validated_data['new_password']
        try:
            validate_password(new_password, user)
            user.set_password(new_password)
            user.save()
            return Response({'detail': '密碼重設成功'}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'detail': e}, status=status.HTTP_400_BAD_REQUEST)

# 監護人視圖
class GuardianView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = GuardianSerializer

    @extend_schema(
        responses={
            200: GuardianSerializer,
            404: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="獲取監護人資料",
        summary="查詢監護人資料"
    )
    def get(self, request):
        try:
            guardian = Guardian.objects.get(student=request.user)
            serializer = self.get_serializer(guardian)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Guardian.DoesNotExist as err:
            return Response({'detail': '找不到監護人資料'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        request=GuardianSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            201: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                    "guardian_id": {"type": "string"}
                }
            },
            400: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="新增或更新監護人資料",
        summary="監護人資料管理"
    )
    def post(self, request):
        try:
            guardian = Guardian.objects.get(student=request.user)
            serializer = self.get_serializer(guardian, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'detail': '監護人資料更新成功'}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Guardian.DoesNotExist:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            guardian = serializer.save(student=request.user)
            return Response({'detail': '監護人資料創建成功', 'guardian_id': guardian.guardian_id}, status=status.HTTP_201_CREATED)

# 用戶檔案視圖
class UserProfileView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserProfileSerializer

    @extend_schema(
        responses={200: UserProfileSerializer},
        description="獲取用戶個人資料",
        summary="查詢個人資料"
    )
    def get(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=UserProfileSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="更新用戶個人資料",
        summary="更新個人資料"
    )
    def put(self, request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': '個人資料更新成功'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 取得用戶名稱和 user_id API
class UserInfoView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = None
    def get(self, request):
        user = request.user
        data = {
            'user_id': user.user_id,
            'name': user.name,
            'role':user.role
        }
        return Response(data, status=status.HTTP_200_OK)



