from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from offers_app.models import OfferDetail
from ..models import Order
from .permissions import IsCustomerUser, IsOrderBusinessUserOrAdmin
from .serializers import OrderSerializer

MISSING_DETAIL_ERROR = {'offer_detail_id': ['This field is required.']}


def build_order_data(detail, customer):
    """Copies the tier data so the order stays stable if the offer changes."""
    return {
        'customer_user': customer,
        'business_user': detail.offer.user,
        'title': detail.title,
        'revisions': detail.revisions,
        'delivery_time_in_days': detail.delivery_time_in_days,
        'price': detail.price,
        'features': detail.features,
        'offer_type': detail.offer_type,
    }


def count_orders_by_status(business_user_id, order_status):
    """Counts a business user's orders in the given status."""
    business_user = get_object_or_404(User, pk=business_user_id)
    return Order.objects.filter(
        business_user=business_user, status=order_status
    ).count()


class OrderListCreateView(generics.ListCreateAPIView):
    """Lists the orders a user is involved in, or books an offer tier."""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsCustomerUser]

    def get_queryset(self):
        """Covers both roles, so customer and business see the same order."""
        user = self.request.user
        return Order.objects.filter(
            Q(customer_user=user) | Q(business_user=user)
        )

    def create(self, request, *args, **kwargs):
        """Books a tier; the request sends offer_detail_id, not model fields."""
        detail_id = request.data.get('offer_detail_id')
        if not detail_id:
            return Response(MISSING_DETAIL_ERROR, status=status.HTTP_400_BAD_REQUEST)
        detail = get_object_or_404(
            OfferDetail.objects.select_related('offer'), pk=detail_id
        )
        order = Order.objects.create(**build_order_data(detail, request.user))
        return Response(
            self.get_serializer(order).data, status=status.HTTP_201_CREATED
        )


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Updates the status of an order, or deletes it as an admin."""

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOrderBusinessUserOrAdmin]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']


class OrderCountView(APIView):
    """Returns how many orders of a business user are still in progress."""

    permission_classes = [IsAuthenticated]

    def get(self, request, business_user_id):
        """Answers 404 for an unknown user rather than reporting a count of zero."""
        count = count_orders_by_status(business_user_id, 'in_progress')
        return Response({'order_count': count}, status=status.HTTP_200_OK)


class CompletedOrderCountView(APIView):
    """Returns how many orders of a business user are completed."""

    permission_classes = [IsAuthenticated]

    def get(self, request, business_user_id):
        """Answers 404 for an unknown user rather than reporting a count of zero."""
        count = count_orders_by_status(business_user_id, 'completed')
        return Response(
            {'completed_order_count': count}, status=status.HTTP_200_OK
        )
