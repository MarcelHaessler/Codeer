from django.db.models import Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from ..models import Offer, OfferDetail
from .filters import OfferFilter
from .pagination import OfferPagination
from .permissions import IsBusinessUserOrReadOnly, IsOfferOwner
from .serializers import (
    OfferDetailSerializer,
    OfferListSerializer,
    OfferRetrieveSerializer,
    OfferWriteSerializer,
)


def annotated_offers():
    """Returns offers annotated with the cheapest price and fastest delivery."""
    return Offer.objects.annotate(
        min_price=Min('details__price'),
        min_delivery_time=Min('details__delivery_time_in_days'),
    ).select_related('user')


class OfferListCreateView(generics.ListCreateAPIView):
    """Lists offers publicly, or creates one as an authenticated business user."""

    permission_classes = [IsBusinessUserOrReadOnly]
    pagination_class = OfferPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OfferFilter
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'min_price']
    ordering = ['-updated_at']

    def get_queryset(self):
        """Annotated, because filtering and ordering by price happen in SQL."""
        return annotated_offers()

    def get_serializer_class(self):
        """POST accepts nested tiers, GET returns them as id and url pairs."""
        if self.request.method == 'POST':
            return OfferWriteSerializer
        return OfferListSerializer

    def perform_create(self, serializer):
        """Takes the owner from the token instead of trusting the request body."""
        serializer.save(user=self.request.user)


class OfferDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieves, updates or deletes a single offer."""

    permission_classes = [IsAuthenticated, IsOfferOwner]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        """Annotated as well, so min_price appears in the detail response."""
        return annotated_offers()

    def get_serializer_class(self):
        """PATCH answers with expanded tiers, GET with id and url references."""
        if self.request.method == 'PATCH':
            return OfferWriteSerializer
        return OfferRetrieveSerializer


class OfferDetailItemView(generics.RetrieveAPIView):
    """Retrieves a single pricing tier of an offer."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]
