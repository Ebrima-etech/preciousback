from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import logging
from .models import User, Address
from .serializers import UserSerializer, AddressSerializer, RegisterSerializer, LoginSerializer

logger = logging.getLogger(__name__)

class AuthViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'user': UserSerializer(user).data,
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }, status=status.HTTP_201_CREATED)
            logger.error(f'Registration validation error: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Registration error: {str(e)}', exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                email = serializer.validated_data['email']
                password = serializer.validated_data['password']

                # Try to get user by email and verify password
                try:
                    user = User.objects.get(email=email)
                    if user.check_password(password):
                        refresh = RefreshToken.for_user(user)
                        return Response({
                            'user': UserSerializer(user).data,
                            'access': str(refresh.access_token),
                            'refresh': str(refresh),
                        })
                except User.DoesNotExist:
                    pass

                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
            logger.error(f'Login validation error: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Login error: {str(e)}', exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        return Response({'detail': 'Successfully logged out'})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def profile(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
