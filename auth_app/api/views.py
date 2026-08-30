from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegistrationSerializer


def build_auth_response(user, token):
    """Returns the payload shared by registration and login."""
    return {
        'token': token.key,
        'username': user.username,
        'email': user.email,
        'user_id': user.id,
    }


class RegistrationView(APIView):
    """Creates a new user account and returns its auth token."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Registers the account and hands out its first token right away."""
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            build_auth_response(user, token),
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticates a user and returns its auth token."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Reuses the stored token; a user keeps the same one across logins."""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            build_auth_response(user, token),
            status=status.HTTP_200_OK,
        )
