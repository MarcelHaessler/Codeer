from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from ..models import Profile
from .permissions import IsProfileOwner
from .serializers import (
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
    ProfileSerializer,
)


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """Retrieves or updates a single profile, addressed by its user id."""

    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsProfileOwner]
    lookup_field = 'user_id'
    lookup_url_kwarg = 'pk'
    http_method_names = ['get', 'patch', 'head', 'options']


class BusinessProfileListView(generics.ListAPIView):
    """Lists all business profiles."""

    queryset = Profile.objects.filter(type='business')
    serializer_class = BusinessProfileListSerializer
    permission_classes = [IsAuthenticated]


class CustomerProfileListView(generics.ListAPIView):
    """Lists all customer profiles."""

    queryset = Profile.objects.filter(type='customer')
    serializer_class = CustomerProfileListSerializer
    permission_classes = [IsAuthenticated]
